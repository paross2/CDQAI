from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from cdqai.core.config import CDQAIConfig
from cdqai.evidence.objects import Evidence


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    evidence: list[Evidence]

    @property
    def count(self) -> int:
        return len(self.evidence)


class BaseRule(ABC):
    """Base class for deterministic Kentucky data quality rules."""

    rule_id: str = "base_rule"
    name: str = "Base Rule"
    description: str = ""

    def is_enabled(self, config: CDQAIConfig) -> bool:
        return True

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, config: CDQAIConfig) -> RuleResult:
        """Evaluate the rule against a merged crash dataset."""
        raise NotImplementedError
