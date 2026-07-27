from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset
from cdqai.detectors.narrative import NarrativeAnomalyDetector
from cdqai.detectors.structured import StructuredAnomalyDetector


def run_model_scoring(
    dataset: CrashDataset,
    config: CDQAIConfig,
    logger: logging.Logger,
    refresh_cache: bool = False,
) -> tuple[pd.DataFrame, dict]:
    mfn = config.raw["fields"]["normalized_mfn_field"]
    merged = dataset.merged
    results = pd.DataFrame({mfn: merged[mfn].astype(str).to_numpy()})
    metadata: dict = {}

    structured_cfg = config.raw.get("models", {}).get("structured", {})
    narrative_cfg = config.raw.get("models", {}).get("narrative", {})
    ensemble_cfg = config.raw.get("models", {}).get("ensemble", {})

    if structured_cfg.get("enabled", True):
        results = results.merge(
            StructuredAnomalyDetector(config, logger).score(merged),
            on=mfn,
            how="left",
        )
        metadata["structured_enabled"] = True
    else:
        results["StructuredScore_pct"] = np.nan
        metadata["structured_enabled"] = False

    if narrative_cfg.get("enabled", True):
        results = results.merge(
            NarrativeAnomalyDetector(config, logger).score(
                merged, refresh_cache=refresh_cache
            ),
            on=mfn,
            how="left",
        )
        metadata["narrative_enabled"] = True
    else:
        results["NarrativeScore_pct"] = np.nan
        results["NarrativeAvailable"] = False
        metadata["narrative_enabled"] = False

    sw = float(ensemble_cfg.get("structured_weight", 0.5))
    nw = float(ensemble_cfg.get("narrative_weight", 0.5))
    if sw < 0 or nw < 0 or sw + nw <= 0:
        raise ValueError("Ensemble weights must be nonnegative and sum to a positive value.")

    structured = pd.to_numeric(results.get("StructuredScore_pct"), errors="coerce")
    narrative = pd.to_numeric(results.get("NarrativeScore_pct"), errors="coerce")

    # The ensemble is valid only when both independent model signals exist.
    # A missing narrative must not be converted into a zero or allow a
    # structured-only record to masquerade as a combined-model result.
    ensemble_available = structured.notna() & narrative.notna()
    results["ModelEnsembleScore"] = np.nan
    results.loc[ensemble_available, "ModelEnsembleScore"] = (
        sw * structured.loc[ensemble_available]
        + nw * narrative.loc[ensemble_available]
    ) / (sw + nw)
    results["ModelConfidence"] = results["ModelEnsembleScore"].rank(
        pct=True, na_option="keep"
    ) * 100.0
    results["EnsembleAvailable"] = ensemble_available

    metadata.update(
        {
            "structured_weight": sw,
            "narrative_weight": nw,
            "records_scored": len(results),
            "narratives_available": int(results["NarrativeScore_pct"].notna().sum()),
            "narratives_excluded": int(results["NarrativeScore_pct"].isna().sum()),
        }
    )
    return results, metadata
