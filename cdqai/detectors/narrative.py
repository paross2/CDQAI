from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from cdqai.core.config import CDQAIConfig
from cdqai.detectors.embeddings import NarrativeEmbeddingManager
from cdqai.detectors.structured import percentile_rank


class NarrativeAnomalyDetector:
    """Score only records that contain usable narrative text."""

    def __init__(self, config: CDQAIConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self.embedding_manager = NarrativeEmbeddingManager(config, logger)

    def score(self, df: pd.DataFrame, refresh_cache: bool = False) -> pd.DataFrame:
        cfg = self.config.raw["models"]["narrative"]
        fields = self.config.raw["fields"]
        mfn = fields["normalized_mfn_field"]
        narrative_text = fields["narrative_text_field"]

        text = df[narrative_text].fillna("").astype(str).str.strip()
        valid_mask = text.ne("")
        valid_df = df.loc[valid_mask].copy()

        results = pd.DataFrame(
            {
                mfn: df[mfn].astype(str).to_numpy(),
                "NarrativeScore": np.nan,
                "NarrativeScore_pct": np.nan,
                "NarrativeAvailable": valid_mask.to_numpy(dtype=bool),
            }
        )

        valid_count = int(valid_mask.sum())
        missing_count = int((~valid_mask).sum())
        self.logger.info(
            "Narrative scoring eligibility: %s usable narratives; %s blank or missing narratives excluded.",
            f"{valid_count:,}",
            f"{missing_count:,}",
        )

        if valid_count < 2:
            self.logger.warning(
                "Narrative anomaly scoring skipped because fewer than two usable narratives were available."
            )
            return results

        embeddings = self.embedding_manager.get_embeddings(
            valid_df, refresh_cache=refresh_cache
        )
        self.logger.info("Running narrative Isolation Forest on usable embeddings.")
        model = IsolationForest(
            contamination=float(cfg.get("contamination", 0.02)),
            random_state=int(cfg.get("random_state", 42)),
            n_jobs=-1,
        )
        raw = -model.fit(embeddings).decision_function(embeddings)
        pct = percentile_rank(raw)

        valid_scores = pd.DataFrame(
            {
                mfn: valid_df[mfn].astype(str).to_numpy(),
                "NarrativeScore": raw,
                "NarrativeScore_pct": pct,
            }
        )
        results = results.drop(columns=["NarrativeScore", "NarrativeScore_pct"]).merge(
            valid_scores, on=mfn, how="left"
        )
        return results
