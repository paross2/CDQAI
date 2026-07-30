from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer

from cdqai.core.config import CDQAIConfig
from cdqai.features.field_roles import classify_field


def percentile_rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(pct=True).to_numpy() * 100.0


class StructuredAnomalyDetector:
    def __init__(self, config: CDQAIConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self.feature_columns: list[str] = []
        self.excluded_columns: dict[str, str] = {}
        self.field_roles: dict[str, str] = {}

    def select_features(self, df: pd.DataFrame) -> list[str]:
        cfg = self.config.raw["models"]["structured"]
        mfn = self.config.raw["fields"]["normalized_mfn_field"]
        narrative = self.config.raw["fields"]["narrative_text_field"]
        selected: list[str] = []
        self.excluded_columns = {}
        self.field_roles = {}

        for column in df.columns:
            decision = classify_field(column, df[column], cfg, mfn, narrative)
            self.field_roles[str(column)] = decision.role
            if decision.eligible:
                selected.append(str(column))
            else:
                self.excluded_columns[str(column)] = decision.reason

        # Version 2.2.1 deliberately does not truncate by database schema order.
        # Administrators can use include_fields for a reviewed, deterministic feature list.
        return selected

    @staticmethod
    def _prepare_features(df: pd.DataFrame, columns: list[str]) -> np.ndarray:
        x = df[columns].replace([np.inf, -np.inf], np.nan)
        # Median imputation avoids manufacturing zero-valued outliers for continuous fields.
        # Binary fields retain their ordinary 0/1 center under median imputation.
        return SimpleImputer(strategy="median").fit_transform(x)

    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        cfg = self.config.raw["models"]["structured"]
        mfn = self.config.raw["fields"]["normalized_mfn_field"]
        numeric_cols = self.select_features(df)
        self.feature_columns = numeric_cols
        if not numeric_cols:
            raise ValueError("No approved numeric columns are available for structured anomaly detection.")

        self.logger.info("Structured model fields used (%s): %s", len(numeric_cols), ", ".join(numeric_cols))
        if self.excluded_columns:
            self.logger.info(
                "Structured model fields excluded (%s): %s",
                len(self.excluded_columns),
                "; ".join(f"{name} [{reason}]" for name, reason in self.excluded_columns.items()),
            )

        x = self._prepare_features(df, numeric_cols)
        model = IsolationForest(
            contamination=float(cfg.get("contamination", 0.02)),
            random_state=int(cfg.get("random_state", 42)),
            n_jobs=-1,
        )
        raw = -model.fit(x).decision_function(x)
        pct = percentile_rank(raw)
        return pd.DataFrame({mfn: df[mfn].to_numpy(), "StructuredScore": raw, "StructuredScore_pct": pct})
