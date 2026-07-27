from __future__ import annotations
import logging
from pathlib import Path
import pandas as pd

def load_dataframe_cache(path: Path, logger: logging.Logger) -> pd.DataFrame | None:
    if not path.exists(): logger.info("Cache not found: %s", path); return None
    try: logger.info("Loading dataframe cache: %s", path); return pd.read_parquet(path)
    except Exception as exc: logger.warning("Unable to read cache. Falling back to SQL. Error: %s", exc); return None

def write_dataframe_cache(df: pd.DataFrame, path: Path, logger: logging.Logger) -> None:
    try: path.parent.mkdir(parents=True, exist_ok=True); logger.info("Writing dataframe cache: %s", path); df.to_parquet(path, index=False)
    except Exception as exc: logger.warning("Unable to write cache: %s", exc)
