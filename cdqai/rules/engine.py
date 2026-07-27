from __future__ import annotations

import logging
from dataclasses import dataclass, field

from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset
from cdqai.evidence.engine import EvidenceCollection
from cdqai.evidence.objects import Evidence
from cdqai.rules.base import BaseRule
from cdqai.rules.completeness import RequiredFieldCompletenessRule
from cdqai.rules.injury import NarrativeInjuryConflictRule
from cdqai.rules.narrative_quality import MissingNarrativeRule, SparseNarrativeRule


DEFAULT_RULES: tuple[type[BaseRule], ...] = (
    MissingNarrativeRule,
    SparseNarrativeRule,
    RequiredFieldCompletenessRule,
    NarrativeInjuryConflictRule,
)


@dataclass
class RuleEngine:
    config: CDQAIConfig
    logger: logging.Logger
    rule_classes: tuple[type[BaseRule], ...] = field(default_factory=lambda: DEFAULT_RULES)

    def run(self, dataset: CrashDataset) -> EvidenceCollection:
        all_evidence: list[Evidence] = []

        self.logger.info("Running Kentucky Rule Engine with %s rules.", len(self.rule_classes))

        for rule_class in self.rule_classes:
            rule = rule_class()

            if not rule.is_enabled(self.config):
                self.logger.info("Skipping disabled rule: %s", rule.rule_id)
                continue

            self.logger.info("Evaluating rule: %s — %s", rule.rule_id, rule.name)
            result = rule.evaluate(dataset.merged, self.config)
            self.logger.info("Rule %s generated %s evidence item(s).", result.rule_id, f"{result.count:,}")
            all_evidence.extend(result.evidence)

        self.logger.info("Kentucky Rule Engine generated %s total evidence item(s).", f"{len(all_evidence):,}")
        return EvidenceCollection(items=all_evidence)
