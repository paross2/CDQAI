# CDQAI file version: 2.3.1
from types import SimpleNamespace
import hashlib
import numpy as np
import pandas as pd
from cdqai.detectors.narrative_spans import sentence_sensitivity
from cdqai.reports.dashboard_report import _narrative_payload
from cdqai.rules.injury import NarrativeInjuryConflictRule


def test_sentence_removal_measures_score_drop_without_marking_whole_narrative():
    text = "Ordinary fabricated sentence. Unusual fabricated segment. Final normal sentence."
    encode = lambda texts: np.array([[float("Unusual" in t)] for t in texts])
    model = SimpleNamespace(decision_function=lambda vectors: -vectors[:, 0])
    spans = sentence_sensitivity(text, encode, model, 1.0)
    assert len(spans) == 1
    assert spans[0]["text"] == "Unusual fabricated segment."
    payload = _narrative_payload(text, recorded_spans=spans)
    assert payload["narrativeFull"] == text
    assert payload["evidenceMethod"] == "sentence_removal_sensitivity"
    assert payload["evidenceSpans"][0]["score_drop"] == 1.0
    assert sentence_sensitivity(text, encode, model, 2.0) == []


def test_rule_records_late_trigger_and_preserves_unicode_offsets():
    text = "  🚗 " + "Ordinary fabricated detail. " * 30 + "Passenger reported pain."
    cfg = SimpleNamespace(raw={"fields": {"normalized_mfn_field": "MFN", "narrative_text_field": "Narrative"},
        "rules": {"injury_conflict": {"injury_field_candidates": ["Injury"], "no_injury_values": ["none"]}}})
    evidence = NarrativeInjuryConflictRule().evaluate(pd.DataFrame({"MFN": ["FAKE"], "Narrative": [text], "Injury": ["none"]}), cfg).evidence
    spans = evidence[0].supporting_values["narrative_spans"]
    assert spans[0]["start"] > 500
    payload = _narrative_payload(text, recorded_spans=spans)
    assert payload["evidenceSpans"][0]["text"] == "pain"
    assert _narrative_payload(text + " changed", recorded_spans=spans)["evidenceSpans"] == []


def test_no_substring_or_false_statistical_claim_for_structured_finding():
    assert _narrative_payload("Paint was scratched.", "pain")["evidenceSpans"] == []
    assert _narrative_payload("Valid text.", recorded_spans=[], narrative_model=False)["evidenceMethod"] == "no_segment_evidence"


def test_scoring_carries_sensitivity_to_model_evidence(monkeypatch, tmp_path):
    from copy import deepcopy
    import logging
    from cdqai.core.config import DEFAULT_CONFIG, CDQAIConfig
    from cdqai.detectors.narrative import NarrativeAnomalyDetector
    from cdqai.evidence.model_evidence import build_model_evidence
    raw = deepcopy(DEFAULT_CONFIG)
    raw["fields"] = {"normalized_mfn_field": "MFN", "narrative_text_field": "Narrative"}
    cfg = CDQAIConfig(raw, tmp_path)
    class Model:
        def fit(self, values):
            return self
        def decision_function(self, values):
            return -values[:, 0]
    monkeypatch.setattr("cdqai.detectors.narrative.IsolationForest", lambda **kw: Model())
    detector = NarrativeAnomalyDetector(cfg, logging.getLogger("synthetic"))
    monkeypatch.setattr(detector.embedding_manager, "get_embeddings", lambda *a, **kw: np.array([[0.], [0.], [1.]]))
    monkeypatch.setattr(detector.embedding_manager, "encode_review_texts", lambda texts: np.array([[float("Unusual" in t)] for t in texts]))
    scores = detector.score(pd.DataFrame({"MFN": ["FAKE1", "FAKE2", "FAKE3"],
        "Narrative": ["Ordinary.", "Normal.", "Normal sentence. Unusual fabricated segment."]}))
    assert scores.NarrativeScore.tolist() == [0., 0., 1.]
    item = next(x for x in build_model_evidence(scores, cfg).items if x.source == "MODEL_NARRATIVE")
    assert item.supporting_values["narrative_spans"][0]["text"] == "Unusual fabricated segment."
