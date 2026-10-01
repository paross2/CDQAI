<!-- CDQAI file version: 2.3.6 -->
# Person severity reconciliation

Rec01 `KABCO` remains the crash severity used for priority weighting. The optional
Rec03 comparison does not overwrite it or place person rows in the model dataset.
An analyst must decide whether a discrepancy represents an error.

The supplied field-code guide maps Injury Severity 01/02/03/04/05 to K/A/B/C/O.
Numeric and zero-padded representations are accepted. Injury Severity 09 means
"Fatality Removed by FARS Reconciliation"; it is retained as a reconciliation flag
with unresolved person severity. Codes in seating-position and other fields are
not used to interpret Injury Severity. Blank/unrecognized codes are unresolved.

When all matched persons have known severity and valid unique keys, their highest
severity is compared to Rec01 KABCO. With unresolved persons, only a known severity
higher than KABCO establishes a discrepancy. Code 09 alone never creates one.
Duplicate or missing unit/person keys prevent comparison. Missing matched persons
are not assumed uninjured. A fully mapped set of returned rows does not establish
that the source has complete person coverage; discrepancies remain review prompts.

## Enable locally

In your ignored config/config.yaml, add:

```yaml
person_severity:
  enabled: true
  table: "MultiYear.dbo.Rec03_2021to2025"
```

Ensure the configured crash table covers the matching period and has `YR`, `KABCO`,
and its configured crash identifier. No private configuration is modified by this
change. The feature is disabled by default.

The loader selects only `Master File`, `Unit Number`, `Person Number`,
`Injury Severity`, and `YR`. It matches crash identifier plus year and retains
unit/person keys only for validation. It uses exact trimmed identifier text,
normalizing numeric .0 suffixes; it does not guess equivalence of leading zeros.
Unmatched person rows are outside this comparison and are not orphan findings.

Run the full pipeline locally. When using a merged crash cache, refresh it after
source changes so current Rec03 rows are compared with current Rec01 data.
Rec03 is freshly loaded on every enabled run, including runs using a crash cache.

The protected local `outputs/person_severity_review.csv` lists comparison status,
highest known person severity, unresolved counts, and `Reconciliation09Count`.
Discrepancies also enter normal evidence, findings, and dashboard outputs.
These outputs must not be uploaded or shared with AI tools. Disabling the feature
does not remove older output files; a previous CSV must not be read as a current run.

This is the Rec03 severity comparison only. Vehicle and factor-table scoring for
Rec02/Rec11/Rec12/Rec13 is not implemented by this change. No live database checks
were performed; verification uses fabricated records and mocked SQL reads.
