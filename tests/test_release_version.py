# CDQAI file version: 2.3.6
from pathlib import Path

import pytest

from tools.release_version import release_paths, synchronize
from tools.release_version import inventory_gaps, synchronized_text


def test_current_release_files_are_synchronized():
    root = Path(__file__).resolve().parents[1]
    assert synchronize(root, check=True) == []
    assert not list(root.glob("Release_[0-9]*.bat"))


def test_git_inventory_detects_omissions_without_reading_them(tmp_path, monkeypatch):
    from types import SimpleNamespace
    (tmp_path / "VERSION").write_text("2.3.5\n")
    (tmp_path / "release-files.txt").write_text("VERSION\n")
    (tmp_path / "release-exclusions.txt").write_text("# archived data\nexternal.xlsx\n")
    monkeypatch.setattr("tools.release_version.subprocess.run", lambda *a, **kw:
                        SimpleNamespace(stdout="VERSION\0external.xlsx\0forgotten.py\0"))
    assert inventory_gaps(tmp_path) == ["forgotten.py"]
    (tmp_path / "release-exclusions.txt").write_text("VERSION\nexternal.xlsx\nforgotten.py\n")
    assert inventory_gaps(tmp_path) == ["VERSION"]


def test_current_guides_and_readme_link_update_but_history_does_not():
    for path in ("docs/ANALYST_GUIDANCE.md", "docs/NARRATIVE_HIGHLIGHTS.md"):
        assert "Version 9.8.7" in synchronized_text(path, "Version 1.2.3\n", "1.2.3", "9.8.7")
    result = synchronized_text("README.md", "docs/RELEASE_NOTES_1.2.3.md", "1.2.3", "9.8.7")
    assert "docs/RELEASE_NOTES_9.8.7.md" in result
    result = synchronized_text("docs/RELEASE_NOTES_1.2.3.md", "Version 1.2.3\n", "1.2.3", "9.8.7")
    assert result.endswith("Version 1.2.3\n")


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
