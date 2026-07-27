from __future__ import annotations

import re

import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem
from cdqai.rules.base import BaseRule, RuleResult


INJURY_SIGNAL_RE = re.compile(
    r"\b(?:"
    r"injur(?:y|ed|ies)?|"
    r"hurt|pain|"
    r"hospital|"
    r"ems|ambulance|"
    r"transport(?:ed)?|"
    r"airlift(?:ed)?|"
    r"fatal(?:ity)?|"
    r"killed|dead|deceased"
    r")\b",
    flags=re.IGNORECASE,
)


class NarrativeInjuryConflictRule(BaseRule):
    rule_id = "KY_REC01_NARRATIVE_INJURY_CONFLICT"
    name = "Narrative injury signal conflicts with coded no-injury value"
    description = "Flags records where the narrative suggests injury/EMS/hospital/fatality but a candidate injury field indicates no injury."

    def is_enabled(self, config: CDQAIConfig) -> bool:
        return bool(config.raw.get("rules", {}).get("injury_conflict", {}).get("enabled", True))

    def evaluate(self, df: pd.DataFrame, config: CDQAIConfig) -> RuleResult:
        mfn = config.raw["fields"]["normalized_mfn_field"]
        narrative = config.raw["fields"]["narrative_text_field"]
        rule_config = config.raw.get("rules", {}).get("injury_conflict", {})

        candidate_fields = list(rule_config.get("injury_field_candidates", []))
        no_injury_values = {
            str(value).strip().lower()
            for value in rule_config.get("no_injury_values", [])
        }

        if narrative not in df.columns:
            return RuleResult(rule_id=self.rule_id, evidence=[])

        available_fields = [field for field in candidate_fields if field in df.columns]

        if not available_fields:
            return RuleResult(rule_id=self.rule_id, evidence=[])

        narrative_text = df[narrative].fillna("").astype(str)
        has_injury_signal = narrative_text.str.contains(INJURY_SIGNAL_RE, regex=True, na=False)

        evidence: list[Evidence] = []

        for field in available_fields:
            coded_values = df[field].fillna("").astype(str).str.strip().str.lower()
            coded_no_injury = coded_values.isin(no_injury_values)
            conflict_rows = df[has_injury_signal & coded_no_injury]

            for _, row in conflict_rows.iterrows():
                evidence.append(
                    Evidence(
                        mfn=str(row[mfn]),
                        record_type=RecordType.REC01,
                        traffic_record_system=TrafficRecordSystem.CRASH,
                        quality_characteristic=QualityCharacteristic.ACCURACY,
                        category="Narrative Injury Conflict",
                        severity=Severity.HIGH,
                        confidence=0.90,
                        message=(
                            "Narrative contains injury, EMS, hospital, or fatality language, "
                            f"but field '{field}' appears to indicate no injury."
                        ),
                        source=self.rule_id,
                        supporting_fields=[narrative, field],
                        supporting_values={
                            narrative: str(row[narrative])[:500],
                            field: row[field],
                        },
                    )
                )

        return RuleResult(rule_id=self.rule_id, evidence=evidence)
