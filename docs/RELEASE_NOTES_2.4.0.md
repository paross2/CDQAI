<!-- CDQAI file version: 2.5.0 -->
# CDQAI 2.4.0 - Local E-Scooter Narrative Review

## Highlights

- Adds an opt-in narrative classifier using TF-IDF and Logistic Regression, trained at runtime from a user-configured local labeled CSV.
- Performs a stratified holdout precision check before fitting on all supplied labels.
- Loads only configured crash identifier, year, and unit-type code from local sources to suppress candidates already coded with the configured scooter code.
- Adds review-only evidence and a separate dashboard print/Save-as-PDF report containing only candidate MFNs.
- Keeps the detector disabled by default; no private training data, server settings, narratives, or classifier artifacts are committed.

## Important limitations

- Unit type code `12` is a provisional assumption from the legacy script. Verify it against the applicable current codebook before enabling the detector.
- Model scores are not calibrated probabilities and do not confirm scooter involvement or a coding error.
- This release does not correct structured fields. Analysts must verify every candidate against source records.
- Training files and database table/field mappings must be configured locally in the ignored `config/config.yaml`.

## Validation

- Synthetic-only classifier tests verify that matching explicit scooter codes suppress candidates and that evidence/exports omit narrative text.
- Real data, local database access, and private training files are intentionally outside automated validation.
