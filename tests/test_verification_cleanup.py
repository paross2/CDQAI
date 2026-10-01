# CDQAI file version: 2.3.6
from pathlib import Path
import pytest
from tools.verify_release import verification_workspace


@pytest.mark.parametrize("fails", [False, True])
def test_workspace_removes_only_its_owned_files(tmp_path, fails):
    (tmp_path / "release-files.txt").write_text("VERSION\n")
    (tmp_path / "VERSION").write_text("2.3.5\n")
    (tmp_path / "config").mkdir()
    private = tmp_path / "config/config.yaml"
    private.write_text("synthetic private sentinel")
    workspace = None
    try:
        with verification_workspace(tmp_path) as workspace:
            assert (workspace / "VERSION").is_file()
            assert not (workspace / "config/config.yaml").exists()
            (workspace / "temporary-result.txt").write_text("synthetic")
            if fails:
                raise RuntimeError("synthetic failure")
    except RuntimeError:
        assert fails
    assert workspace is not None and not workspace.exists()
    assert private.read_text() == "synthetic private sentinel"
