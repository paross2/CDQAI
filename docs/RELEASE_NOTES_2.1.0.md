# CDQAI 2.1.0 — Responsive Analyst Decision Support

Version 2.1.0 improves analyst triage without changing the underlying anomaly models.

## Dashboard

The dashboard now uses a responsive page width, adaptive metric cards, contained tables, sticky headers, sortable summary columns, and expandable finding details. Long explanations and rule identifiers no longer force the overall page beyond the browser viewport.

## Decision-support fields

Finding CSV outputs now include:

- `ConfidenceScore`: deterministic 0–100 synthesis of maximum evidence confidence, signal-family agreement, and rule support.
- `EvidenceAgreement`: the independent analytical signal families supporting the finding.
- `EvidenceStrength`: Limited, Moderate, Strong, or Very Strong.
- `AnalystPriority`: analyst-facing review urgency.
- `RecommendedAction`: deterministic next-step guidance based on the evidence categories.

These fields organize existing evidence; they do not determine that a record is incorrect.
