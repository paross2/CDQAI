# Development review: 2026-09-23

## Baseline

Both inspected checkouts started clean at `3a2eb99` (release 2.2.4). Source files
matched after line-ending normalization. `VERSION`, package metadata, and build
metadata say 2.2.4; several current setup documents still said 2.2.3. The existing
environment runs Python 3.11.6. The first test run produced 32 passes and two failures:
a missing openpyxl dependency and a test requiring the deliberately ignored private
configuration file. Setup work corrects these issues without changing model thresholds.

The private configuration exists and uses Windows authentication. Source settings
were checked without reproducing database values here. The configured narrative
source differs from the historical handoff. Loaders currently handle one crash
table and one narrative table, not separate Rec02/Rec03 loading and validation.

## Confirmed protections and limitations

- Global structured scoring excludes configured identifiers, geography, county,
  raw HHMM time, and Context-prefixed fields. Missing values use median imputation.
  Feature selection no longer truncates by schema order, and scoring uses all rows;
  Isolation Forest still uses its own normal tree-fitting subsampling.
- The 2.2.4 canonical MFN and longest-narrative fix is in dashboard lookup code.
  Initial preprocessing only converts MFNs to strings and strips whitespace.
- Finding-year derivation recognizes YR and YYYYMMDD CollisionDate, but checks
  other year columns before YR. It chooses one year column for the whole frame;
  an empty CrashYear column can hide a valid YR, and an invalid year is filtered
  after date fallback. Add explicit row-level precedence and regression tests.
- Actual default weights are structured 0.5 and narrative 0.5. Rules produce
  separate evidence and influence finding priority rather than contributing a
  third weighted model score.
- `docs/CDQAI_DESIGN.md` is a placeholder, not a completed system design.
- Current tracked runtime directories contain only `.gitkeep`; the private config
  is not tracked. Tracked XLSX files are documented county-level DVMT context,
  not record-level crash exports. Ignore rules do not protect a file already tracked
  or added with `git add -f`, and this review is not a full historical secret audit.

## Recommended next work, in order

1. **Make joins and cache identity reliable.** Share canonical MFN handling across
   loaders, preprocessing, findings, and reports. Reject or quarantine missing keys;
   define duplicate resolution and validate join cardinality. Duplicate MFNs can
   multiply rows during both narrative merging and score merging. Embedding cache
   identity currently checks only ordered MFNs, not narrative content, model revision,
   preprocessing version, dtype, or array integrity. A repaired narrative can reuse
   a stale embedding. Merged caches also lack source/configuration fingerprints.
2. **Correct evidence dependence before tuning weights.** Ensemble and multi-model
   evidence derive from the same component scores, but source diversity and evidence
   strength count them as independent corroboration. Separate base signal families
   from derived summaries, and cover disabled-model and tied-score cases. Percentiles
   and the displayed confidence heuristic must not imply a calibrated error probability.
3. **Make evidence specific.** Retain observed coded values, validated Kentucky code
   meanings, appropriate comparison groups, and concrete follow-up actions. Add
   negation/context handling to injury rules: a phrase such as "no injury" currently
   contains a keyword that can trigger conflict evidence. Fix year precedence alongside
   report regression tests. Validate Rec02/Rec03 relationships before claiming that scope.
4. **Make embeddings scalable after cache correctness.** Current code encodes all text
   and loads the full array into RAM. Add measured peak-memory/runtime reporting,
   content-based reuse, resumable batches, memory-mapped arrays, explicit local-model
   selection, and model revision provenance. Benchmark on an approved representative
   sample before processing approximately half a million records.
5. **Calibrate with analyst dispositions.** Use reviewed samples across years,
   counties, missingness patterns, and finding categories. Evaluate precision at
   the analyst review budget and stability across cohorts, then tune thresholds and
   weights. Preserve completeness monitoring separately from the actionable queue.

The setup smoke run covers structured scoring, rules, findings, and report generation
with fabricated data. It does not establish SQL connectivity, embedding-model quality,
browser interaction correctness, or production-scale performance.
