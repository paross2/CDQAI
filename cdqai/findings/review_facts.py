# CDQAI file version: 2.3.1
"""Grounded analyst breadcrumbs independent of an optional language model."""
from __future__ import annotations

import math


def build_review_facts(finding) -> tuple[dict, ...]:
    facts = []
    for index, item in enumerate(finding.evidence, 1):
        fields = [str(field) for field in item.supporting_fields]
        text = item.message
        percentile = item.supporting_values.get("percentile")
        if isinstance(percentile, (int, float)) and math.isfinite(percentile):
            text += f" Recorded percentile: {percentile:g}."
        hints = item.supporting_values.get("review_fields", [])
        if item.source == "MODEL_STRUCTURED":
            for hint in hints:
                fields.append(hint["field"])
                text += (f" Review {hint['field']}={hint['value']:g}; cohort 1st-99th percentile "
                         f"range {hint['p01']:g} to {hint['p99']:g}, median {hint['median']:g}.")
            text += (" These comparisons do not identify which field caused the model score." if hints else
                     " No individual tail-value field was identified; the signal concerns a combination of variables.")
        elif item.source == "MODEL_NARRATIVE":
            text += " No individual word or sentence is established as the cause of this model score."
        elif not item.source.startswith("MODEL_"):
            # Include coded numeric values only. Never copy raw narrative text into the LLM packet.
            for field in fields:
                value = item.supporting_values.get(field)
                if isinstance(value, (int, float)) and math.isfinite(float(value)):
                    text += f" Observed {field}={value}."
        facts.append({"id": f"E{index}", "source": item.source,
                      "fields": list(dict.fromkeys(fields)), "text": text})
    return tuple(facts)
