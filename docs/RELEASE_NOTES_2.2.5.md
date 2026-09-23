# CDQAI 2.2.5 - Local Setup and Synthetic Validation

This maintenance release makes it easier to set up CDQAI and verify its basic
operation before an authorized user runs it on protected data.

## Changes

- Added `python -m cdqai.main --smoke-test`: 128 fabricated records exercise
  structured scoring, deterministic rules, findings, and report generation.
  It ignores private configuration, SQL, existing crash caches, and narrative
  embedding models. Results go to `outputs/smoke/`.
- Deferred narrative-model imports until narrative scoring is enabled.
- Added development requirements including pytest, a beginner `How To Run.txt`,
  local development instructions, and publication checks.
- Removed the release test's dependency on the deliberately ignored private config.
- Corrected setup documentation, structured-model descriptions, and version metadata.
- Recorded follow-up priorities: MFN merge consistency, embedding cache validation,
  evidence dependence, and more specific analyst evidence.

The existing production scoring weights, evidence thresholds, and rules are
unchanged. This release does not implement the follow-up analytical features.
Machine-specific VS Code settings remain local and are not part of the release.

## Upgrade and run

Preserve the existing `config/config.yaml`, approved local data, and caches.
Update source files, then install dependencies in the project environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m cdqai.main --smoke-test
```

Have the project owner arrange any necessary package/model downloads within the
approved environment. The smoke dashboard is `outputs/smoke/dashboard.html`.
For an authorized real-data run, follow `How To Run.txt` and run `Run_CDQAI.bat`
locally. Do not use the historical `Release_2.2.4.bat` to publish this version.

Private configuration can retain its old project version: application identity
comes from the source code and overrides stale local metadata.

## Validation and privacy

Release verification uses a separate source-only directory, placeholder
configuration, and fabricated test fixtures: **34 passed, 2 deselected**. The
standalone synthetic smoke command also completed successfully. The two workbook-dependent tests
are excluded so verification does not open local input workbooks. A synthetic
smoke run exercises reports without reading protected inputs or existing outputs.

SQL connectivity, real-data output quality, semantic embedding execution, and
production-scale performance require authorized local review by the user.
Do not upload protected inputs, configuration, reports, logs, or screenshots to
OpenAI, GitHub, or any unapproved service. Only reviewed source and sanitized
documentation belong in this release.
