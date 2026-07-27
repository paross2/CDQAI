from __future__ import annotations
import logging
import pandas as pd
from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset

def write_model_outputs(dataset: CrashDataset, scores: pd.DataFrame, config: CDQAIConfig, logger: logging.Logger) -> None:
    outputs=config.raw.get("outputs",{}); mfn=config.raw["fields"]["normalized_mfn_field"]; narrative=config.raw["fields"]["narrative_text_field"]
    scores_file=config.outputs_dir/outputs.get("model_scores_file","model_scores.csv"); top_file=config.outputs_dir/outputs.get("top_model_anomalies_file","top_model_anomalies.csv"); top_n=int(outputs.get("top_model_anomalies_rows",1000))
    preview=dataset.merged[[mfn,narrative]].copy(); preview["NarrativePreview"]=preview[narrative].fillna("").astype(str).str.slice(0,500); preview=preview[[mfn,"NarrativePreview"]]
    output=scores.merge(preview,on=mfn,how="left")
    logger.info("Writing model scores: %s", scores_file); output.to_csv(scores_file,index=False)
    logger.info("Writing top model anomalies: %s", top_file); output.sort_values("ModelEnsembleScore",ascending=False).head(top_n).to_csv(top_file,index=False)
