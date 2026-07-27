from __future__ import annotations

import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.systems import TrafficRecordSystem
from cdqai.rules.base import BaseRule, RuleResult


class MissingNarrativeRule(BaseRule):
    rule_id = "KY_REC01_MISSING_NARRATIVE"
    name = "Missing crash narrative"
    description = "Flags Rec01 records with missing narrative text."

    def is_enabled(self, config: CDQAIConfig) -> bool:
        return bool(config.raw.get("rules", {}).get("missing_narrative", {}).get("enabled", True))

    def evaluate(self, df: pd.DataFrame, config: CDQAIConfig) -> RuleResult:
        mfn = config.raw["fields"]["normalized_mfn_field"]
        narrative = config.raw["fields"]["narrative_text_field"]

        if narrative not in df.columns:
            return RuleResult(rule_id=self.rule_id, evidence=[])

        text = df[narrative].fillna("").astype(str).str.strip()
        missing = df[text == ""]

        evidence = [
            Evidence(
                mfn=str(row[mfn]),
                record_type=RecordType.REC01,
                traffic_record_system=TrafficRecordSystem.CRASH,
                quality_characteristic=QualityCharacteristic.COMPLETENESS,
                category="Missing Narrative",
                severity=Severity.MEDIUM,
                confidence=1.0,
                message="Crash record is missing narrative text.",
                source=self.rule_id,
                supporting_fields=[narrative],
                supporting_values={narrative: ""},
            )
            for _, row in missing.iterrows()
        ]

        return RuleResult(rule_id=self.rule_id, evidence=evidence)


class SparseNarrativeRule(BaseRule):
    rule_id = "KY_REC01_SPARSE_NARRATIVE"
    name = "Sparse crash narrative"
    description = "Flags Rec01 records with very short narrative text."

    def is_enabled(self, config: CDQAIConfig) -> bool:
        return bool(config.raw.get("rules", {}).get("sparse_narrative", {}).get("enabled", True))

    def evaluate(self, df: pd.DataFrame, config: CDQAIConfig) -> RuleResult:
        mfn = config.raw["fields"]["normalized_mfn_field"]
        narrative = config.raw["fields"]["narrative_text_field"]
        min_len = int(config.raw.get("rules", {}).get("sparse_narrative", {}).get("minimum_length", 40))

        if narrative not in df.columns:
            return RuleResult(rule_id=self.rule_id, evidence=[])

        text = df[narrative].fillna("").astype(str).str.strip()
        sparse = df[(text != "") & (text.str.len() < min_len)]

        evidence = [
            Evidence(
                mfn=str(row[mfn]),
                record_type=RecordType.REC01,
                traffic_record_system=TrafficRecordSystem.CRASH,
                quality_characteristic=QualityCharacteristic.COMPLETENESS,
                category="Sparse Narrative",
                severity=Severity.LOW,
                confidence=0.90,
                message=f"Crash narrative is shorter than {min_len} characters.",
                source=self.rule_id,
                supporting_fields=[narrative],
                supporting_values={narrative: str(row[narrative])[:200]},
            )
            for _, row in sparse.iterrows()
        ]

        return RuleResult(rule_id=self.rule_id, evidence=evidence)
