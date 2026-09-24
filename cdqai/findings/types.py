# CDQAI file version: 2.2.5
from enum import StrEnum
class FindingType(StrEnum):
    VALIDATION = "Validation"
    CONSISTENCY = "Consistency"
    ANOMALY = "Anomaly"
    MULTI_SIGNAL = "Multi-Signal"
