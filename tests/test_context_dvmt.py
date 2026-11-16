# CDQAI file version: 2.5.0
from pathlib import Path
import logging
from types import SimpleNamespace
import pandas as pd
from cdqai.context.dvmt import DVMTContextManager
from cdqai.core.config import load_config
from cdqai.detectors.structured import StructuredAnomalyDetector

def test_all_annual_context_workbooks_are_present():
    root=Path(__file__).resolve().parents[1]
    years={int(p.stem[-4:]) for p in (root/'context/kentucky_dvmt/raw').glob('*.xlsx')}
    assert years == set(range(1997,2026))

def test_context_year_resolution_prefers_prior():
    manager=DVMTContextManager(load_config(), logging.getLogger('test'))
    assert manager._resolve_year(2024,[2022,2023,2025]) == (2023,'PRIOR_YEAR_FALLBACK')
    assert manager._resolve_year(1996,[1997,1998]) == (1997,'FUTURE_YEAR_FALLBACK')

def test_2025_workbook_parses_120_counties():
    root=Path(__file__).resolve().parents[1]
    path=root/'context/kentucky_dvmt/raw/Mileage and Daily Vehicle Miles Traveled - DVMT2025.xlsx'
    parsed=DVMTContextManager.parse_workbook(path)
    assert len(parsed)==120
    assert parsed.ContextYear.eq(2025).all()
    assert parsed.TotalDVMTThousands.notna().all()

def test_county_and_context_fields_excluded_from_structured_model():
    config=load_config(); detector=StructuredAnomalyDetector(config, logging.getLogger('test'))
    df=pd.DataFrame({'MFN':['1','2'],'CountyNumber':[1,2],'Speed':[10,20],'ContextTotalDVMTThousands':[100,200]})
    assert detector.select_features(df)==['Speed']


def test_crash_county_code_alias_with_older_config(monkeypatch):
    config = load_config()
    manager = DVMTContextManager(config, logging.getLogger('synthetic'))
    context = pd.DataFrame([dict(ContextYear=2025, CountyNumber=1, CountyName="Fabricated",
        UrbanRural="Rural", TotalDVMTThousands=123.0, SourceFile="fabricated.xlsx")])
    monkeypatch.setattr(manager, "load", lambda refresh=False: context)
    result, _ = manager.enrich(pd.DataFrame({"YR": [2025], "CountyCode": [1]}))
    assert result.iloc[0].ContextStatus == "USABLE"
    assert result.iloc[0].ContextTotalDVMTThousands == 123.0


def test_failed_workbook_is_retried_and_partial_context_is_not_cached(tmp_path, monkeypatch):
    raw_dir = tmp_path / "context"
    raw_dir.mkdir()
    (raw_dir / "DVMT2024.xlsx").touch()
    (raw_dir / "DVMT2025.xlsx").touch()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    config = SimpleNamespace(
        raw={"context": {"kentucky_dvmt": {"directory": "context"}}},
        project_root=tmp_path,
        cache_dir=cache_dir,
    )
    manager = DVMTContextManager(config, logging.getLogger("synthetic"))
    calls = []

    def parse(path):
        calls.append(path.name)
        if path.name == "DVMT2025.xlsx":
            raise ImportError("synthetic missing workbook dependency")
        return pd.DataFrame([{
            "ContextYear": 2024,
            "CountyNumber": 1,
            "CountyName": "Fabricated",
            "UrbanRural": "Rural",
            "TotalDVMTThousands": 123.0,
            "SourceFile": path.name,
        }])

    monkeypatch.setattr(manager, "parse_workbook", parse)

    first = manager.load()
    second = manager.load()

    assert len(first) == len(second) == 1
    assert calls.count("DVMT2025.xlsx") == 2
    assert not manager.cache_path.exists()
    assert not manager.manifest_path.exists()
