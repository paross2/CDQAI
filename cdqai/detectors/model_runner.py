from __future__ import annotations
import logging
import pandas as pd
from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset
from cdqai.detectors.narrative import NarrativeAnomalyDetector
from cdqai.detectors.structured import StructuredAnomalyDetector

def run_model_scoring(dataset: CrashDataset, config: CDQAIConfig, logger: logging.Logger, refresh_cache: bool=False) -> tuple[pd.DataFrame, dict]:
    mfn=config.raw["fields"]["normalized_mfn_field"]; merged=dataset.merged
    results=pd.DataFrame({mfn: merged[mfn].astype(str).to_numpy()}); metadata={}
    structured_cfg=config.raw.get("models",{}).get("structured",{}); narrative_cfg=config.raw.get("models",{}).get("narrative",{}); ensemble_cfg=config.raw.get("models",{}).get("ensemble",{})
    if structured_cfg.get("enabled", True):
        results=results.merge(StructuredAnomalyDetector(config, logger).score(merged), on=mfn, how="left"); metadata["structured_enabled"]=True
    else: results["StructuredScore_pct"]=0.0; metadata["structured_enabled"]=False
    if narrative_cfg.get("enabled", True):
        results=results.merge(NarrativeAnomalyDetector(config, logger).score(merged, refresh_cache), on=mfn, how="left"); metadata["narrative_enabled"]=True
    else: results["NarrativeScore_pct"]=0.0; metadata["narrative_enabled"]=False
    sw=float(ensemble_cfg.get("structured_weight",0.5)); nw=float(ensemble_cfg.get("narrative_weight",0.5)); total=sw+nw
    if total <= 0: raise ValueError("Ensemble weights must sum to a positive value.")
    results["ModelEnsembleScore"]=(sw*results["StructuredScore_pct"].fillna(0)+nw*results["NarrativeScore_pct"].fillna(0))/total
    results["ModelConfidence"]=results["ModelEnsembleScore"].rank(pct=True)*100.0
    metadata.update({"structured_weight": sw, "narrative_weight": nw, "records_scored": len(results)})
    return results, metadata
