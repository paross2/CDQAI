from __future__ import annotations

import importlib.metadata
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_NAME = "Crash Data Quality Artificial Intelligence"
SHORT_NAME = "CDQAI"
VERSION = "2.1.2"
RELEASE_NAME = "Collapsible Dashboard & Findings Explorer"

LEAD_DEVELOPER = "Paul Ross"
LEAD_TITLE = "Research Scientist Principal"
CONTRIBUTING_DEVELOPER = "Nathaniel Swallom"
CONTRIBUTOR_TITLE = "Research Scientist"
ORGANIZATION = "Kentucky Transportation Center"
INSTITUTION = "University of Kentucky"

SOFTWARE_LICENSE = "MIT License"
DOCUMENTATION_LICENSE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"

AI_ATTRIBUTION = (
    "This software was developed by Paul Ross, with contributions from Nathaniel Swallom, "
    "and with the assistance of OpenAI ChatGPT. ChatGPT was used as an engineering and "
    "documentation aid. Human review, software architecture, algorithm selection, validation, "
    "testing, and final implementation remain under the direction and responsibility of the lead developer."
)

FUNDING_ACKNOWLEDGMENT = (
    "Development of the Crash Data Quality Artificial Intelligence (CDQAI) software was supported "
    "through Federal Traffic Safety Information Systems (Section 405(c)) grant funding administered "
    "by the Kentucky Office of Highway Safety (KOHS) under the Kentucky Transportation Cabinet (KYTC)."
)

DISCLAIMER = (
    "The findings, conclusions, and software presented herein are those of the authors and do not "
    "necessarily represent the official views or policies of the Kentucky Transportation Center, "
    "the University of Kentucky, the Kentucky Office of Highway Safety, the Kentucky Transportation "
    "Cabinet, or the United States Department of Transportation."
)

CORE_PACKAGES = (
    "PyYAML", "pandas", "numpy", "SQLAlchemy", "pyodbc", "tqdm", "pyarrow",
    "scikit-learn", "sentence-transformers",
)

def package_versions(packages: tuple[str, ...] = CORE_PACKAGES) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in packages:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not installed"
    return versions

def _git_value(project_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=project_root, stderr=subprocess.DEVNULL, text=True, timeout=2
        ).strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"

def collect_build_info(project_root: Path) -> dict[str, object]:
    return {
        "project": PROJECT_NAME,
        "short_name": SHORT_NAME,
        "version": VERSION,
        "release_name": RELEASE_NAME,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "operating_system": platform.platform(),
        "architecture": platform.machine(),
        "git_branch": _git_value(project_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "git_commit": _git_value(project_root, "rev-parse", "--short", "HEAD"),
        "git_tag": _git_value(project_root, "describe", "--tags", "--exact-match"),
        "packages": package_versions(),
    }
