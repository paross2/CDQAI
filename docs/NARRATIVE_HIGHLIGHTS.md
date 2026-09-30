<!-- CDQAI file version: 2.3.2 -->
# Narrative highlights in 2.3.0

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
The model's existing token limit applies; this feature does not extend it to cover
every token of a long narrative. Cached embeddings that do not reproduce the
current text suppress sensitivity highlights rather than supplying false spans.

Run Run_CDQAI.bat locally to regenerate reports. Existing dashboards do not change
when software is upgraded. These narratives and span outputs remain protected.
