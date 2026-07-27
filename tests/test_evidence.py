import pytest

from cdqai.evidence import Evidence, EvidenceBundle, Severity
from cdqai.kentucky import QualityCharacteristic, RecordType, TrafficRecordSystem


def test_evidence_confidence_range():
    evidence = Evidence(
        mfn="123",
        record_type=RecordType.REC01,
        traffic_record_system=TrafficRecordSystem.CRASH,
        quality_characteristic=QualityCharacteristic.ACCURACY,
        category="Test Finding",
        severity=Severity.HIGH,
        confidence=0.95,
        message="Test message.",
        source="unit-test",
    )
    assert evidence.severity_label == "High"


def test_evidence_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        Evidence(
            mfn="123",
            record_type=RecordType.REC01,
            traffic_record_system=TrafficRecordSystem.CRASH,
            quality_characteristic=QualityCharacteristic.ACCURACY,
            category="Test Finding",
            severity=Severity.HIGH,
            confidence=1.5,
            message="Test message.",
            source="unit-test",
        )


def test_evidence_bundle_adds_matching_mfn():
    evidence = Evidence(
        mfn="123",
        record_type=RecordType.REC01,
        traffic_record_system=TrafficRecordSystem.CRASH,
        quality_characteristic=QualityCharacteristic.ACCURACY,
        category="Test Finding",
        severity=Severity.HIGH,
        confidence=0.95,
        message="Test message.",
        source="unit-test",
    )
    bundle = EvidenceBundle(mfn="123")
    bundle.add(evidence)
    assert bundle.count == 1
    assert bundle.max_confidence == 0.95
