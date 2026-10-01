# CDQAI file version: 2.3.6
from copy import deepcopy
import hashlib
import json
import logging
import os
import re
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.detectors.narrative_chunks import FullNarrativeEncoder, split_narrative
from cdqai.detectors.embeddings import NarrativeEmbeddingManager
from cdqai.detectors.narrative_spans import sentence_sensitivity
from cdqai.reports.dashboard_report import _narrative_payload


class Tokenizer:
    is_fast = True
    model_max_length = 8
    backend_tokenizer = SimpleNamespace(to_str=lambda: "synthetic-tokenizer-v1")

    def num_special_tokens_to_add(self, pair=False):
        return 2

    def __call__(self, text, **kwargs):
        matches = list(re.finditer(r"\S+", text))
        return {"input_ids": list(range(len(matches))), "offset_mapping": [(m.start(), m.end()) for m in matches]}


class Embedder:
    tokenizer = Tokenizer()
    max_seq_length = 8

    def __init__(self):
        self.calls = 0
        self.weight = 1.0

    def __str__(self):
        return "Synthetic embedding architecture"

    def state_dict(self):
        return {"weight": torch.tensor([self.weight])}

    def encode(self, texts, **kwargs):
        self.calls += 1
        assert kwargs["prompt"] == ""
        assert all(len(self.tokenizer(t)["input_ids"]) + 2 <= self.max_seq_length for t in texts)
        return np.array([[self.weight * float("SIGNAL" in t), 1.] for t in texts], dtype=np.float32)


@pytest.mark.parametrize("text", ["word " * 50, "first sentence.\n" * 30, "\U0001f697 word " * 30, "word " * 6, "   "])
def test_every_original_character_is_covered_within_model_budget(text):
    tokenizer = Tokenizer()
    chunks, _ = split_narrative(text, tokenizer, 6, 2)
    covered = np.zeros(len(text), dtype=bool)
    for chunk in chunks:
        covered[chunk.start:chunk.end] = True
        assert len(tokenizer(text[chunk.start:chunk.end])["input_ids"]) <= 6
    assert covered.all()
    assert chunks[0].start == 0 and chunks[-1].end == len(text)


def test_large_overlap_still_advances_past_sentence_boundaries():
    text = "one two three. four five six. seven eight nine. " * 5
    chunks, _ = split_narrative(text, Tokenizer(), 6, 5)
    assert all(a.end < b.end for a, b in zip(chunks, chunks[1:]))
    assert chunks[-1].end == len(text)


@pytest.mark.parametrize("position", [0, 30, 59])
def test_beginning_middle_and_end_all_affect_full_text_features(position):
    words = ["ordinary"] * 60
    words[position] = "SIGNAL"
    encoder = FullNarrativeEncoder(Embedder(), overlap=2, batch_size=3)
    features, coverage = encoder.encode([" ".join(words), "ordinary " * 60])
    assert features.shape == (2, 4)
    assert features[0, 0] > 0  # Entire-document weighted average includes the signal.
    assert features[0, 2] == 1  # Maximum channel retains a short local signal.
    assert features[1, 0] == features[1, 2] == 0
    assert coverage[0]["tokens"] == 60 and coverage[0]["chunks"] > 1
    assert coverage[0]["status"] == "complete"


def test_removal_highlight_uses_full_encoding_and_original_offsets():
    text = "\U0001f697 " + "Ordinary detail. " * 20 + "Late SIGNAL detail."
    encoder = FullNarrativeEncoder(Embedder(), overlap=2)
    model = SimpleNamespace(decision_function=lambda values: -values[:, 2])
    encode = lambda texts: encoder.encode(texts)[0]
    details = sentence_sensitivity(text, encode, model, 1., max_sentences=12, return_details=True)
    assert details["status"] == "limited" and details["sentences_tested"] == 12
    assert details["spans"][0]["text"] == "Late SIGNAL detail."
    span = details["spans"][0]
    assert text[span["start"]:span["end"]] == span["text"]
    assert not sentence_sensitivity(text, encode, model, 2.)


def test_newline_sentences_are_not_silently_dropped():
    text = "Normal line\nSIGNAL line\nNormal end"
    encode = lambda texts: np.array([[float("SIGNAL" in t)] for t in texts])
    model = SimpleNamespace(decision_function=lambda v: -v[:, 0])
    detail = sentence_sensitivity(text, encode, model, 1., return_details=True)
    assert detail["sentences_total"] == detail["sentences_tested"] == 3
    assert detail["spans"][0]["text"] == "SIGNAL line"


def manager(tmp_path, monkeypatch):
    embedder = Embedder()
    monkeypatch.setattr("cdqai.detectors.embeddings.SentenceTransformer", lambda *a, **kw: embedder)
    raw = deepcopy(DEFAULT_CONFIG)
    raw["fields"] = {"normalized_mfn_field": "MFN", "narrative_text_field": "Narrative"}
    raw["models"]["narrative"]["chunk_overlap_tokens"] = 2
    return NarrativeEmbeddingManager(CDQAIConfig(raw, tmp_path), logging.getLogger("synthetic")), embedder


def test_cache_rejects_legacy_changed_text_settings_weights_and_corruption(tmp_path, monkeypatch):
    mgr, embedder = manager(tmp_path, monkeypatch)
    frame = pd.DataFrame({"MFN": ["FAKE", "FAKE"], "Narrative": ["word " * 25, "Late SIGNAL."]})
    ep, ip = mgr.config.narrative_embeddings_path, mgr.config.narrative_embedding_index_path
    ep.parent.mkdir(parents=True)
    np.save(ep, np.ones((2, 2)))
    ip.write_text(json.dumps({"mfns": ["FAKE", "FAKE"]}))
    first = mgr.get_embeddings(frame)
    calls = embedder.calls
    np.testing.assert_array_equal(first, mgr.get_embeddings(frame))
    assert embedder.calls == calls
    frame.loc[0, "Narrative"] += " SIGNAL"
    second = mgr.get_embeddings(frame)
    assert embedder.calls > calls and second[0, 2] == 1
    calls = embedder.calls
    mgr._encoder.overlap = 1
    mgr.get_embeddings(frame)
    assert embedder.calls > calls
    calls = embedder.calls
    embedder.weight = 2.
    assert mgr.get_embeddings(frame)[0, 2] == 2
    assert embedder.calls > calls
    calls = embedder.calls
    np.save(ep, np.zeros_like(first))
    assert mgr.get_embeddings(frame)[0, 2] == 2
    assert embedder.calls > calls
    calls = embedder.calls
    ep.write_bytes(b"")
    mgr.get_embeddings(frame)
    assert embedder.calls > calls
    calls = embedder.calls
    mgr.get_embeddings(frame, refresh_cache=True)
    assert embedder.calls > calls
    assert len(list(ep.parent.iterdir())) == 2  # No abandoned temporary cache files.


def test_dashboard_separates_full_text_coverage_from_limited_review():
    text = "Synthetic text."
    analysis = {"narrative_sha256": hashlib.sha256(text.encode()).hexdigest(), "status": "complete",
                "tokens": 900, "chunks": 5, "review": {"status": "limited", "sentences_tested": 12, "sentences_total": 40}}
    payload = _narrative_payload(text, recorded_spans=[], analysis=analysis)
    assert "Full narrative processed" in payload["analysisCoverage"]
    assert "12 of 40" in payload["analysisCoverage"]
    assert "unavailable" in _narrative_payload(text + "changed", analysis=analysis)["analysisCoverage"]


def test_fitted_detector_scores_late_signal_and_carries_coverage(tmp_path, monkeypatch):
    from cdqai.detectors.narrative import NarrativeAnomalyDetector
    from cdqai.evidence.model_evidence import build_model_evidence
    mgr, _ = manager(tmp_path, monkeypatch)
    mgr.config.raw["model_evidence"]["narrative_percentile"] = 75
    texts = ["ordinary " * 60] * 20
    for position in [0, 30, 59]:
        words = ["ordinary"] * 60
        words[position] = "SIGNAL"
        texts.append(" ".join(words))
    frame = pd.DataFrame({"MFN": [f"FAKE-{i}" for i in range(len(texts))], "Narrative": texts})
    detector = NarrativeAnomalyDetector(mgr.config, logging.getLogger("synthetic"))
    detector.embedding_manager = mgr
    scores = detector.score(frame)
    assert scores.iloc[-3:].NarrativeScore.min() > scores.iloc[:20].NarrativeScore.max()
    analysis = json.loads(scores.iloc[-1].NarrativeAnalysis)
    assert analysis["status"] == "complete" and analysis["tokens"] == 60
    assert analysis["review"]["status"] == "insufficient_sentences"
    evidence = build_model_evidence(scores, mgr.config)
    assert any(e.mfn == "FAKE-22" and e.supporting_values["narrative_analysis"]["status"] == "complete"
               for e in evidence.items if e.source == "MODEL_NARRATIVE")
    from datetime import datetime
    from cdqai.data.dataset import CrashDataset, DatasetMetadata
    from cdqai.detectors.model_runner import run_model_scoring
    from cdqai.findings.engine import FindingEngine
    from cdqai.reports.dashboard_report import write_dashboard
    dataset = CrashDataset(frame, frame, frame, DatasetMetadata(datetime.now(), 23, 23, 23, 23, 23, 0, 23, 0, 100.))
    mgr.config.raw["models"]["structured"]["enabled"] = False
    scores, metadata = run_model_scoring(dataset, mgr.config, logging.getLogger("synthetic"))
    assert metadata["narrative_coverage"]["complete_records"] == 23
    evidence = build_model_evidence(scores, mgr.config)
    mgr.config.outputs_dir.mkdir(parents=True, exist_ok=True)
    write_dashboard(dataset, evidence, FindingEngine().run(evidence), mgr.config, logging.getLogger("synthetic"))
    companion = (mgr.config.outputs_dir / "dashboard_narratives.js").read_text(encoding="utf-8")
    payload = json.loads(companion.removeprefix("window.CDQAINarratives = ").strip().removesuffix(";"))
    assert "Full narrative processed: 60 tokens" in payload["FAKE-22"]["analysisCoverage"]
    assert "fewer than two sentences" in payload["FAKE-22"]["analysisCoverage"]


def test_model_export_preserves_duplicate_row_coverage(tmp_path, monkeypatch):
    from cdqai.reports.model_report import write_model_outputs
    mgr, _ = manager(tmp_path, monkeypatch)
    mgr.config.outputs_dir.mkdir(parents=True)
    dataset = SimpleNamespace(merged=pd.DataFrame({"MFN": ["FAKE", "FAKE"], "Narrative": ["First", "Second"]}))
    scores = pd.DataFrame({"MFN": ["FAKE", "FAKE"], "ModelEnsembleScore": [10, 20], "NarrativeAnalysis": ["first-coverage", "second-coverage"]})
    write_model_outputs(dataset, scores, mgr.config, logging.getLogger("synthetic"))
    actual = pd.read_csv(mgr.config.outputs_dir / "model_scores.csv")
    assert len(actual) == 2
    assert actual.NarrativePreview.tolist() == ["First", "Second"]
    assert actual.NarrativeAnalysis.tolist() == scores.NarrativeAnalysis.tolist()


@pytest.mark.skipif(os.getenv("CDQAI_LOCAL_MODEL_TEST") != "1", reason="Explicit offline local-model validation")
def test_real_local_tokenizer_and_model_cover_long_unicode_narrative(tmp_path):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)
    encoder = FullNarrativeEncoder(model, overlap=32, batch_size=16)
    text = "\U0001f697 Fabricated ordinary crash detail. " * 100 + "Fabricated unusual ending."
    chunks, tokens = split_narrative(text, model.tokenizer, encoder.budget, 32)
    assert tokens > model.max_seq_length
    for chunk in chunks:
        assert len(model.tokenizer(text[chunk.start:chunk.end], truncation=False)["input_ids"]) <= model.max_seq_length
    vectors, coverage = encoder.encode([text, text.replace("unusual ending", "different conclusion")])
    dimension = model.get_embedding_dimension() if hasattr(model, "get_embedding_dimension") else model.get_sentence_embedding_dimension()
    assert vectors.shape == (2, dimension * 2)
    assert not np.allclose(vectors[0], vectors[1], atol=1e-7)
    assert coverage[0]["status"] == "complete"
    mgr = NarrativeEmbeddingManager(CDQAIConfig(deepcopy(DEFAULT_CONFIG), tmp_path), logging.getLogger("synthetic"))
    mgr._encoder = encoder
    assert len(mgr.fingerprint()["model_weights"]) == 64
