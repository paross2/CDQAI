# CDQAI file version: 2.3.5
"""Optional Rec03 severity review; never substitutes for Rec01 KABCO."""
from __future__ import annotations

import re
import pandas as pd

from cdqai.evidence.objects import Evidence
from cdqai.evidence.severity import Severity
from cdqai.kentucky.records import RecordType
from cdqai.kentucky.quality import QualityCharacteristic
from cdqai.kentucky.systems import TrafficRecordSystem

INJURY_CODES = {"1": "K", "2": "A", "3": "B", "4": "C", "5": "O"}
ORDER = {"O": 0, "C": 1, "B": 2, "A": 3, "K": 4}


def key(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    if re.fullmatch(r"\d+\.0", value):
        value = value[:-2]
    return value


def injury_code(value):
    value = key(value)
    return value.lstrip("0") or "0" if value else ""


def quoted_table(value):
    parts = str(value).split(".")
    if len(parts) != 3 or any(not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", p) for p in parts):
        raise ValueError("person_severity.table requires database.schema.table identifiers.")
    return ".".join(f"[{p}]" for p in parts)


def attach_person_severity(dataset, config, logger, db=None):
    cfg = config.raw.get("person_severity", {})
    if cfg.get("enabled") is not True:
        return dataset
    from cdqai.data.database import DatabaseManager
    db = db or DatabaseManager(config, logger)
    # Explicit projection: no names, addresses, birth dates, or license numbers.
    query = ("SELECT [Master File], [Unit Number], [Person Number], [Injury Severity], [YR] FROM "
             + quoted_table(cfg.get("table", "")))
    persons = pd.read_sql(query, db.engine)
    dataset.person_severity_review = review_person_severity(dataset.merged, persons, config)
    logger.info("Person severity review prepared; Rec01 priority severity retained.")
    return dataset


def review_person_severity(crashes, persons, config):
    required = ["Master File", "Unit Number", "Person Number", "Injury Severity", "YR"]
    if any(c not in persons for c in required):
        raise ValueError("Rec03 severity review is missing required schema fields.")
    mfn = config.raw["fields"]["normalized_mfn_field"]
    if any(c not in crashes for c in [mfn, "YR", "KABCO"]):
        raise ValueError("Severity review requires crash identifier, YR, and KABCO.")
    p = persons[required].copy()
    p["_mfn"] = p["Master File"].map(key)
    p["_year"] = p["YR"].map(key)
    p["_unit"] = p["Unit Number"].map(key)
    p["_person"] = p["Person Number"].map(key)
    p["_code"] = p["Injury Severity"].map(injury_code)
    p["_duplicate"] = p.duplicated(["_mfn", "_year", "_unit", "_person"], keep=False)
    groups = {k: g for k, g in p.groupby(["_mfn", "_year"], sort=False) if all(k)}
    rows = []
    for _, crash in crashes[[mfn, "YR", "KABCO"]].drop_duplicates().iterrows():
        group = groups.get((key(crash[mfn]), key(crash["YR"])))
        reported = key(crash["KABCO"]).upper()
        known = [] if group is None else [INJURY_CODES[c] for c in group["_code"] if c in INJURY_CODES]
        highest = max(known, key=ORDER.get) if known else ""
        reconciled = 0 if group is None else int(group["_code"].eq("9").sum())
        unresolved = 0 if group is None else int((~group["_code"].isin(INJURY_CODES)).sum())
        bad_keys = False if group is None else bool((group["_duplicate"] | group["_unit"].eq("") | group["_person"].eq("")).any())
        complete = group is not None and unresolved == 0 and not bad_keys
        # A known higher injury establishes a discrepancy even when other persons are unresolved.
        conflict = bool(reported in ORDER and highest and not bad_keys and
                        (ORDER[highest] > ORDER[reported] or (complete and highest != reported)))
        status = ("No matched persons" if group is None else "Invalid person keys" if bad_keys else
                  "Unresolved person severity" if unresolved else "Comparable")
        rows.append({"MFN": key(crash[mfn]), "YR": key(crash["YR"]), "Rec01KABCO": reported,
                     "HighestKnownPersonSeverity": highest, "PersonSeverityResolved": complete,
                     "Reconciliation09Count": reconciled, "UnresolvedPersonCount": unresolved,
                     "SeverityReviewStatus": status, "SeverityDiscrepancy": conflict})
    return pd.DataFrame(rows, columns=["MFN", "YR", "Rec01KABCO", "HighestKnownPersonSeverity",
        "PersonSeverityResolved", "Reconciliation09Count", "UnresolvedPersonCount",
        "SeverityReviewStatus", "SeverityDiscrepancy"])


def severity_evidence(review):
    if review is None or review.empty:
        return []
    items = []
    for row in review.to_dict("records"):
        if not row["SeverityDiscrepancy"]:
            continue
        items.append(Evidence(row["MFN"], RecordType.REC03, TrafficRecordSystem.CRASH,
            QualityCharacteristic.ACCURACY, "Crash/Person Severity Conflict", Severity.MEDIUM, 0.95,
            f"Rec01 KABCO is {row['Rec01KABCO']}; highest known Rec03 injury severity is "
            f"{row['HighestKnownPersonSeverity']}. Review source coding and reconciliation history. "
            "Code 09 remains unresolved; Rec01 KABCO still controls crash-priority weighting.",
            "REC03_SEVERITY_REVIEW", ["KABCO", "Injury Severity"], row))
    return items
