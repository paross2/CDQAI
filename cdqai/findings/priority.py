from __future__ import annotations
from cdqai.evidence.objects import Evidence

def score_evidence(items: list[Evidence]) -> float:
    severity = max(int(x.severity) for x in items)
    confidence = max(x.confidence for x in items)
    diversity = len({x.source for x in items})
    multi_bonus = 2.0 if diversity >= 2 else 0.0
    return severity * 2.0 + confidence * 2.0 + min(diversity - 1, 3) * 0.75 + multi_bonus

def priority_level(score: float) -> str:
    if score >= 13: return "Critical"
    if score >= 10: return "High"
    if score >= 7: return "Medium"
    return "Low"
