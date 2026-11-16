# CDQAI file version: 2.5.1
from cdqai.kentucky.mapping import systems_for_record
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem


def test_crash_record_maps_to_crash_and_roadway():
    systems = systems_for_record(RecordType.CRASH)
    assert TrafficRecordSystem.CRASH in systems
    assert TrafficRecordSystem.ROADWAY in systems
