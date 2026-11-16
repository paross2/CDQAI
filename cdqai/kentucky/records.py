# CDQAI file version: 2.5.0
from __future__ import annotations

from enum import StrEnum


class RecordType(StrEnum):
    CRASH = "Crash"
    VEHICLE = "Vehicle"
    PERSON = "Person"
