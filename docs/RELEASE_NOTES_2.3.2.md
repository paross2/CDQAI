<!-- CDQAI file version: 2.3.2 -->
# CDQAI 2.3.2 — Plain-Language Analyst Guidance

Local Llama drafts now explain related findings together in conversational language,
state what the evidence cannot establish, and suggest a practical next check rather
than simply repeating model percentiles.

- Combine base-model evidence while omitting repetitive derived summaries from the prompt.
- Use bounded, recorded sentence-sensitivity excerpts when available.
- Reject responses without a review action and certain unsupported shared-cause claims.
- Preserve evidence references and keep drafts separate from scores, rankings, and deterministic explanations.
- Retain local-only Ollama verification, offline embedding-model loading, narrative highlights,
  optional Rec03 reconciliation, and selected-crash print-to-PDF reporting from 2.3.1.

These checks do not prove that generated prose is correct. Analysts must verify
drafts against the evidence. Two anomaly scores do not establish a contradiction
or a common cause. Detecting uncoded human factors remains future work.

Upgrade the source files, retain your ignored local configuration, and run
Run_CDQAI.bat locally to regenerate the dashboard and drafts. Ollama guidance must
already be enabled and configured for a verified local model. Missing source
narratives cannot be recovered by this update.

Validation: 106 tests passed using fabricated records and mocked services; a
fabricated local Llama request also passed during development. Two workbook-dependent
tests are excluded from source-only verification.
No private configuration, crash inputs, record-level reports, or runtime caches
are attached to this release.
