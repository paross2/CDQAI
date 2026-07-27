import logging
import sys
import types

import numpy as np
import pandas as pd

# Permit importing the detector module in minimal test environments.
if "sentence_transformers" not in sys.modules:
    module = types.ModuleType("sentence_transformers")
    module.SentenceTransformer = object
    sys.modules["sentence_transformers"] = module

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.data.dataset import CrashDataset
from cdqai.detectors import model_runner


def test_missing_narrative_cannot_form_ensemble(tmp_path, monkeypatch):
    raw = DEFAULT_CONFIG.copy()
    raw["fields"] = {
        "normalized_mfn_field": "MFN",
        "narrative_text_field": "NarrativeTxt",
    }
    config = CDQAIConfig(raw=raw, project_root=tmp_path)
    merged = pd.DataFrame(
        {
            "MFN": ["1", "2"],
            "NarrativeTxt": [None, "Usable narrative"],
        }
    )
    dataset = CrashDataset(
        crashes=merged.copy(),
        narratives=merged[["MFN", "NarrativeTxt"]].copy(),
        merged=merged,
        metadata={},
    )

    monkeypatch.setattr(
        model_runner.StructuredAnomalyDetector,
        "score",
        lambda self, df: pd.DataFrame(
            {
                "MFN": ["1", "2"],
                "StructuredScore_pct": [99.9, 90.0],
            }
        ),
    )
    monkeypatch.setattr(
        model_runner.NarrativeAnomalyDetector,
        "score",
        lambda self, df, refresh_cache=False: pd.DataFrame(
            {
                "MFN": ["1", "2"],
                "NarrativeScore_pct": [np.nan, 80.0],
                "NarrativeAvailable": [False, True],
            }
        ),
    )

    scores, metadata = model_runner.run_model_scoring(
        dataset, config, logging.getLogger("test")
    )

    missing = scores.loc[scores["MFN"] == "1"].iloc[0]
    usable = scores.loc[scores["MFN"] == "2"].iloc[0]
    assert pd.isna(missing["ModelEnsembleScore"])
    assert pd.isna(missing["ModelConfidence"])
    assert not bool(missing["EnsembleAvailable"])
    assert usable["ModelEnsembleScore"] == 85.0
    assert bool(usable["EnsembleAvailable"])
    assert metadata["narratives_excluded"] == 1
