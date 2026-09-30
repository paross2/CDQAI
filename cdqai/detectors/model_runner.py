# CDQAI file version: 2.3.1
from __future__ import annotations

import logging
import math
import numpy as np
import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset
from cdqai.detectors.structured import StructuredAnomalyDetector


def combine_model_scores(results: pd.DataFrame, structured_weight: float, narrative_weight: float) -> pd.DataFrame:
    weights = (structured_weight, narrative_weight)
    if any(not math.isfinite(w) or w < 0 for w in weights) or sum(weights) <= 0:
        raise ValueError("Ensemble weights must be finite, nonnegative, and sum to a positive value.")
    result = results.copy()
    s = pd.to_numeric(result["StructuredScore_pct"], errors="coerce")
    n = pd.to_numeric(result["NarrativeScore_pct"], errors="coerce")
    if "NarrativeAvailable" in result:
        n = n.where(result["NarrativeAvailable"].fillna(False).astype(bool))
        result["NarrativeScore_pct"] = n
    sw = s.notna().astype(float) * structured_weight
    nw = n.notna().astype(float) * narrative_weight
    total = (sw + nw).replace(0, np.nan)
    result["EffectiveStructuredWeight"] = (sw / total).fillna(0)
    result["EffectiveNarrativeWeight"] = (nw / total).fillna(0)
    result["ModelEnsembleScore"] = (sw * s.fillna(0) + nw * n.fillna(0)) / total
    both = (sw > 0) & (nw > 0)
    result["EnsembleEligible"] = both
    result["ModelConfidence"] = np.nan
    # A single available model is not a second, corroborating ensemble signal.
    result.loc[both, "ModelConfidence"] = result.loc[both, "ModelEnsembleScore"].rank(pct=True) * 100
    return result


def run_model_scoring(dataset: CrashDataset, config: CDQAIConfig, logger: logging.Logger,
                      refresh_cache: bool = False) -> tuple[pd.DataFrame, dict]:
    mfn = config.raw["fields"]["normalized_mfn_field"]
    text = config.raw["fields"]["narrative_text_field"]
    merged = dataset.merged
    results = pd.DataFrame({mfn: merged[mfn].astype(str).to_numpy()})
    results["NarrativeAvailable"] = merged[text].fillna("").astype(str).str.strip().ne("").to_numpy()
    results["StructuredScore_pct"] = np.nan
    results["NarrativeScore_pct"] = np.nan
    models = config.raw.get("models", {})
    structured_cfg = models.get("structured", {})
    narrative_cfg = models.get("narrative", {})
    ensemble_cfg = models.get("ensemble", {})
    metadata = {"structured_enabled": bool(structured_cfg.get("enabled", True)),
                "narrative_enabled": bool(narrative_cfg.get("enabled", True))}

    def attach(scored: pd.DataFrame) -> None:
        if len(scored) != len(results) or scored[mfn].astype(str).tolist() != results[mfn].tolist():
            raise ValueError("Model score rows do not align with source rows.")
        # Do not merge on duplicated MFNs and multiply score rows.
        for column in scored.columns:
            if column != mfn:
                results[column] = scored[column].to_numpy()

    if metadata["structured_enabled"]:
        detector = StructuredAnomalyDetector(config, logger)
        attach(detector.score(merged))
        metadata.update(structured_fields_used=detector.feature_columns,
                        structured_fields_excluded=detector.excluded_columns)
    if metadata["narrative_enabled"]:
        from cdqai.detectors.narrative import NarrativeAnomalyDetector
        attach(NarrativeAnomalyDetector(config, logger).score(merged, refresh_cache))
    sw = float(ensemble_cfg.get("structured_weight", 0.5))
    nw = float(ensemble_cfg.get("narrative_weight", 0.5))
    results = combine_model_scores(results, sw, nw)
    metadata.update(structured_weight=sw, narrative_weight=nw, records_scored=len(results),
                    narratives_not_scored=int(results["NarrativeScore_pct"].isna().sum()),
                    context=dataset.context_summary)
    return results, metadata
