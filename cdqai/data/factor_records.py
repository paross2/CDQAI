# CDQAI file version: 2.5.0
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from cdqai.core.config import CDQAIConfig
from cdqai.kentucky.factor_codes import FACTOR_CATALOGS


def _quoted_identifier(value: object, setting: str) -> str:
    name = str(value).strip()
    if not name or any(character in name for character in "[];.") or any(
        ord(character) < 32 for character in name
    ):
        raise ValueError(f"{setting} must be a single SQL identifier.")
    return f"[{name.replace(']', ']]')}]"


def _quoted_table(value: object) -> str:
    parts = str(value).split(".")
    if len(parts) != 3:
        raise ValueError("factor_review table entries must be database.schema.table.")
    return ".".join(_quoted_identifier(part, "factor table name") for part in parts)


def load_factor_records(
    config: CDQAIConfig, engine: Engine, logger: logging.Logger
) -> pd.DataFrame:
    """Load only crash linkage and factor-code columns from configured factor tables."""
    settings = config.raw.get("factor_review", {})
    categories = settings.get("categories", {})
    queries = []
    for factor_type, catalog in FACTOR_CATALOGS.items():
        category = categories.get(factor_type, {})
        tables = category.get("tables", [])
        if not isinstance(tables, list) or not tables:
            raise ValueError(
                f"Configure factor_review.categories.{factor_type}.tables before enabling factor review."
            )
        mfn_field = _quoted_identifier(category.get("mfn_field", "MFN"), "mfn_field")
        year_field = _quoted_identifier(category.get("year_field", "YR"), "year_field")
        code_field = _quoted_identifier(
            category.get("code_field", catalog["field"]), "code_field"
        )
        for table in tables:
            queries.append((factor_type, text(
                f"SELECT {mfn_field} AS CDQAI_MFN, {year_field} AS CDQAI_YEAR, "
                f"{code_field} AS CDQAI_CODE FROM {_quoted_table(table)}"
            )))

    frames = []
    for factor_type, query in queries:
        frame = pd.read_sql(query, engine)
        frame["FactorType"] = factor_type
        frames.append(frame)

    records = pd.concat(frames, ignore_index=True)
    if records.empty:
        raise ValueError("Configured factor tables returned no rows.")
    if records[["CDQAI_MFN", "CDQAI_YEAR", "CDQAI_CODE"]].isna().any().any():
        logger.warning("Some projected factor rows have a missing MFN, year, or code.")
    records = records.rename(columns={
        "CDQAI_MFN": "MFN",
        "CDQAI_YEAR": "Year",
        "CDQAI_CODE": "Code",
    })
    logger.info("Projected factor records loaded: %s", f"{len(records):,}")
    return records[["FactorType", "MFN", "Year", "Code"]]
