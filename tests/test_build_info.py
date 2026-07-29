from pathlib import Path

from cdqai.core import build_info

def test_release_metadata():
    assert build_info.VERSION == "2.1.1"
    assert build_info.RELEASE_NAME == "Build Metadata & Provenance"
    assert build_info.LEAD_DEVELOPER == "Paul Ross"
    assert build_info.CONTRIBUTING_DEVELOPER == "Nathaniel Swallom"
    assert "OpenAI ChatGPT" in build_info.AI_ATTRIBUTION
    assert "Section 405(c)" in build_info.FUNDING_ACKNOWLEDGMENT

def test_package_versions_are_reported():
    versions = build_info.package_versions(("pytest", "package-that-does-not-exist-cdqai"))
    assert versions["pytest"] != "not installed"
    assert versions["package-that-does-not-exist-cdqai"] == "not installed"

def test_current_release_files_do_not_use_stale_version():
    root = Path(__file__).resolve().parents[1]
    current_files = [
        root / "README.md", root / "GIT_SETUP.md", root / "VERSION", root / "pyproject.toml",
        root / "config/config.yaml", root / "config/config.example.yaml", root / "cdqai/main.py",
        root / "Run_CDQAI_2.1.1.bat", root / "INSTALL_VERSION_2.1.1.txt"
    ]
    for path in current_files:
        text = path.read_text(encoding="utf-8")
        assert "2.0.2" not in text, path
        assert "2.1.0" not in text, path
