<!-- CDQAI file version: 2.3.2 -->
# CDQAI 2.3.0 — Narrative Evidence and Analyst Review

This local release adds full-narrative yellow highlights for exact deterministic
rule matches and bounded sentence-removal model sensitivity. It also includes
optional local Ollama guidance, severity-aware narrative priority, and optional
Rec03 severity reconciliation that preserves Rec01 KABCO and unresolved code 09.

See [narrative highlighting](NARRATIVE_HIGHLIGHTS.md),
[analyst guidance](ANALYST_GUIDANCE.md), and [person severity](PERSON_SEVERITY.md)
for setup and limits. Model sensitivity is not proof that text is incorrect.

Run Run_CDQAI.bat to regenerate reports; existing dashboards are not upgraded
in place. Keep the generated dashboard and companion narrative JavaScript together.
Use Configure_CDQAI.bat locally if enabling the optional features. Embedding-model
assets must already be installed; runtime Hub access is disabled.

Validation used fabricated records: 100 regression tests passed, followed by
an additional scoring-to-evidence integration test. Two workbook-dependent tests
were excluded. No production records or private configuration were inspected.

File markers and application metadata are synchronized to 2.3.0. GitHub publication
is separate from the local upgrade; no tag or published GitHub release was created.
