# CDQAI Version 2.0.2 Release Notes

## Annual Reporting Reliability

Version 2.0.2 is a maintenance release focused on reliable year-based reporting and repository hygiene. It does not change the structured, narrative, ensemble, evidence, or finding algorithms.

### Fixed

- Recognizes `YR` as an explicit crash-year field.
- Falls back to deriving `CrashYear` from supported collision-date fields, including `CollisionDate`.
- Validates derived years and preserves missing years using pandas nullable integer values.
- Restores populated `CrashYear` values in `findings.csv`.
- Restores annual aggregation in `annual_findings.csv`.

### Repository improvements

- Updated package, configuration, documentation, and launcher metadata to Version 2.0.2.
- Added a root `VERSION` file and root `CHANGELOG.md`.
- Expanded `.gitignore` for virtual environments, IDE files, runtime artifacts, local configuration, and generated model data.
- Removed compiled Python artifacts from the release package.
- Added tracked placeholder files for `outputs`, `cache`, and `logs`.

### Validation

The year-reporting correction was validated against a production run containing crash years 2020 through 2024. All 15,088 findings received a `CrashYear`, with zero missing values, and `annual_findings.csv` was populated for all five years.

### Deferred

Blank-narrative model scoring and related ensemble behavior remain scheduled for a later feature release.
