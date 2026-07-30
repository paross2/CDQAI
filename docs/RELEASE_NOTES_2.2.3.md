# CDQAI 2.2.3 — Lightweight On-Demand Narrative Evidence

Version 2.2.3 makes complete crash narratives reliably available to analysts without embedding hundreds of thousands of narratives in `dashboard.html`.

## What changed

- `dashboard.html` remains compact and contains only the findings table and review metadata.
- Complete narratives are written to `dashboard_narratives.js`, a companion file loaded by the dashboard.
- The companion JavaScript format works when the dashboard is opened directly from Windows Explorer; it does not depend on a local web server or browser permission to fetch a `file://` JSON resource.
- Narrative text is rendered only when the analyst clicks the `+` button for a finding.
- Direct deterministic-rule phrases are highlighted in yellow.
- Embedding-only narrative findings are labeled as narrative-level statistical evidence without falsely assigning importance to individual words.
- Missing narratives are displayed as an explicit review limitation rather than a quiet blank message.
- `finding_evidence.parquet` persists the complete narrative, 500-character preview, evidence spans, evidence method, and explanation for every finding. A CSV fallback is written if Parquet support is unavailable.
- The dashboard logs the number of finding records that are missing a complete narrative.

## Files that must stay together

Keep these files in the same output folder:

- `dashboard.html`
- `dashboard_narratives.js`
- `finding_evidence.parquet` (or the CSV fallback)

Moving only `dashboard.html` will prevent narrative evidence from loading.

## Scope

This release changes report storage and analyst interaction. It does not change the anomaly models, thresholds, or finding-priority formula.
