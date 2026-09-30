# CDQAI file version: 2.3.5
from __future__ import annotations
from dataclasses import dataclass
from cdqai.evidence.objects import Evidence
from cdqai.findings.decision_support import (
    analyst_priority, confidence_score, evidence_agreement, evidence_strength, recommended_action,
    ranking_evidence,
)

@dataclass(frozen=True)
class Finding:
    mfn: str
    finding_type: str
    primary_issue: str
    priority_score: float
    priority_level: str
    evidence: tuple[Evidence, ...]
    explanation: str
    actionable: bool
    crash_severity: str = "unknown"
    narrative_priority_weight: float = 1.0
    completeness_bonus: float = 0.0
    priority_rationale: str = ""
    review_facts: tuple[dict, ...] = ()
    llm_guidance: str = ""
    llm_status: str = "Disabled"
    llm_model: str = ""

    def to_dict(self) -> dict:
        ranked = ranking_evidence(self.evidence)
        severest = max(ranked, key=lambda x: int(x.severity))
        strength = evidence_strength(self.evidence)
        return {
            "MFN": self.mfn, "FindingType": self.finding_type, "PrimaryIssue": self.primary_issue,
            "IssueCategories": "; ".join(sorted({x.category for x in self.evidence})),
            "PriorityScore": round(self.priority_score, 3), "PriorityLevel": self.priority_level,
            "Severity": severest.severity_label, "Confidence": round(max(x.confidence for x in ranked), 4),
            "ConfidenceScore": confidence_score(self.evidence),
            "EvidenceAgreement": evidence_agreement(self.evidence),
            "EvidenceStrength": strength,
            "AnalystPriority": analyst_priority(self.priority_level, strength, self.actionable),
            "RecommendedAction": recommended_action(self.evidence, self.actionable),
            "EvidenceCount": len(self.evidence), "RuleIDs": "; ".join(sorted({x.source for x in self.evidence})),
            "TrafficRecordSystems": "; ".join(sorted({x.traffic_record_system.value for x in self.evidence})),
            "RecordTypes": "; ".join(sorted({x.record_type.value for x in self.evidence})),
            "QualityCharacteristics": "; ".join(sorted({x.quality_characteristic.value for x in self.evidence})),
            "Explanation": self.explanation, "ReviewStatus": "Not Reviewed",
            "CrashSeverityGroup": self.crash_severity,
            "NarrativePriorityWeight": self.narrative_priority_weight,
            "NarrativeCompletenessBonus": self.completeness_bonus,
            "PriorityRationale": self.priority_rationale,
            "ReviewFacts": self.review_facts,
            "LLMGuidance": self.llm_guidance, "LLMStatus": self.llm_status,
            "LLMModel": self.llm_model,
        }
