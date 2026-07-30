from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd


def normalize_field_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


@dataclass(frozen=True)
class FieldDecision:
    role: str
    eligible: bool
    reason: str


DEFAULT_GEOGRAPHIC_NAMES = {
    "latitude", "lat", "gpslatitude", "crashlatitude", "decimallatitude",
    "longitude", "lon", "lng", "long", "gpslongitude", "crashlongitude", "decimallongitude",
    "xcoordinate", "ycoordinate", "xcoord", "ycoord", "easting", "northing",
}
DEFAULT_COUNTY_NAMES = {
    "countynumber", "countyno", "county", "cnty", "countycode", "countyid",
}
DEFAULT_TIME_NAMES = {
    "time", "crashtime", "collisiontime", "accidenttime", "timeofday", "hourminute", "hhmm",
}
DEFAULT_IDENTIFIER_HINTS = {
    "mfn", "masterfile", "masterfilenumber", "recordid", "rowid", "sequenceid", "sourceid",
}


def classify_field(
    column: str,
    series: pd.Series,
    structured_cfg: dict[str, Any],
    normalized_mfn_field: str,
    narrative_field: str,
) -> FieldDecision:
    name = str(column)
    normalized = normalize_field_name(name)
    mfn_normalized = normalize_field_name(normalized_mfn_field)
    narrative_normalized = normalize_field_name(narrative_field)

    include_fields = {normalize_field_name(x) for x in structured_cfg.get("include_fields", [])}
    explicit_exclusions = {normalize_field_name(x) for x in structured_cfg.get("exclude_fields", [])}
    prefixes = tuple(normalize_field_name(x) for x in structured_cfg.get("exclude_prefixes", ["Context"]))
    geographic = DEFAULT_GEOGRAPHIC_NAMES | {
        normalize_field_name(x) for x in structured_cfg.get("geographic_fields", [])
    }
    county = DEFAULT_COUNTY_NAMES | {
        normalize_field_name(x) for x in structured_cfg.get("county_fields", [])
    }
    temporal = DEFAULT_TIME_NAMES | {
        normalize_field_name(x) for x in structured_cfg.get("hhmm_time_fields", [])
    }
    identifiers = DEFAULT_IDENTIFIER_HINTS | {
        normalize_field_name(x) for x in structured_cfg.get("identifier_fields", [])
    }

    if normalized == mfn_normalized or normalized in identifiers:
        return FieldDecision("Identifier", False, "Record linkage or source identifier")
    if normalized == narrative_normalized:
        return FieldDecision("Text feature", False, "Used by the narrative model")
    if prefixes and normalized.startswith(prefixes):
        return FieldDecision("Context/provenance", False, "Excluded from global structured anomaly scoring")
    if normalized in geographic:
        return FieldDecision("Geographic context", False, "Retained for mapping and explicit spatial validation only")
    if normalized in county:
        return FieldDecision("Grouping/context", False, "County is a join and comparison-context field, not a global anomaly feature")
    if normalized in temporal:
        return FieldDecision("Temporal source field", False, "Raw HHMM/time values require cyclical transformation before model use")
    if normalized in explicit_exclusions:
        return FieldDecision("Configured exclusion", False, "Explicitly excluded in structured-model configuration")
    if include_fields and normalized not in include_fields:
        return FieldDecision("Not approved", False, "Not present in the explicit structured-model include list")
    if not pd.api.types.is_numeric_dtype(series):
        return FieldDecision("Categorical/source field", False, "Retained for rules and analyst review")
    if series.nunique(dropna=True) <= 1:
        return FieldDecision("Non-informative numeric", False, "Constant or empty numeric field")
    return FieldDecision("Numeric analytical feature", True, "Approved numeric field for the global structured model")
