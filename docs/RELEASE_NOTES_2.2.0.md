# CDQAI Version 2.2.0 — Context-Aware Analysis

Version 2.2.0 adds county-level roadway exposure and geographic context to CDQAI while preserving the principle that findings are evidence for human review, not declarations of error.

## Included context

The release contains annual Kentucky county-level Mileage and Daily Vehicle Miles Traveled workbooks for 1997–2025. CDQAI normalizes the workbooks and caches a unified Parquet table.

## Matching policy

1. Use the crash's exact context year when available.
2. Otherwise use the nearest preceding year.
3. If no preceding year exists and future fallback is enabled, use the nearest later year.
4. Continue without context rather than terminate when context cannot be attached.

Every attached record retains the requested year, selected year, absolute gap, match type, status, county, urban/rural designation, DVMT, and source filename.

## Modeling safeguard

County Number is used as a join/grouping key and is excluded from the global structured anomaly model by default. Derived context and provenance fields are also excluded. This prevents low-volume counties or numeric county codes from becoming anomaly signals merely because they are uncommon.

## Annual maintenance

Add the newest official KYTC workbook to `context/kentucky_dvmt/raw/` annually. The health and run outputs disclose fallback and stale-context use.
