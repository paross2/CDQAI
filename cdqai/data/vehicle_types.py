# CDQAI file version: 2.5.0
from __future__ import annotations

import logging
import re

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from cdqai.core.config import CDQAIConfig


IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9 #]*")


def _quoted_identifier(value: object, setting: str) -> str:
    name = str(value).strip()
    if not IDENTIFIER.fullmatch(name):
        raise ValueError(f"{setting} must be a simple SQL identifier.")
    return f"[{name}]"


def _quoted_table(value: object) -> str:
    parts = str(value).split(".")
    if len(parts) != 3:
        raise ValueError("scooter_classifier.vehicle_tables entries must be database.schema.table.")
    return ".".join(_quoted_identifier(part, "vehicle table name") for part in parts)


def load_vehicle_type_records(
    config: CDQAIConfig, engine: Engine, logger: logging.Logger
) -> pd.DataFrame:
    cfg = config.raw.get("scooter_classifier", {})
    tables = cfg.get("vehicle_tables", [])
    if not isinstance(tables, list) or not tables:
        raise ValueError("Configure scooter_classifier.vehicle_tables before enabling the scooter classifier.")

    mfn_field = _quoted_identifier(cfg.get("vehicle_mfn_field", "Master File"), "vehicle_mfn_field")
    year_field = _quoted_identifier(cfg.get("vehicle_year_field", "YR"), "vehicle_year_field")
    unit_field = _quoted_identifier(cfg.get("unit_type_field", "Unit Type Code"), "unit_type_field")
    frames = []
    for table in tables:
        query = text(
            f"SELECT {mfn_field} AS CDQAI_MFN, {year_field} AS CDQAI_YEAR, "
            f"{unit_field} AS CDQAI_UNIT_TYPE FROM {_quoted_table(table)}"
        )
        frames.append(pd.read_sql(query, engine))

    records = pd.concat(frames, ignore_index=True)
    if records.empty:
        raise ValueError("Configured vehicle tables returned no rows; scooter coding cannot be reconciled.")
    logger.info("Projected vehicle-type records loaded: %s", f"{len(records):,}")
    return records
