# CDQAI file version: 2.5.1
from __future__ import annotations

from enum import StrEnum


class RecordType(StrEnum):
    CRASH = "Crash"
    VEHICLE = "Vehicle"
    PERSON = "Person"
