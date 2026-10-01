<!-- CDQAI file version: 2.3.6 -->
# CDQAI 2.3.6 - AI Powered Crash Data Anomaly Detector

- Scores complete narratives with overlapping token-budgeted chunks and combined weighted-mean/maximum features; no silent fallback to truncated inputs.
- Rebuilds embedding caches when ordered record/text hashes, model weights, tokenizer, software stack, or chunk settings change. Cache integrity checks reject older or mismatched arrays.
- Re-encodes the full remaining narrative during sentence-removal review; preserves original offsets for highlights and reports complete/limited/unavailable review separately.
- Exports coverage in model scores, finding evidence, dashboard companion data, and manifest summary. Keeps duplicate-ID previews aligned with their original rows.
- Includes the dashboard Expand all/Collapse all controls, accurate highlight guidance, release preflight audit, and automatic temporary-workspace cleanup.

## Upgrade and validation

Run Run_CDQAI.bat locally from the authoritative GitHub installation. The first
narrative run rebuilds old embeddings automatically and can take substantially
longer. No SQL or real-data pipeline was run as part of development validation.
Regenerate dashboard.html and dashboard_narratives.js together. Earlier generated
reports retain their old version and analysis method.

The representation and anomaly rankings change. Detailed highlights remain bounded
to the configured qualifying-record and sentence limits (defaults: 20 and 12).
Full-text coverage does not guarantee a highlight or establish a data error.
The old merged-data cache still follows normal cache settings; use --refresh-cache
when source database content has changed and should be reloaded.

Validation: 130 tests passed in an isolated source-only workspace, including the
installed offline embedding model and an Edge browser check. Two external-workbook
tests were excluded. Synthetic cases covered beginning/middle/end signals, Unicode,
long and newline-separated narratives, cache invalidation/corruption, duplicate IDs,
coverage exports, and dashboard interactions. Temporary artifacts were removed.
