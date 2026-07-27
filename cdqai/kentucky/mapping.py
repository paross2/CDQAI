from __future__ import annotations

from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem


RECORD_SYSTEM_MAP: dict[RecordType, tuple[TrafficRecordSystem, ...]] = {
    RecordType.REC01: (
        TrafficRecordSystem.CRASH,
        TrafficRecordSystem.ROADWAY,
    ),
    RecordType.REC02: (
        TrafficRecordSystem.VEHICLE,
    ),
    RecordType.REC03: (
        TrafficRecordSystem.DRIVER,
    ),
}


def systems_for_record(record_type: RecordType) -> tuple[TrafficRecordSystem, ...]:
    return RECORD_SYSTEM_MAP[record_type]
