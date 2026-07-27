from __future__ import annotations
import json, logging
from dataclasses import asdict
import pandas as pd
from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset

def write_dataset_outputs(dataset: CrashDataset, config: CDQAIConfig, logger: logging.Logger) -> None:
    outputs=config.raw.get("outputs",{}); sample_rows=int(outputs.get("sample_rows",1000))
    metadata_dict=asdict(dataset.metadata); summary_df=pd.DataFrame([{"Metric":k,"Value":v} for k,v in metadata_dict.items()])
    summary_path=config.outputs_dir/outputs.get("summary_file","dataset_summary.csv"); sample_path=config.outputs_dir/outputs.get("sample_file","merged_sample.csv"); metadata_json_path=config.outputs_dir/"dataset_metadata.json"
    logger.info("Writing dataset summary: %s", summary_path); summary_df.to_csv(summary_path,index=False)
    logger.info("Writing merged sample: %s", sample_path); dataset.merged.head(sample_rows).to_csv(sample_path,index=False)
    logger.info("Writing dataset metadata JSON: %s", metadata_json_path); metadata_json_path.write_text(json.dumps(metadata_dict, indent=2, default=str), encoding="utf-8")
