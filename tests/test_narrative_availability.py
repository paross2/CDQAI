# CDQAI file version: 2.3.2
from copy import deepcopy
import logging
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.detectors.model_runner import combine_model_scores, run_model_scoring
from cdqai.evidence.model_evidence import build_model_evidence


def config(tmp_path):
    raw = deepcopy(DEFAULT_CONFIG)
    raw["fields"] = {"normalized_mfn_field": "MFN", "narrative_text_field": "NarrativeTxt"}
    return CDQAIConfig(raw, tmp_path)


def test_blank_narratives_have_no_narrative_or_ensemble_evidence(tmp_path):
    results = pd.DataFrame({"MFN": ["FAKE-1", "FAKE-2"], "NarrativeAvailable": [False, True],
                            "StructuredScore_pct": [99.99, 20], "NarrativeScore_pct": [np.nan, 99.99]})
    combined = combine_model_scores(results, 0.5, 0.5)
    assert combined.loc[0, "EffectiveStructuredWeight"] == 1
    assert combined.loc[0, "EffectiveNarrativeWeight"] == 0
    assert pd.isna(combined.loc[0, "ModelConfidence"])
    evidence = build_model_evidence(combined, config(tmp_path))
    categories = {x.category for x in evidence.items if x.mfn == "FAKE-1"}
    assert categories == {"Structured Anomaly"}


def test_no_active_models_produce_no_model_evidence(tmp_path):
    results = pd.DataFrame({"MFN": ["FAKE"], "StructuredScore_pct": [np.nan], "NarrativeScore_pct": [np.nan]})
    assert not build_model_evidence(combine_model_scores(results, 0.5, 0.5), config(tmp_path)).items


@pytest.mark.parametrize("weights", [(-1, 2), (0, 0), (float("nan"), 1), (1, float("inf"))])
def test_invalid_ensemble_weights_are_rejected(weights):
    with pytest.raises(ValueError):
        combine_model_scores(pd.DataFrame(), *weights)


def test_ensemble_is_not_an_additional_base_model(tmp_path):
    scores = pd.DataFrame({"MFN": ["FAKE"], "StructuredScore_pct": [100],
                           "NarrativeScore_pct": [90], "ModelConfidence": [100]})
    evidence = build_model_evidence(scores, config(tmp_path))
    assert not any(x.category == "Multi-Model Anomaly" for x in evidence.items)


def test_blank_text_not_used_for_narrative_fit(tmp_path, monkeypatch):
    from cdqai.detectors.narrative import NarrativeAnomalyDetector
    detector = NarrativeAnomalyDetector(config(tmp_path), logging.getLogger("synthetic"))
    frame = pd.DataFrame({"MFN": ["FAKE-0", "FAKE-1", "FAKE-2"],
                          "NarrativeTxt": ["   ", "Fabricated one", "Fabricated two"]})
    monkeypatch.setattr(detector.embedding_manager, "get_embeddings", lambda *a, **k: np.array([[1000., 1000.], [1., 2.], [2., 1.]]))
    result = detector.score(frame)
    assert pd.isna(result.loc[0, "NarrativeScore_pct"])
    assert result["NarrativeScored"].tolist() == [False, True, True]


def test_all_blank_narratives_never_request_embeddings(tmp_path, monkeypatch):
    from cdqai.detectors.narrative import NarrativeAnomalyDetector
    detector = NarrativeAnomalyDetector(config(tmp_path), logging.getLogger("synthetic"))
    def forbidden(*args, **kwargs):
        pytest.fail("Empty narratives attempted an embedding request")
    monkeypatch.setattr(detector.embedding_manager, "get_embeddings", forbidden)
    frame = pd.DataFrame({"MFN": ["FAKE-1", "FAKE-2"], "NarrativeTxt": [None, " "]})
    assert detector.score(frame)["NarrativeScore_pct"].isna().all()


def test_inconsistent_blank_narrative_scores_cannot_create_evidence(tmp_path):
    scores = pd.DataFrame({"MFN": ["FAKE"], "NarrativeAvailable": [False],
                           "StructuredScore_pct": [20], "NarrativeScore_pct": [100], "ModelConfidence": [100]})
    combined = combine_model_scores(scores, 0.5, 0.5)
    assert pd.isna(combined.loc[0, "NarrativeScore_pct"])
    assert not build_model_evidence(scores, config(tmp_path)).items


def test_duplicates_do_not_multiply_model_score_rows(tmp_path):
    cfg = config(tmp_path)
    cfg.raw["models"]["narrative"]["enabled"] = False
    frame = pd.DataFrame({"MFN": ["FAKE", "FAKE", "FAKE-2"], "NarrativeTxt": ["", "", ""], "NumberVehicles": [1, 2, 3]})
    scores, _ = run_model_scoring(SimpleNamespace(merged=frame, context_summary={}), cfg, logging.getLogger("synthetic"))
    assert len(scores) == len(frame)
