import logging

import numpy as np
import pandas as pd

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.detectors.narrative import NarrativeAnomalyDetector


def test_blank_narratives_are_excluded_from_scoring(tmp_path, monkeypatch):
    raw = DEFAULT_CONFIG.copy()
    raw["fields"] = {
        "normalized_mfn_field": "MFN",
        "narrative_text_field": "NarrativeTxt",
    }
    config = CDQAIConfig(raw=raw, project_root=tmp_path)
    detector = NarrativeAnomalyDetector(config, logging.getLogger("test"))

    observed = {}

    def fake_embeddings(df, refresh_cache=False):
        observed["mfns"] = df["MFN"].tolist()
        return np.array([[0.0, 0.0], [1.0, 1.0]])

    monkeypatch.setattr(detector.embedding_manager, "get_embeddings", fake_embeddings)

    df = pd.DataFrame(
        {
            "MFN": ["1", "2", "3", "4"],
            "NarrativeTxt": [None, "   ", "Vehicle struck deer.", "Rear-end collision."],
        }
    )
    result = detector.score(df)

    assert observed["mfns"] == ["3", "4"]
    assert result.loc[result["MFN"].isin(["1", "2"]), "NarrativeScore_pct"].isna().all()
    assert not result.loc[result["MFN"].isin(["3", "4"]), "NarrativeScore_pct"].isna().any()
    assert result["NarrativeAvailable"].tolist() == [False, False, True, True]
