<!-- CDQAI file version: 2.5.0 -->
# CDQAI 2.5.0 — Contributing-Factor Review

## What changed

- Adds optional configured loading of Human, Environmental, and Vehicle coded
  factors using only MFN, year, and code projections.
- Adds multi-select factor filters to **All Findings**. Multiple codes within a
  category match with OR; active categories combine with AND. Filter choices
  come only from codes present in loaded tabular data, never from narrative text.
- Adds year-aware coded-factor details to each finding and a separate
  **Narrative-derived factors** placeholder that does not affect coded filters.
- Moves **Flagged crash report** below **Top Actionable Findings** and gives
  each findings block independent expand/collapse controls.
- Removes the separate scooter MFN-only PDF control. E-scooter findings remain
  part of the findings tables.
- Paginates All Findings with full-set filtering and sorting. Only the current
  page is rendered; detailed finding content and narratives load from companion
  chunks when expanded.
- Configures `Run_CDQAI.bat` to put each complete live run in a fresh dated
  output folder with its log, without deleting or overwriting prior runs.
- Checks declared runtime imports at startup and installs only missing
  requirements with the selected interpreter; installation errors stop the run.
- Retries DVMT workbooks on subsequent runs rather than caching partial context
  when any workbook fails to load.

## Local configuration

Factor review is disabled by default. Configure `factor_review` in the ignored
local `config/config.yaml`, setting source identifiers and the corresponding
identifier, year, and category-code fields for each category. The maintained
example uses placeholders and contains no local source names or crash data.

Code 99 is displayed as **None Detected**, while absent factor data is reported
as unavailable. Narrative-derived factor detection is not implemented; its
placeholder is distinct from the coded-factor filters.

## Validation

Automated tests use synthetic records and fake query results only. No live
source access, local configuration, crash data, PII, or real training data is
required for source-only validation.
