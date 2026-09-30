# CDQAI file version: 2.3.5
"""Bounded sentence-removal sensitivity against the fitted narrative model."""
import hashlib
import re
import numpy as np


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sentence_sensitivity(text, encode, model, original_score, max_sentences=12):
    spans = [(m.start(), m.end()) for m in re.finditer(r"[^.!?\n]+(?:[.!?]+|$)", text)
             if m.group().strip()]
    if len(spans) < 2:
        return []
    # Spread the bounded sample across the narrative instead of inspecting only its beginning.
    selected = np.linspace(0, len(spans) - 1, min(max_sentences, len(spans)), dtype=int)
    candidates = [spans[i] for i in selected]
    variants = [text] + [text[:start] + text[end:] for start, end in candidates]
    scores = -model.decision_function(encode(variants))
    if not np.isclose(scores[0], original_score, atol=1e-6, rtol=1e-5):
        return []  # Cached/model input does not reproduce the scored narrative.
    result = []
    for (start, end), score in zip(candidates, scores[1:]):
        while start < end and text[start].isspace():
            start += 1
        delta = float(scores[0] - score)
        if delta > 1e-6:
            result.append({"start": start, "end": end, "text": text[start:end],
                "score_drop": delta, "method": "sentence_removal_sensitivity",
                "narrative_sha256": text_digest(text),
                "reason": "Removing this sentence reduced the fitted model's anomaly score. This is sensitivity evidence, not proof of an error."})
    return sorted(result, key=lambda x: -x["score_drop"])[:min(2, len(spans) - 1)]
