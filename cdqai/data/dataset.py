from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
@dataclass(frozen=True)
class DatasetMetadata:
    created_at: datetime
    crash_records: int
    narrative_records_raw: int
    narrative_records_after_filter: int
    merged_records: int
    distinct_mfns: int
    duplicate_mfn_rows: int
    records_with_narrative: int
    records_without_narrative: int
    average_narrative_length: float
@dataclass
class CrashDataset:
    crashes: pd.DataFrame
    narratives: pd.DataFrame
    merged: pd.DataFrame
    metadata: DatasetMetadata
