# CDQAI file version: 2.5.1
from __future__ import annotations

from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem


RECORD_SYSTEM_MAP: dict[RecordType, tuple[TrafficRecordSystem, ...]] = {
    RecordType.CRASH: (
        TrafficRecordSystem.CRASH,
        TrafficRecordSystem.ROADWAY,
    ),
    RecordType.VEHICLE: (
        TrafficRecordSystem.VEHICLE,
    ),
    RecordType.PERSON: (
        TrafficRecordSystem.DRIVER,
    ),
}


def systems_for_record(record_type: RecordType) -> tuple[TrafficRecordSystem, ...]:
    return RECORD_SYSTEM_MAP[record_type]
