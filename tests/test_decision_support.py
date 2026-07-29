from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem
from cdqai.findings.decision_support import confidence_score, evidence_agreement, evidence_strength, recommended_action


def make(category, source, severity=Severity.HIGH, confidence=0.99):
    return Evidence(
        mfn="1", record_type=RecordType.REC01, traffic_record_system=TrafficRecordSystem.CRASH,
        quality_characteristic=QualityCharacteristic.ACCURACY, category=category,
        severity=severity, confidence=confidence, message="test", source=source,
        supporting_fields=(), supporting_values={},
    )


def test_multi_source_decision_support():
    items = (
        make("Structured Anomaly", "MODEL_STRUCTURED"),
        make("Narrative Anomaly", "MODEL_NARRATIVE"),
        make("Ensemble Anomaly", "MODEL_ENSEMBLE", Severity.CRITICAL, 1.0),
    )
    assert evidence_agreement(items) == "Ensemble Model + Narrative Model + Structured Model"
    assert evidence_strength(items) == "Very Strong"
    assert confidence_score(items) == 86.0
    assert "multiple independent signals" in recommended_action(items, True)
