import pandas as pd
from cdqai.reports.dashboard_report import _canonical_mfn, _build_narrative_lookup
from cdqai.data.dataset import CrashDataset, DatasetMetadata
from datetime import datetime


def _metadata():
    return DatasetMetadata(datetime.now(), 0, 0, 0, 0, 0, 0, 0, 0, 0.0)


def test_canonical_mfn_matches_float_and_integer_forms():
    assert _canonical_mfn(12345) == "12345"
    assert _canonical_mfn(12345.0) == "12345"
    assert _canonical_mfn("12345.0") == "12345"
    assert _canonical_mfn(" 12345 ") == "12345"


def test_narrative_lookup_uses_longest_nonblank_duplicate():
    merged = pd.DataFrame({
        "MFN": [12345.0, "12345", "67890"],
        "NarrativeTxt": ["", "Complete narrative text", "Second narrative"],
    })
    ds = CrashDataset(pd.DataFrame(), pd.DataFrame(), merged, _metadata())
    lookup = _build_narrative_lookup(ds, "MFN", "NarrativeTxt")
    assert lookup["12345"] == "Complete narrative text"
    assert lookup["67890"] == "Second narrative"
