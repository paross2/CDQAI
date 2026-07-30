from pathlib import Path
import logging
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
