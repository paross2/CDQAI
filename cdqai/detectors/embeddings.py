from __future__ import annotations
import json, logging
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from cdqai.core.config import CDQAIConfig
class NarrativeEmbeddingManager:
    def __init__(self, config: CDQAIConfig, logger: logging.Logger) -> None: self.config=config; self.logger=logger
    def load_cached_embeddings(self, expected_mfns: list[str]) -> np.ndarray | None:
        ep=self.config.narrative_embeddings_path; ip=self.config.narrative_embedding_index_path
        if not ep.exists() or not ip.exists(): self.logger.info("Narrative embedding cache not found."); return None
        try:
            cached=json.loads(ip.read_text(encoding="utf-8")).get("mfns", [])
            if cached != expected_mfns: self.logger.info("Narrative embedding cache exists but MFN index does not match current data."); return None
            self.logger.info("Loading narrative embeddings from cache: %s", ep); return np.load(ep)
        except Exception as exc: self.logger.warning("Unable to load narrative embedding cache: %s", exc); return None
    def write_cached_embeddings(self, embeddings: np.ndarray, mfns: list[str]) -> None:
        ep=self.config.narrative_embeddings_path; ip=self.config.narrative_embedding_index_path; ep.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info("Writing narrative embeddings cache: %s", ep); np.save(ep, embeddings)
        ip.write_text(json.dumps({"mfns": mfns, "embedding_shape": list(embeddings.shape)}, indent=2), encoding="utf-8")
    def get_embeddings(self, df: pd.DataFrame, refresh_cache: bool=False) -> np.ndarray:
        fields=self.config.raw["fields"]; mfn=fields["normalized_mfn_field"]; narrative_text=fields["narrative_text_field"]
        cfg=self.config.raw["models"]["narrative"]; model_name=cfg.get("embedding_model","sentence-transformers/all-MiniLM-L6-v2"); batch_size=int(cfg.get("batch_size",256))
        mfns=df[mfn].astype(str).tolist()
        if self.config.use_cache and not refresh_cache:
            cached=self.load_cached_embeddings(mfns)
            if cached is not None: return cached
        self.logger.info("Loading embedding model: %s", model_name); embedder=SentenceTransformer(model_name)
        narratives=df[narrative_text].fillna("").astype(str).tolist(); self.logger.info("Generating narrative embeddings for %s records.", f"{len(narratives):,}")
        embeddings=embedder.encode(narratives,batch_size=batch_size,show_progress_bar=True,convert_to_numpy=True)
        if self.config.write_cache: self.write_cached_embeddings(embeddings, mfns)
        return embeddings
