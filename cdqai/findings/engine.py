# CDQAI file version: 2.3.5
from __future__ import annotations
from dataclasses import dataclass
from cdqai.evidence.engine import EvidenceCollection
from cdqai.findings.finding import Finding
from cdqai.findings.priority import priority_level, score_evidence
from cdqai.findings.decision_support import ranking_evidence
from cdqai.findings.severity_context import severity_by_mfn, priority_settings

COMPLETENESS_ONLY = {"Missing Narrative", "Sparse Narrative"}
MODEL_CATEGORIES = {"Structured Anomaly", "Narrative Anomaly", "Ensemble Anomaly", "Multi-Model Anomaly"}

@dataclass
class FindingEngine:
    def run(self, evidence: EvidenceCollection, dataset=None, config=None) -> list[Finding]:
        findings: list[Finding] = []
        severity = severity_by_mfn(dataset.merged if dataset is not None else None, config)
        for mfn, bundle in evidence.by_mfn().items():
            items = bundle.evidence
            categories = {x.category for x in items}
            sources = {x.source for x in ranking_evidence(items)}
            actionable = not categories.issubset(COMPLETENESS_ONLY)
            if "Multi-Model Anomaly" in categories or len(sources) >= 2:
                kind = "Multi-Signal"
            elif categories & MODEL_CATEGORIES:
                kind = "Anomaly"
            elif any("Conflict" in c for c in categories):
                kind = "Consistency"
            else:
                kind = "Validation"
            primary = max(ranking_evidence(items), key=lambda x: (int(x.severity), x.confidence)).category
            group = severity.get(mfn, "unknown")
            bonus, weight = priority_settings(config, group)
            bonus = bonus if categories & COMPLETENESS_ONLY else 0.0
            score = (score_evidence(items, narrative_weight=weight) if actionable else 0.0) + bonus
            rationale = (f"Crash severity: {group}. Narrative model priority multiplier: {weight:g}; "
                         f"narrative completeness adjustment: +{bonus:g}. "
                         "Completeness does not boost model agreement; derived model summaries are not counted again.")
            messages = " ".join(dict.fromkeys(x.message for x in items))
            findings.append(Finding(mfn, kind, primary, score, priority_level(score), tuple(items),
                f"CDQAI identified {len(items)} evidence signal(s). {messages}", actionable,
                crash_severity=group, narrative_priority_weight=weight,
                completeness_bonus=bonus, priority_rationale=rationale))
        return sorted(findings, key=lambda x: (-x.priority_score, x.mfn))
