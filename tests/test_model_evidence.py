import pandas as pd
from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.evidence.model_evidence import build_model_evidence

def test_model_scores_become_evidence(tmp_path):
    raw = DEFAULT_CONFIG.copy()
    raw["fields"] = {"normalized_mfn_field": "MFN", "narrative_text_field": "NarrativeTxt"}
    config = CDQAIConfig(raw=raw, project_root=tmp_path)
    scores = pd.DataFrame({"MFN":["1"], "StructuredScore_pct":[99.95], "NarrativeScore_pct":[99.8], "ModelConfidence":[99.99]})
    evidence = build_model_evidence(scores, config)
    assert len(evidence.items) == 4
    assert any(x.category == "Multi-Model Anomaly" for x in evidence.items)
