from __future__ import annotations
import logging, urllib.parse
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from cdqai.core.config import CDQAIConfig
class DatabaseManager:
    def __init__(self, config: CDQAIConfig, logger: logging.Logger) -> None:
        self.config=config; self.logger=logger; self._engine: Engine | None = None
    @property
    def engine(self) -> Engine:
        if self._engine is None: self._engine = self._build_engine()
        return self._engine
    def _build_engine(self) -> Engine:
        db=self.config.raw["database"]; trusted="yes" if db.get("trusted_connection", True) else "no"
        conn_str=f"Driver={{{db['driver']}}};Server={db['server']};Trusted_Connection={trusted};"
        self.logger.info("Creating SQL Server engine for server: %s", db["server"])
        return create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}")
    def test_connection(self) -> None:
        with self.engine.connect() as conn: conn.execute(text("SELECT 1"))
        self.logger.info("SQL Server connection test succeeded.")
    def load_crashes(self) -> pd.DataFrame:
        table=self.config.raw["tables"]["crash_table"]; crash_mfn=self.config.raw["fields"]["crash_mfn_field"]; normalized_mfn=self.config.raw["fields"]["normalized_mfn_field"]
        self.logger.info("Loading crash table: %s", table); df=pd.read_sql(f"SELECT * FROM {table}", self.engine); df.rename(columns=lambda col: col.strip(), inplace=True)
        if crash_mfn in df.columns and crash_mfn != normalized_mfn: df.rename(columns={crash_mfn: normalized_mfn}, inplace=True)
        if normalized_mfn not in df.columns: raise KeyError(f"Crash data missing expected MFN field: {normalized_mfn}")
        self.logger.info("Crash records loaded: %s", f"{len(df):,}"); return df
    def load_narratives(self) -> pd.DataFrame:
        table=self.config.raw["tables"]["narrative_table"]; mfn=self.config.raw["fields"]["normalized_mfn_field"]; narrative=self.config.raw["fields"]["narrative_text_field"]
        self.logger.info("Loading narrative table: %s", table); df=pd.read_sql(f"SELECT {mfn}, {narrative} FROM {table}", self.engine); df.rename(columns=lambda col: col.strip(), inplace=True)
        if mfn not in df.columns: raise KeyError(f"Narrative data missing expected MFN field: {mfn}")
        if narrative not in df.columns: raise KeyError(f"Narrative data missing expected text field: {narrative}")
        self.logger.info("Narrative records loaded: %s", f"{len(df):,}"); return df
