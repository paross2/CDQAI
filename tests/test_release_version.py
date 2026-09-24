# CDQAI file version: 2.2.5
from pathlib import Path

import pytest

from tools.release_version import release_paths, synchronize


def test_current_release_files_are_synchronized():
    root = Path(__file__).resolve().parents[1]
    assert synchronize(root, check=True) == []
    assert not list(root.glob("Release_[0-9]*.bat"))


def test_release_update_is_repeatable_and_preserves_history(tmp_path):
    (tmp_path / "VERSION").write_text("2.2.5\n")
    (tmp_path / "release-files.txt").write_text("VERSION\nREADME.md\nLICENSE\nrequirements.txt\nrelease-files.txt\n")
    (tmp_path / "README.md").write_text("# CDQAI\nVersion 2.2.5\n")
    license_body = "MIT License\nCopyright example\nPermission example\n"
    (tmp_path / "LICENSE").write_text(license_body)
    (tmp_path / "requirements.txt").write_text("example-package>=1.2.0\n")
    (tmp_path / "historical.md").write_text("Version 1.0.0\n")
    synchronize(tmp_path, version="2.3.0")
    assert synchronize(tmp_path, check=True) == []
    assert synchronize(tmp_path) == []
    assert "Version 2.3.0" in (tmp_path / "README.md").read_text()
    assert (tmp_path / "LICENSE").read_text().endswith(license_body)
    assert "example-package>=1.2.0" in (tmp_path / "requirements.txt").read_text()
    assert (tmp_path / "historical.md").read_text() == "Version 1.0.0\n"


@pytest.mark.parametrize("relative", [
    "config/config.yaml", "outputs/findings.csv", "cache/private.txt",
    "context/kentucky_dvmt/raw/input.xlsx", "../private.txt", ".env", "C:/private.txt",
])
def test_private_inputs_cannot_enter_release_inventory(tmp_path, relative):
    (tmp_path / "release-files.txt").write_text(relative + "\n")
    with pytest.raises(ValueError):
        release_paths(tmp_path)


def test_check_detects_stale_metadata_without_writing(tmp_path):
    (tmp_path / "VERSION").write_text("2.2.5\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "2.0.0"\n')
    (tmp_path / "release-files.txt").write_text("VERSION\npyproject.toml\nrelease-files.txt\n")
    before = (tmp_path / "pyproject.toml").read_text()
    assert "pyproject.toml" in synchronize(tmp_path, check=True)
    assert (tmp_path / "pyproject.toml").read_text() == before
