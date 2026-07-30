# Changelog

## 2.2.4 — Reliable Narrative MFN Matching

- Canonicalizes MFNs before narrative joins, including integer, string, and `.0` forms.
- Selects the longest nonblank narrative when duplicate MFN rows exist.
- Uses both merged and source narrative frames to populate dashboard evidence.
- Adds regression tests for MFN normalization and duplicate narrative handling.

## 2.2.3 — Lightweight On-Demand Narrative Evidence

- Moved complete narrative payloads out of `dashboard.html` into `dashboard_narratives.js`.
- Added on-demand rendering when a finding row is expanded.
- Added persisted `finding_evidence.parquet` with full narratives and structured evidence spans.
- Added explicit missing-narrative warnings and analyst spot-check instructions.
- Preserved direct rule phrase highlighting without false token attribution for embedding-only anomalies.


## 2.2.2 — Transparent Narrative Evidence

- Added narratives and rule-grounded phrase highlighting to expanded dashboard findings.
- Added Git, Windows 11, GPU, AI-stack, model, and system provenance reporting.
- Added explicit attribution limitations for embedding-only narrative anomalies.

## 2.2.1 — Field-Safe Context-Aware Analysis

- Excluded latitude, longitude, coordinate, County Number, context, identifier, and raw HHMM fields from global structured anomaly scoring.
- Replaced numeric-type-only selection with a shared field-role classifier used by both modeling and the field manifest.
- Removed schema-order-based first-N feature truncation.
- Replaced blanket zero filling with median imputation for approved numeric features.
- Removed unnecessary RobustScaler processing from Isolation Forest.
- Added regression tests proving valid geolocation and county changes cannot alter structured anomaly scores.
- Removed the obsolete `rules/` directory and placeholder `rules.json` from the distribution.
- Added configuration for explicit reviewed feature allow-lists and field aliases.

## 2.2.0 — Context-Aware Analysis

- Added annual county-level Kentucky DVMT and roadway mileage context for 1997–2025.
- Added exact-year matching with prior-year-preferred and future-year-last-resort fallback.
- Added context provenance, year-gap, freshness, urban/rural, county, and exposure fields to the analytical dataset.
- Added graceful degradation when context files or join fields are unavailable.
- Excluded County Number and all derived context fields from global Isolation Forest scoring by default.
- Added a downloadable analysis field manifest showing field roles, eligibility, exclusions, missingness, and cardinality.
- Added annual-update guidance and normalized Parquet caching for efficient large-data runs.

# CDQAI Changelog

## 2.1.2 — Collapsible Dashboard & Findings Explorer

- Added collapsible accordion sections for How CDQAI Works, About CDQAI, Top Actionable Findings, and All Findings.
- Added a complete findings explorer with text search, Primary Issue, Evidence Strength, Analyst Priority, and confidence-range filters.
- Added ascending and descending sorting for findings columns and a live visible-findings count.
- Standardized the project directory and launcher/document names to `CDQAI`, `Run_CDQAI.bat`, and `INSTALL.txt`.
- No analytical models, evidence rules, or scoring behavior changed.


## 2.1.1 — Build Metadata & Provenance

- Added centralized build metadata and runtime provenance.
- Added developer, contributor, AI-assistance, and funding attribution.
- Added MIT software license and CC BY 4.0 documentation license.
- Added citation metadata and dashboard About/Provenance content.
- Corrected stale current-release version references and filenames.

# Changelog

## 2.0.2 — Annual Reporting Reliability

### Fixed

- Added robust `CrashYear` mapping using explicit year fields, including `YR`.
- Added collision-date fallback parsing for supported date fields.
- Restored populated annual findings output.

### Changed

- Updated release metadata and Windows launcher to Version 2.0.2.
- Expanded Git exclusions and removed compiled Python artifacts.
- Added standard release metadata and runtime-folder placeholders.

## 2.0.1 — Documentation and Transparency Update

- Expanded the dashboard and documentation to explain the implemented deterministic rules, structured Isolation Forest, narrative embeddings, evidence thresholds, ensemble calculation, finding synthesis, priority formula, and limitations.
- Made the dashboard explanation read active configuration values rather than hard-code thresholds and rule settings.
- Added regression tests for configuration-driven threshold display and accurate disclosure of deterministic, non-LLM finding synthesis.
- Added Version 2.0.1 release notes.

## Version 1.4.0 — Evidence Framework

### Added

- Kentucky-specific record type definitions.
- Kentucky traffic records system definitions.
- Traffic records quality characteristic definitions.
- Severity definitions.
- Evidence dataclass.
- EvidenceBundle dataclass.
- Evidence summary helpers.
- Evidence report writer.
- README version history.

## Version 1.3.0 — Model Layer

### Added

- Structured anomaly detector.
- Narrative embedding manager.
- Narrative anomaly detector.
- Embedding cache.
- Combined model score output.
- Model output report files.

## Version 1.2.0 — Data Layer

### Added

- DatabaseManager.
- CrashDataset and DatasetMetadata.
- SQL Server data loading.
- MFN normalization and merge pipeline.
- Parquet caching.
- Dataset summary and run manifest outputs.

## Version 1.1.0 — Foundation

### Added

- CDQAI project foundation.
- Configuration loader.
- Logging system.
- Runtime folder creation.
- CLI health check.
- Initial package structure.
- Documentation scaffolding.

## 2.0.0 — Unified Evidence Platform
- Integrated structured, narrative, ensemble, and multi-model evidence.
- Added MFN-level finding synthesis and priority ranking.
- Added actionable, top-finding, annual, dashboard, and summary reports.
- Added Windows launcher and Version 2.0 documentation.
- Clarified that CDQAI reports evidence rather than conclusions.

## 2.1.0 — Responsive Analyst Decision Support

- Replaced the wide dashboard findings table with a compact, expandable analyst queue.
- Added responsive viewport-based layout, horizontal table containment, sticky headers, wrapping, print rules, and client-side sorting.
- Added deterministic `ConfidenceScore`, `EvidenceAgreement`, `EvidenceStrength`, `AnalystPriority`, and `RecommendedAction` fields to finding exports.
- Preserved the existing priority score and evidence synthesis logic for backward compatibility.
