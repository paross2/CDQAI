# CDQAI file version: 2.3.6
from __future__ import annotations
import hashlib
import importlib.metadata
import json
import os
import tempfile
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from cdqai.detectors.narrative_chunks import ALGORITHM, FullNarrativeEncoder


class NarrativeEmbeddingManager:
    def __init__(self, config, logger):
        self.config, self.logger = config, logger
        self.coverage = []
        self._encoder = None

    def encoder(self):
        if self._encoder is None:
            cfg = self.config.raw["models"]["narrative"]
            try:
                model = SentenceTransformer(cfg.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"), local_files_only=True)
            except OSError:
                raise RuntimeError("Embedding model unavailable locally. Install model assets before running CDQAI.") from None
            self._encoder = FullNarrativeEncoder(model, cfg.get("chunk_overlap_tokens", 32), cfg.get("batch_size", 256))
        return self._encoder

    def encode_review_texts(self, texts):
        return self.encoder().encode(texts)[0]

    def fingerprint(self):
        encoder = self.encoder()
        digest = hashlib.sha256()
        for name, tensor in encoder.embedder.state_dict().items():
            digest.update(name.encode("utf-8"))
            digest.update(str((tuple(tensor.shape), tensor.dtype)).encode())
            digest.update(tensor.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
        return {"algorithm": ALGORITHM, "model_weights": digest.hexdigest(),
                "model": self.config.raw["models"]["narrative"].get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
                "tokenizer": hashlib.sha256(encoder.tokenizer.backend_tokenizer.to_str().encode()).hexdigest(),
                "max_tokens": encoder.limit, "overlap_tokens": encoder.overlap,
                "model_config": str(encoder.embedder),
                "packages": {p: importlib.metadata.version(p) for p in
                             ("sentence-transformers", "transformers", "torch", "tokenizers")}}

    def load_cached_embeddings(self, identity):
        ep, ip = self.config.narrative_embeddings_path, self.config.narrative_embedding_index_path
        if not ep.is_file() or not ip.is_file():
            return None
        try:
            metadata = json.loads(ip.read_text(encoding="utf-8"))
            if metadata.get("identity") != identity:
                self.logger.info("Narrative cache is from different text, model, or chunk settings; rebuilding.")
                return None
            values = np.load(ep, allow_pickle=False)
            coverage = metadata["coverage"]
            if (values.ndim != 2 or len(values) != len(identity["rows"]) or not np.isfinite(values).all()
                    or list(values.shape) != metadata["shape"] or len(coverage) != len(values)
                    or hashlib.sha256(values.tobytes()).hexdigest() != metadata["embedding_sha256"]
                    or [c["narrative_sha256"] for c in coverage] != [r[1] for r in identity["rows"]]):
                return None
            self.coverage = coverage
            return values
        except (OSError, ValueError, KeyError, TypeError, EOFError):
            self.logger.warning("Narrative cache invalid; rebuilding without logging private content.")
            return None

    def write_cached_embeddings(self, values, identity):
        ep, ip = self.config.narrative_embeddings_path, self.config.narrative_embedding_index_path
        ep.parent.mkdir(parents=True, exist_ok=True)
        ip.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"identity": identity, "shape": list(values.shape), "coverage": self.coverage,
                    "embedding_sha256": hashlib.sha256(values.tobytes()).hexdigest()}
        staged = []
        try:
            with tempfile.NamedTemporaryFile(dir=ep.parent, delete=False) as handle:
                staged.append(handle.name)
                np.save(handle, values, allow_pickle=False)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ip.parent, delete=False) as handle:
                staged.append(handle.name)
                json.dump(metadata, handle)
            os.replace(staged[0], ep)
            os.replace(staged[1], ip)
        finally:
            for path in staged:
                if os.path.exists(path):
                    os.unlink(path)

    def get_embeddings(self, df, refresh_cache=False):
        fields = self.config.raw["fields"]
        texts = df[fields["narrative_text_field"]].fillna("").astype(str).tolist()
        mfns = df[fields["normalized_mfn_field"]].astype(str).tolist()
        identity = {"encoder": self.fingerprint(), "rows":
                    [[mfn, hashlib.sha256(text.encode("utf-8")).hexdigest()] for mfn, text in zip(mfns, texts)]}
        if self.config.use_cache and not refresh_cache:
            cached = self.load_cached_embeddings(identity)
            if cached is not None:
                return cached
        self.logger.info("Encoding complete narratives for %s rows with token-budgeted chunks.", len(texts))
        values, self.coverage = self.encoder().encode(texts)
        self.logger.info("Full-narrative encoding completed: %s chunks.", sum(c["chunks"] for c in self.coverage))
        if self.config.write_cache:
            self.write_cached_embeddings(values, identity)
        return values
