from __future__ import annotations

import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem
from cdqai.rules.base import BaseRule, RuleResult


class RequiredFieldCompletenessRule(BaseRule):
    rule_id = "KY_REQUIRED_FIELD_COMPLETENESS"
    name = "Required field completeness"
    description = "Flags records where configured required fields are blank."

    def is_enabled(self, config: CDQAIConfig) -> bool:
        return bool(config.raw.get("rules", {}).get("required_fields", {}).get("enabled", True))

    def evaluate(self, df: pd.DataFrame, config: CDQAIConfig) -> RuleResult:
        rule_config = config.raw.get("rules", {}).get("required_fields", {})
        required_fields = list(rule_config.get("rec01", []))

        if not required_fields:
            return RuleResult(rule_id=self.rule_id, evidence=[])

        mfn = config.raw["fields"]["normalized_mfn_field"]
        evidence: list[Evidence] = []

        for field in required_fields:
            if field not in df.columns:
                continue

            missing_mask = df[field].isna() | (df[field].astype(str).str.strip() == "")
            missing_rows = df[missing_mask]

            for _, row in missing_rows.iterrows():
                evidence.append(
                    Evidence(
                        mfn=str(row[mfn]),
                        record_type=RecordType.REC01,
                        traffic_record_system=TrafficRecordSystem.CRASH,
                        quality_characteristic=QualityCharacteristic.COMPLETENESS,
                        category="Missing Required Field",
                        severity=Severity.HIGH,
                        confidence=1.0,
                        message=f"Required field '{field}' is missing or blank.",
                        source=self.rule_id,
                        supporting_fields=[field],
                        supporting_values={field: None},
                    )
                )

        return RuleResult(rule_id=self.rule_id, evidence=evidence)
