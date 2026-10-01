<!-- CDQAI file version: 2.3.6 -->
# Narrative highlights in CDQAI 2.3.6

Expand a dashboard finding to see the complete narrative with yellow segments.
Hover over a segment for its evidence method. Surrounding text remains visible.
The summary cards count highlighted findings, available text without highlights,
and missing text. In All Findings, select Narrative review > Has yellow highlights
to find the highlighted records directly. Missing-text notices are not segment
highlights, and structured-only flags need not have narrative evidence.
Keep dashboard.html and dashboard_narratives.js together in the outputs folder.

Rule highlights use exact match positions from the full narrative, including
triggers after character 500. They show what matched the rule, not a confirmed
contradiction: negation and reporting context still need analyst review.

Model highlights use sentence-removal sensitivity against the same fitted
Isolation Forest. For the top 20 qualifying narrative rows by narrative percentile,
up to 12 sentences spread across the text are removed individually and rescored.
At most two sentences with a positive score drop are highlighted; at least one
sentence remains unhighlighted. This measures sensitivity to removing text, not
proof that the sentence is incorrect or the sole cause of the original flag.
Sentence boundaries are punctuation-based and may split abbreviations.

The complete narrative is re-embedded and its score must reproduce the original
score before highlights are accepted. A content digest and exact substring check
prevent applying spans to a different narrative selected for the same MFN.
Unicode offsets are handled as code points in the browser. HTML is escaped.

Narratives outside the bounded sample, single-sentence narratives, and cases with
no positive score drop have no model highlights. Structured-only findings are
not labelled statistically unusual narratives. Llama does not choose highlights.
Original scores, priorities, and evidence decisions are unchanged by this review.

Configure models.narrative.sentence_review.enabled (default true) and max_records
(default 20, maximum 100). Additional local embedding work increases runtime.
All tokens are now covered by overlapping chunks within the model token limit.
Sentence-removal variants use the same full-text chunking and feature aggregation
as original scoring. Cached embeddings from the older truncated method are rebuilt.
Configure max_sentences (default 12, maximum 100) separately from max_records.
The dashboard reports full-text token/chunk coverage separately from the number
of sentences tested. A complete text score does not imply complete highlight review.

Run Run_CDQAI.bat locally to regenerate reports. Existing dashboards do not change
when software is upgraded. These narratives and span outputs remain protected.

## Reviewing highlights and opening findings

Use Expand all and Collapse all at the top of the dashboard. Expand all respects
current finding filters and opens the containing finding sections. Each expanded
narrative shows the number of supported yellow highlights and scrolls its text
pane to the first one; the complete text remains available above and below it.

A finding without supported spans says No supported text highlight, and its
What to check instruction refers to recorded triggers and coded fields instead.
Not every statistical anomaly has sentence-level evidence: sentence review is
bounded, and a score change may not support a particular sentence. Structured-only
and completeness findings do not imply a word-level narrative trigger. Use the
Narrative status filter to find records with yellow highlights.

Missing companion files and recorded spans that do not match the displayed
narrative are explained separately. Keep dashboard.html and dashboard_narratives.js
from the same successful run together. Regenerate reports locally after updating.

## Full-text scoring in 2.3.6

The default tokenizer has a 256-token model window. Space for special tokens is
reserved, and adjacent chunks overlap by 32 content tokens by default. Sentence
boundaries are preferred when they fit; long sentences split safely across windows.
Every original character remains covered, and each chunk is re-tokenized to check
its budget before encoding. A tokenizer without usable offsets fails explicitly.

Chunk vectors are combined as a new-token-weighted mean plus an elementwise maximum.
The maximum preserves local embedding activations rather than averaging them away;
it is not a separate causal attribution or a guarantee that important facts rank high.
Removing a sentence changes chunk boundaries as well as content, so yellow model
highlights remain sensitivity evidence. They are not proof that a passage is wrong.

Model scores/rankings can change and are not numerically comparable to 2.3.5 scores.
Longer texts cost more to encode and may produce different feature distributions.
Validate representative crash categories locally before relying on changed priorities.
Scoring failure does not silently fall back to truncation. Detail review may be
limited, disabled, not selected, unavailable, or complete; these states are exported.
