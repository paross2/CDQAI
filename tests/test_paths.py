# CDQAI file version: 2.2.5
from cdqai.core.paths import find_project_root

def test_project_root_found():
    root = find_project_root()
    assert (root / "pyproject.toml").exists()
