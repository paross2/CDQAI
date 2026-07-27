from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import pandas as pd

from cdqai.evidence.bundle import EvidenceBundle
from cdqai.evidence.objects import Evidence


@dataclass
class EvidenceCollection:
    items: list[Evidence]

    def by_mfn(self) -> dict[str, EvidenceBundle]:
        bundles: dict[str, EvidenceBundle] = {}

        for item in self.items:
            if item.mfn not in bundles:
                bundles[item.mfn] = EvidenceBundle(mfn=item.mfn)
            bundles[item.mfn].add(item)

        return bundles

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([item.to_dict() for item in self.items])

    def summary_dataframe(self) -> pd.DataFrame:
        rows = []
        grouped: dict[tuple[str, str, str], int] = defaultdict(int)

        for item in self.items:
            key = (
                item.record_type.value,
                item.traffic_record_system.value,
                item.quality_characteristic.value,
            )
            grouped[key] += 1

        for (record_type, system, quality), count in grouped.items():
            rows.append(
                {
                    "RecordType": record_type,
                    "TrafficRecordSystem": system,
                    "QualityCharacteristic": quality,
                    "EvidenceCount": count,
                }
            )

        return pd.DataFrame(rows).sort_values(
            ["RecordType", "TrafficRecordSystem", "QualityCharacteristic"]
        ) if rows else pd.DataFrame(
            columns=["RecordType", "TrafficRecordSystem", "QualityCharacteristic", "EvidenceCount"]
        )
