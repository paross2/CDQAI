<!-- CDQAI file version: 2.5.0 -->
# Person severity reconciliation

The configured crash-severity field remains the source used for priority
weighting. The optional person-severity comparison does not overwrite it or place
person rows in the model dataset. An analyst must decide whether a discrepancy
represents an error.

The comparison uses configured code mappings. Numeric and zero-padded
representations may be accepted by the selected mapping. Unresolved codes remain
unresolved and must not be interpreted using unrelated fields.

When all matched persons have known severity and valid unique keys, their highest
severity is compared with configured crash severity. With unresolved persons,
only a known severity higher than the crash severity establishes a discrepancy.
Duplicate or missing relationship keys prevent comparison. Missing matched persons
are not assumed uninjured. A fully mapped set of returned rows does not establish
that the source has complete person coverage; discrepancies remain review prompts.

## Enable locally

In your ignored `config/config.yaml`, add:

```yaml
person_severity:
  enabled: true
  table: "YOUR_PERSON_DATA_SOURCE"
```

Configure the person source, crash source, and corresponding identifier/year and
severity fields for your environment. No private configuration is included in
this repository. The feature is disabled by default.

The loader selects only configured fields required for comparison and retains
relationship keys only for validation. It uses exact trimmed identifier text,
normalizing numeric `.0` suffixes; it does not guess equivalence of leading zeros.
Unmatched person rows are outside this comparison and are not orphan findings.

Run the full pipeline locally. When using a merged crash cache, refresh it after
source changes so current person rows are compared with current crash data.
Person data is freshly loaded on every enabled run, including runs using a crash cache.

The protected local `outputs/person_severity_review.csv` lists comparison status,
highest known person severity, and unresolved counts.
Discrepancies also enter normal evidence, findings, and dashboard outputs.
These outputs must not be uploaded or shared with AI tools. Disabling the feature
does not remove older output files; a previous CSV must not be read as a current run.

This is the person-severity comparison only. Vehicle and factor-source scoring is
not implemented by this feature. No live database checks were performed;
verification uses fabricated records and mocked source reads.
