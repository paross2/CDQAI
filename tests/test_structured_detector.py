import logging
from pathlib import Path

import numpy as np
import pandas as pd

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.detectors.structured import StructuredAnomalyDetector, percentile_rank


def make_config() -> CDQAIConfig:
    raw = {**DEFAULT_CONFIG}
    raw["fields"] = {
        "normalized_mfn_field": "MFN",
        "narrative_text_field": "NarrativeTxt",
    }
    return CDQAIConfig(raw=raw, project_root=Path.cwd())


def test_percentile_rank_shape():
    values = np.array([1.0, 2.0, 3.0])
    ranked = percentile_rank(values)
    assert ranked.shape == values.shape
    assert ranked.max() == 100.0


def test_geography_county_time_and_identifiers_are_excluded():
    df = pd.DataFrame({
        "MFN": [1, 2, 3],
        "Latitude": [38.0, 37.9, 36.8],
        "Longitude": [-84.5, -85.0, -89.0],
        "CountyNumber": [34, 56, 120],
        "CrashTime": [5, 1359, 2359],
        "RecordID": [100, 101, 102],
        "ContextCountyDVMT": [1.0, 2.0, 3.0],
        "NumberInjured": [0, 1, 2],
        "NarrativeTxt": ["a", "b", "c"],
    })
    detector = StructuredAnomalyDetector(make_config(), logging.getLogger("test"))
    selected = detector.select_features(df)
    assert selected == ["NumberInjured"]
    assert "Latitude" in detector.excluded_columns
    assert "Longitude" in detector.excluded_columns
    assert "CountyNumber" in detector.excluded_columns
    assert "CrashTime" in detector.excluded_columns
    assert "ContextCountyDVMT" in detector.excluded_columns


def test_valid_geolocation_and_county_changes_do_not_change_scores():
    rows = 150
    rng = np.random.default_rng(42)
    base = pd.DataFrame({
        "MFN": np.arange(rows),
        "NumberInjured": rng.integers(0, 5, rows),
        "NumberVehicles": rng.integers(1, 8, rows),
        "Latitude": rng.uniform(36.5, 39.2, rows),
        "Longitude": rng.uniform(-89.5, -82.0, rows),
        "CountyNumber": rng.integers(1, 121, rows),
        "NarrativeTxt": ["test"] * rows,
    })
    changed = base.copy()
    changed["Latitude"] = changed["Latitude"].iloc[::-1].to_numpy()
    changed["Longitude"] = changed["Longitude"].iloc[::-1].to_numpy()
    changed["CountyNumber"] = ((changed["CountyNumber"] + 59) % 120) + 1

    first = StructuredAnomalyDetector(make_config(), logging.getLogger("test")).score(base)
    second = StructuredAnomalyDetector(make_config(), logging.getLogger("test")).score(changed)
    np.testing.assert_allclose(first["StructuredScore"], second["StructuredScore"])
    np.testing.assert_allclose(first["StructuredScore_pct"], second["StructuredScore_pct"])


def test_missing_numeric_values_use_median_not_zero():
    df = pd.DataFrame({"A": [10.0, np.nan, 30.0], "B": [0, 1, 1]})
    prepared = StructuredAnomalyDetector._prepare_features(df, ["A", "B"])
    assert prepared[1, 0] == 20.0
