from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cdqai.evidence.severity import Severity
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem


@dataclass(frozen=True)
class Evidence:
    mfn: str
    record_type: RecordType
    traffic_record_system: TrafficRecordSystem
    quality_characteristic: QualityCharacteristic
    category: str
    severity: Severity
    confidence: float
    message: str
    source: str
    supporting_fields: list[str] = field(default_factory=list)
    supporting_values: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Evidence confidence must be between 0.0 and 1.0.")

    @property
    def severity_label(self) -> str:
        return self.severity.label

    def to_dict(self) -> dict[str, Any]:
        return {
            "MFN": self.mfn,
            "RecordType": self.record_type.value,
            "TrafficRecordSystem": self.traffic_record_system.value,
            "QualityCharacteristic": self.quality_characteristic.value,
            "Category": self.category,
            "Severity": self.severity_label,
            "SeverityValue": int(self.severity),
            "Confidence": self.confidence,
            "Message": self.message,
            "Source": self.source,
            "SupportingFields": "; ".join(self.supporting_fields),
            "SupportingValues": self.supporting_values,
        }
