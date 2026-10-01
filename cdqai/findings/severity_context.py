# CDQAI file version: 2.3.6
"""Crash severity comes only from an explicitly configured, reviewed code mapping."""
from __future__ import annotations

import math
import pandas as pd

GROUPS = ("unknown", "property_damage", "other_injury", "serious_injury", "fatal")
DEFAULT_BONUS = dict(zip(GROUPS, (0.0, 0.0, 0.25, 1.0, 1.5)))
DEFAULT_NARRATIVE_WEIGHT = dict(zip(GROUPS, (1.0, 0.5, 0.75, 1.0, 1.0)))


def code_key(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().casefold()
    # Numeric SQL columns often arrive as floats. Do not reinterpret arbitrary strings.
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def severity_by_mfn(frame, config) -> dict[str, str]:
    if frame is None or config is None:
        return {}
    cfg = config.raw.get("review_priority", {})
    field = cfg.get("severity_field", "")
    if not field or field not in frame.columns:
        return {}
    mapping = {}
    for group, codes in cfg.get("severity_codes", {}).items():
        if group not in GROUPS:
            raise ValueError("Unknown crash severity group in review_priority configuration.")
        for value in codes:
            key = code_key(value)
            if not key or key in mapping:
                raise ValueError("Crash severity mappings must have unique, nonblank codes.")
            mapping[key] = group
    mfn = config.raw["fields"]["normalized_mfn_field"]
    groups = frame[field].map(lambda v: mapping.get(code_key(v), "unknown"))
    out = {}
    # On duplicate rows, retain the most severe mapped value; do not silently lower severity.
    for key, group in zip(frame[mfn].astype(str), groups):
        previous = out.get(key, "unknown")
        out[key] = max((previous, group), key=GROUPS.index)
    return out


def priority_settings(config, group: str) -> tuple[float, float]:
    cfg = config.raw.get("review_priority", {}) if config else {}
    bonus = float(cfg.get("narrative_completeness_bonus", {}).get(group, DEFAULT_BONUS[group]))
    weight = float(cfg.get("narrative_priority_weight", {}).get(group, DEFAULT_NARRATIVE_WEIGHT[group]))
    if not math.isfinite(bonus) or not 0 <= bonus <= 2:
        raise ValueError("Narrative completeness bonus must be between 0 and 2.")
    if not math.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError("Narrative priority weight must be between 0 and 1.")
    return bonus, weight
