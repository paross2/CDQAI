from cdqai.kentucky.mapping import systems_for_record
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem


def test_rec01_maps_to_crash_and_roadway():
    systems = systems_for_record(RecordType.REC01)
    assert TrafficRecordSystem.CRASH in systems
    assert TrafficRecordSystem.ROADWAY in systems
