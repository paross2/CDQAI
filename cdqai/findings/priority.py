# CDQAI file version: 2.3.6
from __future__ import annotations
from cdqai.evidence.objects import Evidence
from cdqai.findings.decision_support import ranking_evidence

def score_evidence(items: list[Evidence], narrative_weight: float = 1.0) -> float:
    items = ranking_evidence(items)
    def weight(item):
        return narrative_weight if item.source == "MODEL_NARRATIVE" else 1.0
    items = [item for item in items if weight(item) > 0]
    if not items:
        return 0.0
    severity = max(int(x.severity) * weight(x) for x in items)
    confidence = max(x.confidence * weight(x) for x in items)
    diversity = len({x.source for x in items})
    multi_bonus = 2.0 if diversity >= 2 else 0.0
    return severity * 2.0 + confidence * 2.0 + min(diversity - 1, 3) * 0.75 + multi_bonus

def priority_level(score: float) -> str:
    if score >= 13: return "Critical"
    if score >= 10: return "High"
    if score >= 7: return "Medium"
    return "Low"
