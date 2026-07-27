from __future__ import annotations
from dataclasses import dataclass
from cdqai.evidence.engine import EvidenceCollection
from cdqai.findings.finding import Finding
from cdqai.findings.priority import priority_level, score_evidence

COMPLETENESS_ONLY = {"Missing Narrative", "Sparse Narrative"}
MODEL_CATEGORIES = {"Structured Anomaly", "Narrative Anomaly", "Ensemble Anomaly", "Multi-Model Anomaly"}

@dataclass
class FindingEngine:
    def run(self, evidence: EvidenceCollection) -> list[Finding]:
        findings: list[Finding] = []
        for mfn, bundle in evidence.by_mfn().items():
            items = bundle.evidence
            categories = {x.category for x in items}
            sources = {x.source for x in items}
            actionable = not categories.issubset(COMPLETENESS_ONLY)
            if "Multi-Model Anomaly" in categories or len(sources) >= 2:
                kind = "Multi-Signal"
            elif categories & MODEL_CATEGORIES:
                kind = "Anomaly"
            elif any("Conflict" in c for c in categories):
                kind = "Consistency"
            else:
                kind = "Validation"
            primary = max(items, key=lambda x: (int(x.severity), x.confidence)).category
            score = score_evidence(items)
            messages = " ".join(dict.fromkeys(x.message for x in items))
            findings.append(Finding(mfn, kind, primary, score, priority_level(score), tuple(items),
                f"CDQAI identified {len(items)} evidence signal(s). {messages}", actionable))
        return sorted(findings, key=lambda x: (-x.priority_score, x.mfn))
