# CDQAI file version: 2.3.6
"""Bounded sentence-removal sensitivity against the fitted narrative model."""
import hashlib
import re
import numpy as np


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sentence_sensitivity(text, encode, model, original_score, max_sentences=12, return_details=False):
    if not 1 <= max_sentences <= 100:
        raise ValueError("sentence_review.max_sentences must be between 1 and 100")
    spans = [(m.start(), m.end()) for m in re.finditer(r"[^.!?\n]+(?:[.!?]+|(?=\n|$))", text)
             if m.group().strip()]
    def finish(result, status, tested=0):
        details = {"spans": result, "status": status, "sentences_total": len(spans), "sentences_tested": tested}
        return details if return_details else result
    if len(spans) < 2:
        return finish([], "insufficient_sentences")
    # Spread the bounded sample across the narrative instead of inspecting only its beginning.
    selected = np.linspace(0, len(spans) - 1, min(max_sentences, len(spans)), dtype=int)
    candidates = [spans[i] for i in selected]
    baseline = float(-model.decision_function(encode([text]))[0])
    if not np.isclose(baseline, original_score, atol=1e-6, rtol=1e-5):
        return finish([], "input_score_mismatch")
    result = []
    for start, end in candidates:
        # Re-chunk and re-encode the complete remaining narrative; no truncated variants.
        score = float(-model.decision_function(encode([text[:start] + text[end:]]))[0])
        while start < end and text[start].isspace():
            start += 1
        delta = baseline - score
        if delta > 1e-6:
            result.append({"start": start, "end": end, "text": text[start:end],
                "score_drop": delta, "method": "sentence_removal_sensitivity",
                "narrative_sha256": text_digest(text),
                "reason": "Removing this sentence reduced the fitted model's anomaly score. This is sensitivity evidence, not proof of an error."})
    selected_spans = sorted(result, key=lambda x: -x["score_drop"])[:min(2, len(spans) - 1)]
    return finish(selected_spans, "limited" if len(candidates) < len(spans) else "complete", len(candidates))
