from pathlib import Path

from cdqai.core import build_info

def test_release_metadata():
    assert build_info.VERSION == "2.2.4"
    assert build_info.RELEASE_NAME == "Transparent Narrative Evidence"
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
        root / "Run_CDQAI.bat", root / "INSTALL.txt"
    ]
    for path in current_files:
        text = path.read_text(encoding="utf-8")
        assert "2.0.2" not in text, path
        assert "2.1.0" not in text, path


def test_ai_stack_packages_are_reported():
    for package in ("sentence-transformers", "transformers", "huggingface-hub", "torch", "tokenizers"):
        assert package in build_info.CORE_PACKAGES


def test_source_archive_metadata_is_explicit(tmp_path):
    info = build_info.collect_build_info(tmp_path)
    assert info["git_branch"]
    assert info["git_commit"] != "unknown"
    assert info["git_tag"]
    assert info["repository"] == "https://github.com/paross2/CDQAI"
