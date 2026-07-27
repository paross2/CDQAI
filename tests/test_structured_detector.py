import numpy as np
from cdqai.detectors.structured import percentile_rank

def test_percentile_rank_shape():
    values = np.array([1.0, 2.0, 3.0])
    ranked = percentile_rank(values)
    assert ranked.shape == values.shape
    assert ranked.max() == 100.0
