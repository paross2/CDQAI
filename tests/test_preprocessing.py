import pandas as pd
from cdqai.data.preprocessing import normalize_mfn

def test_normalize_mfn_strips_whitespace():
    df = pd.DataFrame({"MFN": [" 123 ", 456]})
    out = normalize_mfn(df, "MFN")
    assert out["MFN"].tolist() == ["123", "456"]
