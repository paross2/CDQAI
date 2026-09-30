<!-- CDQAI file version: 2.3.1 -->
# CDQAI 2.3.1 — Analyst Review and Selected-Crash Reports

This release publishes the accumulated dashboard and local-analysis changes since
2.2.5, including work previously labelled 2.3.0 in local development.

- Full narratives with exact rule highlights and bounded model sentence-removal sensitivity.
- Session-only review checkboxes and print-to-PDF reports containing selected crashes only.
- Optional local-only Ollama/Llama drafts, separate from deterministic scoring and evidence.
- Severity-aware narrative priority, blank-narrative exclusion, and removal of derived-signal double counting.
- Optional Rec03 severity reconciliation: code 09 remains unresolved and Rec01 KABCO controls priority.
- CountyCode DVMT matching, offline embedding-model loading, and safer local setup/cache switching.

Use How To Run.txt and the feature documents for configuration and limitations.
Run locally to regenerate reports. Narratives absent from the SQL source cannot
be highlighted. Print flags clear on reload; no analyst notes are collected.

Validation uses fabricated records and mocked services, with a fabricated Edge
browser check for review selection, full-text highlighting, and print invocation.
Workbook-dependent tests are excluded from source-only verification. No production
data, private configuration, runtime reports, or caches are included in this release.

More conversational Llama explanations are planned as subsequent work. Detection
of uncoded human factors from narratives is future research, not implemented here.
