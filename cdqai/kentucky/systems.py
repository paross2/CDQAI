# CDQAI file version: 2.3.2
from __future__ import annotations

from enum import StrEnum


class TrafficRecordSystem(StrEnum):
    CRASH = "Crash"
    ROADWAY = "Roadway"
    VEHICLE = "Vehicle"
    DRIVER = "Driver"
