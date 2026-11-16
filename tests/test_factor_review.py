# CDQAI file version: 2.5.1
from copy import deepcopy
import logging

import pandas as pd
import pytest

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.data.factor_records import load_factor_records


def make_config():
    raw = deepcopy(DEFAULT_CONFIG)
    raw["factor_review"]["enabled"] = True
    raw["factor_review"]["categories"] = {
        "human": {
            "tables": ["YOUR_DATABASE.YOUR_SCHEMA.YOUR_HUMAN_FACTOR_SOURCE"],
            "mfn_field": "MFN",
            "year_field": "YR",
            "code_field": "HumanFactorCode",
        },
        "environmental": {
            "tables": ["YOUR_DATABASE.YOUR_SCHEMA.YOUR_ENVIRONMENT_FACTOR_SOURCE"],
            "mfn_field": "MFN",
            "year_field": "YR",
            "code_field": "EnvironmentalFactorCode",
        },
        "vehicle": {
            "tables": ["YOUR_DATABASE.YOUR_SCHEMA.YOUR_VEHICLE_FACTOR_SOURCE"],
            "mfn_field": "MFN",
            "year_field": "YR",
            "code_field": "VehicularFactorCode",
        },
    }
    return CDQAIConfig(raw, project_root=None)


def test_factor_loader_projects_only_linkage_and_code_fields(monkeypatch):
    queries = []

    def fake_read_sql(query, engine):
        queries.append(str(query))
        return pd.DataFrame({
            "CDQAI_MFN": [123],
            "CDQAI_YEAR": [2024],
            "CDQAI_CODE": ["02"],
        })

    monkeypatch.setattr("cdqai.data.factor_records.pd.read_sql", fake_read_sql)
    records = load_factor_records(make_config(), engine=object(), logger=logging.getLogger(__name__))

    assert list(records.columns) == ["FactorType", "MFN", "Year", "Code"]
    assert records["FactorType"].tolist() == ["human", "environmental", "vehicle"]
    assert len(queries) == 3
    assert all("SELECT *" not in query for query in queries)
    assert "[MFN] AS CDQAI_MFN" in queries[0]
    assert "[YR] AS CDQAI_YEAR" in queries[0]
    assert "[HumanFactorCode] AS CDQAI_CODE" in queries[0]
    assert "[YOUR_DATABASE].[YOUR_SCHEMA].[YOUR_HUMAN_FACTOR_SOURCE]" in queries[0]


def test_factor_loader_rejects_unsafe_or_unqualified_table_names(monkeypatch):
    config = make_config()
    config.raw["factor_review"]["categories"]["human"]["tables"] = [
        "YOUR_DATABASE.YOUR_SCHEMA.BAD]TABLE"
    ]

    def unexpected_query(*args, **kwargs):
        pytest.fail("Unsafe identifier must be rejected before querying.")

    monkeypatch.setattr("cdqai.data.factor_records.pd.read_sql", unexpected_query)
    with pytest.raises(ValueError, match="single SQL identifier"):
        load_factor_records(config, engine=object(), logger=logging.getLogger(__name__))


def test_factor_loader_requires_tables_for_each_enabled_category():
    config = make_config()
    config.raw["factor_review"]["categories"]["vehicle"]["tables"] = []

    with pytest.raises(ValueError, match="categories.vehicle.tables"):
        load_factor_records(config, engine=object(), logger=logging.getLogger(__name__))
