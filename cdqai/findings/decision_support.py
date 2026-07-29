from __future__ import annotations

from cdqai.evidence.objects import Evidence


def _signal_family(item: Evidence) -> str:
    category = item.category.lower()
    source = item.source.upper()
    if "structured" in category or "STRUCTURED" in source:
        return "Structured Model"
    if "narrative anomaly" in category or "NARRATIVE" in source and "SPARSE" not in source and "MISSING" not in source:
        return "Narrative Model"
    if "ensemble" in category or "ENSEMBLE" in source:
        return "Ensemble Model"
    if "multi-model" in category or "MULTI_SIGNAL" in source:
        return "Multi-Model"
    return "Rule"


def evidence_agreement(items: tuple[Evidence, ...] | list[Evidence]) -> str:
    families = sorted({_signal_family(item) for item in items})
    return " + ".join(families)


def evidence_strength(items: tuple[Evidence, ...] | list[Evidence]) -> str:
    families = {_signal_family(item) for item in items}
    max_severity = max(int(item.severity) for item in items)
    max_confidence = max(float(item.confidence) for item in items)
    deterministic = "Rule" in families
    independent = len(families)
    if (independent >= 3 and max_confidence >= 0.99) or (deterministic and independent >= 2 and max_severity >= 4):
        return "Very Strong"
    if independent >= 2 or (deterministic and max_confidence >= 0.95) or max_severity >= 4:
        return "Strong"
    if max_confidence >= 0.90 or max_severity >= 3:
        return "Moderate"
    return "Limited"


def confidence_score(items: tuple[Evidence, ...] | list[Evidence]) -> float:
    families = {_signal_family(item) for item in items}
    highest = max(float(item.confidence) for item in items) * 70.0
    agreement = min(max(len(families) - 1, 0) * 8.0, 24.0)
    deterministic = 6.0 if "Rule" in families else 0.0
    return round(min(100.0, highest + agreement + deterministic), 1)


def analyst_priority(priority_level: str, strength: str, actionable: bool) -> str:
    if not actionable:
        return "Routine Completeness Review"
    if priority_level == "Critical" or strength == "Very Strong":
        return "Immediate Review"
    if priority_level == "High" or strength == "Strong":
        return "Priority Review"
    if priority_level == "Medium":
        return "Standard Review"
    return "Review as Resources Allow"


def recommended_action(items: tuple[Evidence, ...] | list[Evidence], actionable: bool) -> str:
    categories = {item.category for item in items}
    if not actionable:
        return "Verify narrative availability and completeness; obtain or correct narrative text when required."
    if any("Conflict" in category for category in categories):
        return "Compare coded fields with the narrative and source record; resolve the apparent inconsistency."
    if "Multi-Model Anomaly" in categories or len({_signal_family(item) for item in items}) >= 3:
        return "Review the full crash record, coded variables, and narrative together because multiple independent signals agree."
    if "Structured Anomaly" in categories and "Narrative Anomaly" in categories:
        return "Review unusual coded-variable combinations alongside the narrative for corroborating or conflicting details."
    if "Structured Anomaly" in categories:
        return "Inspect the coded crash variables and compare them with source documentation and similar records."
    if "Narrative Anomaly" in categories:
        return "Read the complete narrative and verify that unusual language or events are accurately coded."
    return "Review the supporting evidence and source record, then document the analyst disposition."
