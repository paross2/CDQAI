from __future__ import annotations

import pandas as pd

from cdqai.features.field_roles import classify_field


def write_field_manifest(dataset, config, logger):
    df = dataset.merged
    cfg = config.raw.get("models", {}).get("structured", {})
    mfn = config.raw["fields"]["normalized_mfn_field"]
    narrative = config.raw["fields"]["narrative_text_field"]
    rows = []
    for column in df.columns:
        decision = classify_field(column, df[column], cfg, mfn, narrative)
        rows.append({
            "FieldName": column,
            "DataType": str(df[column].dtype),
            "Role": decision.role,
            "StructuredModelEligible": decision.eligible,
            "Reason": decision.reason,
            "MissingPercent": round(float(df[column].isna().mean() * 100), 3),
            "UniqueValues": int(df[column].nunique(dropna=True)),
        })
    path = config.outputs_dir / config.raw.get("outputs", {}).get("field_manifest_file", "analysis_field_manifest.csv")
    pd.DataFrame(rows).to_csv(path, index=False)
    logger.info("Field manifest written: %s", path)
    return path
