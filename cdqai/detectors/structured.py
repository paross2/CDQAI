from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from cdqai.core.config import CDQAIConfig

def percentile_rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(pct=True).to_numpy() * 100.0
class StructuredAnomalyDetector:
    def __init__(self, config: CDQAIConfig, logger: logging.Logger) -> None: self.config=config; self.logger=logger
    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        cfg=self.config.raw["models"]["structured"]; mfn=self.config.raw["fields"]["normalized_mfn_field"]
        numeric_cols=[c for c in df.select_dtypes(include=["number"]).columns if c != mfn]
        if not numeric_cols: raise ValueError("No numeric columns available for structured anomaly detection.")
        max_cols=int(cfg.get("max_numeric_columns",80))
        if len(numeric_cols)>max_cols:
            self.logger.info("Limiting structured model to first %s numeric columns out of %s.", max_cols, len(numeric_cols)); numeric_cols=numeric_cols[:max_cols]
        self.logger.info("Structured model numeric columns: %s", len(numeric_cols))
        x=df[numeric_cols].replace([np.inf,-np.inf],np.nan).fillna(0); x_scaled=RobustScaler().fit_transform(x)
        model=IsolationForest(contamination=float(cfg.get("contamination",0.02)), random_state=int(cfg.get("random_state",42)), n_jobs=-1)
        raw=-model.fit(x_scaled).decision_function(x_scaled); pct=percentile_rank(raw)
        return pd.DataFrame({mfn: df[mfn].to_numpy(), "StructuredScore": raw, "StructuredScore_pct": pct})
