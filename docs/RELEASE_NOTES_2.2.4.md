# CDQAI 2.2.4 — Reliable Narrative MFN Matching

Version 2.2.4 fixes a narrative lookup defect in 2.2.3. Finding MFNs and source-data MFNs are now canonicalized before joining, so values such as `12345`, `12345.0`, and numeric 12345 resolve to the same record. When duplicate narrative rows exist, CDQAI retains the longest nonblank narrative. The dashboard continues to load complete narratives on demand from `dashboard_narratives.js`.
