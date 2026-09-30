# CDQAI file version: 2.3.1
from __future__ import annotations
import logging
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from cdqai.core.config import CDQAIConfig
from cdqai.detectors.embeddings import NarrativeEmbeddingManager
from cdqai.detectors.structured import percentile_rank
class NarrativeAnomalyDetector:
    def __init__(self, config: CDQAIConfig, logger: logging.Logger) -> None:
        self.config=config; self.logger=logger; self.embedding_manager=NarrativeEmbeddingManager(config, logger)
    def score(self, df: pd.DataFrame, refresh_cache: bool=False) -> pd.DataFrame:
        cfg=self.config.raw["models"]["narrative"]; mfn=self.config.raw["fields"]["normalized_mfn_field"]
        text_field = self.config.raw["fields"]["narrative_text_field"]
        available = df[text_field].fillna("").astype(str).str.strip().ne("").to_numpy()
        result = pd.DataFrame({mfn: df[mfn].to_numpy(), "NarrativeScore": np.nan,
                               "NarrativeScore_pct": np.nan, "NarrativeScored": False})
        if available.sum() < 2:
            self.logger.info("Narrative model skipped: fewer than two nonblank narratives.")
            return result
        # Preserve the full-row embedding-cache identity, but never fit or rank blanks.
        embeddings=self.embedding_manager.get_embeddings(df, refresh_cache=refresh_cache)
        self.logger.info("Running narrative Isolation Forest on embeddings.")
        model=IsolationForest(contamination=float(cfg.get("contamination",0.02)), random_state=int(cfg.get("random_state",42)), n_jobs=-1)
        raw=-model.fit(embeddings[available]).decision_function(embeddings[available]); pct=percentile_rank(raw)
        result.loc[available, "NarrativeScore"] = raw
        result.loc[available, "NarrativeScore_pct"] = pct
        result.loc[available, "NarrativeScored"] = True
        result["NarrativeReviewSpans"] = "[]"
        review = cfg.get("sentence_review", {})
        if review.get("enabled", False):
            from cdqai.detectors.narrative_spans import sentence_sensitivity
            limit = int(review.get("max_records", 20))
            if not 1 <= limit <= 100:
                raise ValueError("sentence_review.max_records must be between 1 and 100")
            threshold = float(self.config.raw.get("model_evidence", {}).get("narrative_percentile", 99))
            chosen = result[result.NarrativeScore_pct >= threshold].nlargest(limit, "NarrativeScore_pct")
            for idx in chosen.index:
                text = str(df.iloc[idx][text_field])
                try:
                    spans = sentence_sensitivity(text, self.embedding_manager.encode_review_texts,
                                                 model, float(result.at[idx, "NarrativeScore"]))
                except (OSError, RuntimeError, ValueError):
                    self.logger.warning("Optional sentence review unavailable; narrative scores retained.")
                    break
                result.at[idx, "NarrativeReviewSpans"] = json.dumps(spans)
        return result
