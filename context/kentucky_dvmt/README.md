# Kentucky DVMT and Mileage Context

This directory contains annual Kentucky Transportation Cabinet county-level mileage and Daily Vehicle Miles Traveled (DVMT) workbooks. Version 2.2.0 includes 1997–2025.

## Annual maintenance

Add the newest official workbook to `raw/` each year. The filename must contain a four-digit year. CDQAI rebuilds its normalized context cache when the raw source inventory changes.

## Year matching

For each crash, CDQAI uses the exact context year when available. Otherwise it uses the closest prior year. If no prior year exists, it may use the closest future year. The selected year, gap, match type, and source file are retained in the analytical dataset and run outputs.

County Number is a join and grouping key. It is excluded from global Isolation Forest scoring by default. DVMT and roadway context describe exposure and comparison context; they are not interpreted as proof that an individual crash record is erroneous.

Source: Kentucky Transportation Cabinet, Division of Planning, Roadway Information and Data.
