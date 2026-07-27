from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset, DatasetMetadata


def normalize_mfn(df: pd.DataFrame, mfn_col: str) -> pd.DataFrame:
    out = df.copy()
    out[mfn_col] = out[mfn_col].astype(str).str.strip()
    return out


def build_dataset(
    crashes: pd.DataFrame,
    narratives: pd.DataFrame,
    config: CDQAIConfig,
    logger: logging.Logger,
) -> CrashDataset:
    fields = config.raw["fields"]
    mfn = fields["normalized_mfn_field"]
    narrative_text = fields["narrative_text_field"]

    raw_narrative_count = len(narratives)

    logger.info("Normalizing MFN fields.")
    crashes = normalize_mfn(crashes, mfn)
    narratives = normalize_mfn(narratives, mfn)

    logger.info("Filtering narratives to crash MFNs.")
    narratives_filtered = narratives[narratives[mfn].isin(crashes[mfn])].copy()

    logger.info("Merging crash and narrative data.")
    merged = pd.merge(crashes, narratives_filtered, on=mfn, how="left")
    merged[narrative_text] = merged[narrative_text].fillna("")

    if len(merged) == 0:
        raise RuntimeError("No records after merge. Check MFN alignment.")

    metadata = build_metadata(
        merged=merged,
        config=config,
        crash_records=len(crashes),
        narrative_records_raw=raw_narrative_count,
        narrative_records_after_filter=len(narratives_filtered),
    )

    logger.info("Merged records: %s", f"{metadata.merged_records:,}")
    logger.info("Records without narrative: %s", f"{metadata.records_without_narrative:,}")

    return CrashDataset(
        crashes=crashes,
        narratives=narratives_filtered,
        merged=merged,
        metadata=metadata,
    )


def build_dataset_from_merged_cache(
    merged: pd.DataFrame,
    config: CDQAIConfig,
    logger: logging.Logger,
) -> CrashDataset:
    """Build a CrashDataset from cached merged data.

    This avoids unnecessary SQL reloads for rule/model runs when the merged parquet cache exists.
    Raw crash/narrative frames are intentionally empty because the merged frame is sufficient
    for downstream scoring and evidence generation.
    """
    mfn = config.raw["fields"]["normalized_mfn_field"]

    if mfn not in merged.columns:
        raise KeyError(f"Cached merged dataset is missing MFN field: {mfn}")

    merged = normalize_mfn(merged, mfn)

    metadata = build_metadata(
        merged=merged,
        config=config,
        crash_records=len(merged),
        narrative_records_raw=0,
        narrative_records_after_filter=0,
    )

    logger.info("Dataset built from merged cache.")
    logger.info("Cached merged records: %s", f"{metadata.merged_records:,}")

    return CrashDataset(
        crashes=pd.DataFrame(),
        narratives=pd.DataFrame(),
        merged=merged,
        metadata=metadata,
    )


def build_metadata(
    merged: pd.DataFrame,
    config: CDQAIConfig,
    crash_records: int,
    narrative_records_raw: int,
    narrative_records_after_filter: int,
) -> DatasetMetadata:
    mfn = config.raw["fields"]["normalized_mfn_field"]
    narrative_text = config.raw["fields"]["narrative_text_field"]

    if narrative_text in merged.columns:
        narrative_lengths = merged[narrative_text].fillna("").astype(str).str.len()
    else:
        narrative_lengths = pd.Series([0] * len(merged))

    return DatasetMetadata(
        created_at=datetime.now(),
        crash_records=crash_records,
        narrative_records_raw=narrative_records_raw,
        narrative_records_after_filter=narrative_records_after_filter,
        merged_records=len(merged),
        distinct_mfns=merged[mfn].nunique(),
        duplicate_mfn_rows=len(merged) - merged[mfn].nunique(),
        records_with_narrative=int((narrative_lengths > 0).sum()),
        records_without_narrative=int((narrative_lengths == 0).sum()),
        average_narrative_length=float(narrative_lengths.mean()) if len(narrative_lengths) else 0.0,
    )
