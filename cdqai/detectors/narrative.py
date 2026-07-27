from __future__ import annotations
import logging
import pandas as pd
from sklearn.ensemble import IsolationForest
from cdqai.core.config import CDQAIConfig
from cdqai.detectors.embeddings import NarrativeEmbeddingManager
from cdqai.detectors.structured import percentile_rank
class NarrativeAnomalyDetector:
    def __init__(self, config: CDQAIConfig, logger: logging.Logger) -> None:
        self.config=config; self.logger=logger; self.embedding_manager=NarrativeEmbeddingManager(config, logger)
    def score(self, df: pd.DataFrame, refresh_cache: bool=False) -> pd.DataFrame:
        cfg=self.config.raw["models"]["narrative"]; mfn=self.config.raw["fields"]["normalized_mfn_field"]
        embeddings=self.embedding_manager.get_embeddings(df, refresh_cache=refresh_cache)
        self.logger.info("Running narrative Isolation Forest on embeddings.")
        model=IsolationForest(contamination=float(cfg.get("contamination",0.02)), random_state=int(cfg.get("random_state",42)), n_jobs=-1)
        raw=-model.fit(embeddings).decision_function(embeddings); pct=percentile_rank(raw)
        return pd.DataFrame({mfn: df[mfn].to_numpy(), "NarrativeScore": raw, "NarrativeScore_pct": pct})
