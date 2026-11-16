# CDQAI Version 2.2.1 — Field-Safe Context-Aware Analysis

Version 2.2.1 corrects the structured-model feature-selection logic identified during analyst review of Version 2.2.0. Numeric storage type is no longer treated as proof that a field is appropriate for global anomaly scoring.

## Model-input corrections

- County Number and county aliases are context and grouping fields only.
- Latitude, longitude, coordinates, easting, and northing are geographic-context fields only.
- Context-derived and provenance columns remain outside the global structured model.
- Record identifiers and linkage keys are excluded.
- Raw HHMM/time fields are excluded until an explicit cyclical transformation is implemented.
- Constant or empty numeric fields are excluded.
- Optional `include_fields` configuration supports a reviewed deterministic allow-list.

Geographic fields remain available for mapping, filtering, context joins, and future deterministic checks such as invalid coordinate ranges or county-coordinate disagreement.

## Preprocessing corrections

- Removed the first-N numeric-column truncation that made schema order affect model behavior.
- Replaced blanket `fillna(0)` behavior with median imputation.
- Removed RobustScaler because Isolation Forest does not require scaling and the step added memory and processing overhead.

## Transparency and tests

The structured detector and `analysis_field_manifest.csv` now share one field-role classifier. The manifest records each field's analytical role, model eligibility, and exclusion reason. Regression tests verify that changing only valid Kentucky coordinates or County Number does not change structured anomaly scores.

## Packaging correction

The obsolete `rules/` folder and placeholder `rules.json` are not included. Deterministic rules remain implemented in Python under `cdqai/rules/`, while configurable thresholds remain in YAML configuration.
