from __future__ import annotations
import logging
import pandas as pd
from cdqai.core.config import CDQAIConfig
from cdqai.data.dataset import CrashDataset
from cdqai.findings.finding import Finding

YEAR_CANDIDATES = (
    "CrashYear",
    "Year",
    "YEAR",
    "CRASH_YEAR",
    "Crash_Year",
    "YR",
)

DATE_CANDIDATES = (
    "CollisionDate",
    "CrashDate",
    "CRASH_DATE",
    "Collision_Date",
)


def _year_map(dataset: CrashDataset, config: CDQAIConfig) -> pd.DataFrame:
    """Create a unique MFN-to-CrashYear lookup.

    Preference order:
    1. A recognized explicit year field.
    2. A year derived from a recognized collision-date field.
    3. An empty lookup if neither is available.
    """
    mfn = config.raw["fields"]["normalized_mfn_field"]
    merged = dataset.merged

    if mfn not in merged.columns:
        raise KeyError(
            f"Normalized MFN field '{mfn}' was not found in the merged dataset."
        )

    year_column = next(
        (column for column in YEAR_CANDIDATES if column in merged.columns),
        None,
    )
    date_column = next(
        (column for column in DATE_CANDIDATES if column in merged.columns),
        None,
    )

    if not year_column and not date_column:
        return pd.DataFrame(columns=[mfn, "CrashYear"])

    out = merged[[mfn]].copy()
    out["CrashYear"] = pd.Series(pd.NA, index=out.index, dtype="Int64")

    if year_column:
        out["CrashYear"] = (
            pd.to_numeric(merged[year_column], errors="coerce")
            .round()
            .astype("Int64")
        )

    if date_column:
        raw_date = merged[date_column].astype("string").str.strip()

        parsed_date = pd.to_datetime(
            raw_date,
            format="%Y%m%d",
            errors="coerce",
        )

        unresolved = parsed_date.isna()
        if unresolved.any():
            parsed_date.loc[unresolved] = pd.to_datetime(
                raw_date.loc[unresolved],
                errors="coerce",
            )

        date_year = parsed_date.dt.year.astype("Int64")
        out["CrashYear"] = out["CrashYear"].fillna(date_year)

    current_year = pd.Timestamp.now().year
    valid_year = out["CrashYear"].between(
        1900,
        current_year + 1,
        inclusive="both",
    )
    out.loc[~valid_year.fillna(False), "CrashYear"] = pd.NA

    return (
        out.dropna(subset=[mfn])
        .drop_duplicates(subset=[mfn], keep="first")
        [[mfn, "CrashYear"]]
    )

def findings_dataframe(findings: list[Finding], dataset: CrashDataset, config: CDQAIConfig) -> pd.DataFrame:
    df = pd.DataFrame([x.to_dict() for x in findings])
    if df.empty:
        return df
    return df.merge(_year_map(dataset, config), on="MFN", how="left")

def write_finding_outputs(findings: list[Finding], dataset: CrashDataset, config: CDQAIConfig, logger: logging.Logger) -> None:
    outputs = config.raw.get("outputs", {})
    df = findings_dataframe(findings, dataset, config)
    actionable_ids = {x.mfn for x in findings if x.actionable}
    actionable = df[df["MFN"].isin(actionable_ids)].copy() if not df.empty else df.copy()
    top = actionable.head(int(outputs.get("top_findings_rows", 100)))
    df.to_csv(config.outputs_dir / outputs.get("findings_file", "findings.csv"), index=False)
    actionable.to_csv(config.outputs_dir / outputs.get("actionable_findings_file", "actionable_findings.csv"), index=False)
    top.to_csv(config.outputs_dir / outputs.get("top_findings_file", "top_findings.csv"), index=False)
    if df.empty:
        summary = pd.DataFrame(columns=["FindingType", "PriorityLevel", "FindingCount"])
    else:
        summary = df.groupby(["FindingType", "PriorityLevel"], dropna=False).size().reset_index(name="FindingCount")
    summary.to_csv(config.outputs_dir / outputs.get("findings_summary_file", "findings_summary.csv"), index=False)
    if "CrashYear" in actionable.columns and not actionable.empty:
        annual = actionable.groupby("CrashYear").agg(
            ActionableFindings=("MFN", "count"),
            HighPriorityFindings=("PriorityLevel", lambda s: int((s == "High").sum())),
            CriticalPriorityFindings=("PriorityLevel", lambda s: int((s == "Critical").sum())),
            ConsistencyFindings=("FindingType", lambda s: int((s == "Consistency").sum())),
            AnomalyFindings=("FindingType", lambda s: int((s == "Anomaly").sum())),
            MultiSignalFindings=("FindingType", lambda s: int((s == "Multi-Signal").sum())),
        ).reset_index()
    else:
        annual = pd.DataFrame(columns=["CrashYear","ActionableFindings","HighPriorityFindings","CriticalPriorityFindings","ConsistencyFindings","AnomalyFindings","MultiSignalFindings"])
    annual.to_csv(config.outputs_dir / outputs.get("annual_findings_file", "annual_findings.csv"), index=False)
    logger.info("Finding outputs written: %s total; %s actionable.", len(df), len(actionable))