from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ContextSummary:
    enabled: bool
    available_years: tuple[int, ...] = ()
    exact_records: int = 0
    prior_fallback_records: int = 0
    future_fallback_records: int = 0
    unavailable_records: int = 0
    stale_records: int = 0
    maximum_year_gap: int = 0

    def to_dict(self) -> dict:
        value = asdict(self)
        value["available_years"] = list(self.available_years)
        return value


class DVMTContextManager:
    """Load, normalize, select, and attach annual county DVMT context."""

    DERIVED_COLUMNS = (
        "ContextRequestedYear", "ContextUsedYear", "ContextYearGap",
        "ContextMatchType", "ContextStatus", "ContextSourceFile",
        "ContextCountyNumber", "ContextCountyName", "ContextUrbanRural",
        "ContextTotalDVMTThousands",
    )

    def __init__(self, config, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self.cfg = config.raw.get("context", {}).get("kentucky_dvmt", {})
        directory = self.cfg.get("directory", "context/kentucky_dvmt/raw")
        self.raw_dir = config.project_root / directory
        cache_name = self.cfg.get("normalized_cache_file", "kentucky_county_dvmt.parquet")
        self.cache_path = config.cache_dir / cache_name
        self.fallback_cache_path = self.cache_path.with_suffix(".pkl")
        self.manifest_path = config.cache_dir / "kentucky_county_dvmt_sources.json"

    @property
    def enabled(self) -> bool:
        return bool(self.cfg.get("enabled", True))

    def source_files(self) -> list[Path]:
        if not self.raw_dir.exists():
            return []
        return sorted(self.raw_dir.glob("*.xlsx"))

    @staticmethod
    def year_from_path(path: Path) -> int:
        match = re.search(r"(?:19|20)\d{2}", path.name)
        if not match:
            raise ValueError(f"Context workbook filename does not contain a year: {path.name}")
        return int(match.group(0))

    def _inventory_signature(self, files: list[Path]) -> str:
        digest = hashlib.sha256()
        for path in files:
            stat = path.stat()
            digest.update(f"{path.name}|{stat.st_size}|{stat.st_mtime_ns}".encode())
        return digest.hexdigest()

    @staticmethod
    def _find_header(raw: pd.DataFrame) -> tuple[int, int]:
        for row_index in range(min(20, len(raw))):
            values = raw.iloc[row_index].astype(str).str.strip().str.lower()
            matches = np.flatnonzero(values.eq("county").to_numpy())
            if len(matches):
                return row_index, int(matches[0])
        raise ValueError("Could not locate County header in DVMT workbook.")

    @classmethod
    def parse_workbook(cls, path: Path) -> pd.DataFrame:
        year = cls.year_from_path(path)
        raw = pd.read_excel(path, header=None)
        header_row, county_col = cls._find_header(raw)
        header = raw.iloc[header_row].fillna("").astype(str).str.strip()
        number_col = county_col - 1

        # Total county DVMT appears immediately after County, or after an urban/rural descriptor.
        candidates = []
        for col in range(county_col + 1, min(county_col + 5, raw.shape[1])):
            label = header.iloc[col].lower()
            if "total" in label or "tot." in label or "dvmt" in label:
                candidates.append(col)
        total_col = candidates[0] if candidates else county_col + 1
        urban_col = county_col + 1 if total_col > county_col + 1 else None

        body = raw.iloc[header_row + 1:].copy()
        county_number = pd.to_numeric(body.iloc[:, number_col], errors="coerce")
        mask = county_number.between(1, 120)
        body = body.loc[mask]
        county_number = county_number.loc[mask].astype(int)
        result = pd.DataFrame({
            "ContextYear": year,
            "CountyNumber": county_number.to_numpy(),
            "CountyName": body.iloc[:, county_col].fillna("").astype(str).str.strip().to_numpy(),
            "UrbanRural": (body.iloc[:, urban_col].fillna("").astype(str).str.strip().to_numpy() if urban_col is not None else ""),
            "TotalDVMTThousands": pd.to_numeric(body.iloc[:, total_col], errors="coerce").to_numpy(),
            "SourceFile": path.name,
        })
        result = result[result["CountyName"].ne("")].drop_duplicates(["ContextYear", "CountyNumber"])
        if len(result) < 100:
            raise ValueError(f"Only {len(result)} county rows parsed from {path.name}; expected approximately 120.")
        return result

    def load(self, refresh: bool = False) -> pd.DataFrame:
        files = self.source_files()
        if not files:
            self.logger.warning("No DVMT context workbooks found in %s.", self.raw_dir)
            return pd.DataFrame()
        signature = self._inventory_signature(files)
        if not refresh and self.cache_path.exists() and self.manifest_path.exists():
            try:
                manifest = pd.read_json(self.manifest_path, typ="series")
                if manifest.get("signature") == signature:
                    try:
                        return pd.read_parquet(self.cache_path)
                    except Exception:
                        if self.fallback_cache_path.exists():
                            return pd.read_pickle(self.fallback_cache_path)
                        raise
            except Exception:
                self.logger.warning("DVMT context cache could not be reused; rebuilding.")
        frames = []
        for path in files:
            try:
                frames.append(self.parse_workbook(path))
            except Exception as exc:
                self.logger.warning("Skipping context workbook %s: %s", path.name, exc)
        if not frames:
            return pd.DataFrame()
        context = pd.concat(frames, ignore_index=True).sort_values(["ContextYear", "CountyNumber"])
        try:
            context.to_parquet(self.cache_path, index=False)
        except ImportError:
            self.logger.warning("Parquet engine unavailable; using pickle for DVMT context cache.")
            context.to_pickle(self.fallback_cache_path)
        self.manifest_path.write_text(pd.Series({"signature": signature, "files": len(files)}).to_json(indent=2), encoding="utf-8")
        return context

    def _resolve_year(self, requested: int, available: list[int]) -> tuple[int | None, str]:
        if requested in available:
            return requested, "EXACT"
        prior = [year for year in available if year < requested]
        if prior:
            return max(prior), "PRIOR_YEAR_FALLBACK"
        if bool(self.cfg.get("allow_future_fallback", True)):
            future = [year for year in available if year > requested]
            if future:
                return min(future), "FUTURE_YEAR_FALLBACK"
        return None, "UNAVAILABLE"

    @staticmethod
    def _first_existing(columns: pd.Index, candidates: list[str]) -> str | None:
        lookup = {str(column).lower(): str(column) for column in columns}
        for candidate in candidates:
            if candidate.lower() in lookup:
                return lookup[candidate.lower()]
        return None

    def enrich(self, df: pd.DataFrame, refresh: bool = False) -> tuple[pd.DataFrame, ContextSummary]:
        if not self.enabled:
            return df, ContextSummary(enabled=False)
        context = self.load(refresh=refresh)
        if context.empty:
            out = df.copy()
            for column in self.DERIVED_COLUMNS:
                out[column] = np.nan
            out["ContextMatchType"] = "UNAVAILABLE"
            out["ContextStatus"] = "UNAVAILABLE"
            return out, ContextSummary(enabled=True, unavailable_records=len(out))

        fields = self.cfg.get("fields", {})
        year_candidates = fields.get("year_candidates", ["CrashYear", "YR", "Year", "Crash_Year"])
        county_candidates = fields.get("county_candidates", ["CountyNumber", "County_Number", "CountyNo", "COUNTY", "CNTY"])
        year_col = self._first_existing(df.columns, year_candidates)
        county_col = self._first_existing(df.columns, county_candidates)
        out = df.copy()
        if year_col is None or county_col is None:
            self.logger.warning("DVMT context not attached: year or county field was not found.")
            for column in self.DERIVED_COLUMNS:
                out[column] = np.nan
            out["ContextMatchType"] = "UNAVAILABLE"
            out["ContextStatus"] = "MISSING_JOIN_FIELDS"
            return out, ContextSummary(enabled=True, available_years=tuple(sorted(context.ContextYear.unique())), unavailable_records=len(out))

        requested_years = pd.to_numeric(out[year_col], errors="coerce").astype("Int64")
        counties = pd.to_numeric(out[county_col], errors="coerce").astype("Int64")
        available = sorted(int(x) for x in context.ContextYear.unique())
        mapping = {int(year): self._resolve_year(int(year), available) for year in requested_years.dropna().unique()}
        used_year = requested_years.map(lambda value: mapping.get(int(value), (None, "UNAVAILABLE"))[0] if pd.notna(value) else None).astype("Int64")
        match_type = requested_years.map(lambda value: mapping.get(int(value), (None, "UNAVAILABLE"))[1] if pd.notna(value) else "UNAVAILABLE")

        out["ContextRequestedYear"] = requested_years
        out["ContextUsedYear"] = used_year
        out["ContextYearGap"] = (requested_years - used_year).abs().astype("Int64")
        out["ContextMatchType"] = match_type
        out["ContextCountyNumber"] = counties
        joined = out.merge(
            context.rename(columns={
                "CountyNumber": "ContextCountyNumber",
                "ContextYear": "ContextUsedYear",
                "CountyName": "ContextCountyName",
                "UrbanRural": "ContextUrbanRural",
                "TotalDVMTThousands": "ContextTotalDVMTThousands",
                "SourceFile": "ContextSourceFile",
            }),
            on=["ContextUsedYear", "ContextCountyNumber"], how="left", suffixes=("", "_lookup")
        )
        max_gap = int(self.cfg.get("maximum_year_gap", 3))
        joined["ContextStatus"] = np.where(
            joined["ContextCountyName"].isna(), "UNAVAILABLE",
            np.where(joined["ContextYearGap"].fillna(max_gap + 1) > max_gap, "STALE", "USABLE")
        )
        counts = joined["ContextMatchType"].value_counts()
        summary = ContextSummary(
            enabled=True,
            available_years=tuple(available),
            exact_records=int(counts.get("EXACT", 0)),
            prior_fallback_records=int(counts.get("PRIOR_YEAR_FALLBACK", 0)),
            future_fallback_records=int(counts.get("FUTURE_YEAR_FALLBACK", 0)),
            unavailable_records=int((joined["ContextStatus"] == "UNAVAILABLE").sum()),
            stale_records=int((joined["ContextStatus"] == "STALE").sum()),
            maximum_year_gap=int(joined["ContextYearGap"].dropna().max()) if joined["ContextYearGap"].notna().any() else 0,
        )
        self.logger.info("DVMT context attached: exact=%s prior=%s future=%s unavailable=%s.", summary.exact_records, summary.prior_fallback_records, summary.future_fallback_records, summary.unavailable_records)
        return joined, summary
