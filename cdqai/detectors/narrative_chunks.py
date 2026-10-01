# CDQAI file version: 2.3.6
"""Token-budgeted original-text spans and full-document features."""
from dataclasses import dataclass
import hashlib
import re
import numpy as np

ALGORITHM = "fulltext-weighted-mean-max-v1"


@dataclass(frozen=True)
class Chunk:
    start: int
    end: int
    weight: int


def split_narrative(text, tokenizer, budget, overlap=32):
    if budget < 2 or not 0 <= overlap < budget:
        raise ValueError("Chunk budget must exceed overlap and allow at least two tokens")
    offsets = tokenizer(text, add_special_tokens=False, truncation=False, return_offsets_mapping=True)["offset_mapping"]
    if not offsets:
        return [Chunk(0, len(text), 1)], 0
    boundaries = {m.end() for m in re.finditer(r"[.!?]+(?:\s|$)|\n+", text)}
    chunks, first, covered = [], 0, 0
    while first < len(offsets):
        last = min(first + budget, len(offsets))
        if last < len(offsets):
            candidates = [i for i in range(first + max(1, budget // 2), last + 1)
                          if i > covered and any(c in boundaries for c in range(offsets[i - 1][1], offsets[i][0] + 1))]
            if candidates:
                last = candidates[-1]
        start = 0 if not chunks else min(offsets[first][0], chunks[-1].end)
        while True:
            end = len(text) if last == len(offsets) else offsets[last - 1][1]
            size = len(tokenizer(text[start:end], add_special_tokens=False, truncation=False)["input_ids"])
            if size <= budget:
                break
            last -= 1
            if last <= first:
                raise ValueError("Tokenizer cannot produce a safe chunk without truncation")
        if end <= start or (chunks and end <= chunks[-1].end):
            raise ValueError("Tokenizer offsets did not advance narrative coverage")
        chunks.append(Chunk(start, end, max(1, last - covered)))
        covered = last
        if last == len(offsets):
            break
        first = max(first + 1, last - overlap)
    if chunks[0].start != 0 or chunks[-1].end != len(text):
        raise ValueError("Incomplete narrative coverage")
    return chunks, len(offsets)


class FullNarrativeEncoder:
    def __init__(self, embedder, overlap=32, batch_size=256):
        self.embedder, self.tokenizer = embedder, embedder.tokenizer
        if not getattr(self.tokenizer, "is_fast", False):
            raise ValueError("Full-narrative coverage requires a fast tokenizer with character offsets")
        self.limit = min(int(embedder.max_seq_length), int(self.tokenizer.model_max_length))
        self.budget = self.limit - self.tokenizer.num_special_tokens_to_add(pair=False)
        self.overlap, self.batch_size = int(overlap), int(batch_size)
        if self.batch_size < 1 or not 0 <= self.overlap < self.budget:
            raise ValueError("Invalid narrative chunk settings")

    def encode(self, texts):
        sums, maxima, weights, coverage = {}, {}, {}, []
        queue, owners = [], []

        def flush():
            if not queue:
                return
            vectors = np.asarray(self.embedder.encode(queue, batch_size=self.batch_size,
                                convert_to_numpy=True, show_progress_bar=False, prompt=""), dtype=np.float32)
            if vectors.ndim != 2 or len(vectors) != len(queue) or not np.isfinite(vectors).all():
                raise ValueError("Invalid narrative chunk embeddings")
            for (owner, weight), vector in zip(owners, vectors):
                if owner not in sums:
                    sums[owner] = vector.astype(np.float64) * weight
                    maxima[owner] = vector.copy()
                    weights[owner] = weight
                else:
                    sums[owner] += vector * float(weight)
                    maxima[owner] = np.maximum(maxima[owner], vector)
                    weights[owner] += weight
            queue.clear()
            owners.clear()

        for index, text in enumerate(texts):
            chunks, tokens = split_narrative(text, self.tokenizer, self.budget, self.overlap)
            coverage.append({"narrative_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                             "tokens": tokens, "chunks": len(chunks), "token_budget": self.budget,
                             "overlap_tokens": self.overlap, "method": ALGORITHM,
                             "status": "complete" if text.strip() else "missing"})
            for chunk in chunks:
                queue.append(text[chunk.start:chunk.end])
                owners.append((index, chunk.weight))
                if len(queue) >= self.batch_size:
                    flush()
        flush()
        features = np.asarray([np.concatenate((sums[i] / weights[i], maxima[i]))
                               for i in range(len(texts))], dtype=np.float32)
        return features, coverage
