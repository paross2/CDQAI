from __future__ import annotations

from dataclasses import dataclass, field

from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity


@dataclass
class EvidenceBundle:
    mfn: str
    evidence: list[Evidence] = field(default_factory=list)

    def add(self, item: Evidence) -> None:
        if item.mfn != self.mfn:
            raise ValueError("Evidence MFN does not match bundle MFN.")
        self.evidence.append(item)

    @property
    def count(self) -> int:
        return len(self.evidence)

    @property
    def max_severity(self) -> Severity | None:
        if not self.evidence:
            return None
        return max((item.severity for item in self.evidence), default=None)

    @property
    def max_confidence(self) -> float:
        if not self.evidence:
            return 0.0
        return max(item.confidence for item in self.evidence)

    @property
    def categories(self) -> list[str]:
        return sorted({item.category for item in self.evidence})

    def to_rows(self) -> list[dict]:
        return [item.to_dict() for item in self.evidence]
