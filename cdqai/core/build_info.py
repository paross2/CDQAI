from __future__ import annotations

import importlib.metadata
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_NAME = "Crash Data Quality Artificial Intelligence"
SHORT_NAME = "CDQAI"
VERSION = "2.2.4"
RELEASE_NAME = "Transparent Narrative Evidence"
REPOSITORY_URL = "https://github.com/paross2/CDQAI"
DEFAULT_BRANCH = "main"
DEFAULT_TAG = "v2.2.4"

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
    "scikit-learn", "sentence-transformers", "transformers", "huggingface-hub",
    "torch", "tokenizers",
)


def package_versions(packages: tuple[str, ...] = CORE_PACKAGES) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in packages:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not installed"
    return versions


def _git_value(project_root: Path, *args: str) -> str | None:
    try:
        value = subprocess.check_output(
            ["git", *args], cwd=project_root, stderr=subprocess.DEVNULL, text=True, timeout=3
        ).strip()
        return value or None
    except (OSError, subprocess.SubprocessError):
        return None


def _git_metadata(project_root: Path) -> dict[str, str]:
    branch = _git_value(project_root, "rev-parse", "--abbrev-ref", "HEAD")
    commit = _git_value(project_root, "rev-parse", "--short=12", "HEAD")
    tag = _git_value(project_root, "describe", "--tags", "--exact-match")
    dirty = _git_value(project_root, "status", "--porcelain")
    return {
        "git_branch": branch or os.getenv("CDQAI_GIT_BRANCH", DEFAULT_BRANCH),
        "git_commit": commit or os.getenv("CDQAI_GIT_COMMIT", "source archive; commit unavailable"),
        "git_tag": tag or os.getenv("CDQAI_GIT_TAG", DEFAULT_TAG),
        "git_dirty": "yes" if dirty else "no" if branch else "not available",
        "repository": REPOSITORY_URL,
    }


def _windows_details() -> dict[str, str]:
    release = platform.release()
    version = platform.version()
    result = {
        "operating_system": platform.platform(),
        "os_name": platform.system() or "Unknown",
        "os_edition": "",
        "os_version": release,
        "os_build": version.split(".")[-1] if version else "",
    }
    if platform.system() != "Windows":
        return result
    try:
        import winreg  # type: ignore
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            product = str(winreg.QueryValueEx(key, "ProductName")[0])
            display = str(winreg.QueryValueEx(key, "DisplayVersion")[0])
            build = str(winreg.QueryValueEx(key, "CurrentBuildNumber")[0])
            ubr = str(winreg.QueryValueEx(key, "UBR")[0])
        # Some Windows 11 installations retain a Windows 10 ProductName compatibility value.
        if int(build) >= 22000 and "Windows 10" in product:
            product = product.replace("Windows 10", "Windows 11")
        result.update({
            "operating_system": f"{product} {display} (Build {build}.{ubr})",
            "os_name": "Windows 11" if int(build) >= 22000 else "Windows 10",
            "os_edition": product,
            "os_version": display,
            "os_build": f"{build}.{ubr}",
        })
    except (OSError, ValueError):
        pass
    return result


def _gpu_info() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "; ".join(torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count()))
        return "No CUDA GPU detected"
    except (ImportError, RuntimeError):
        return "Unavailable"


def collect_build_info(project_root: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "project": PROJECT_NAME,
        "short_name": SHORT_NAME,
        "version": VERSION,
        "release_name": RELEASE_NAME,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "architecture": platform.machine(),
        "gpu": _gpu_info(),
        "packages": package_versions(),
    }
    info.update(_windows_details())
    info.update(_git_metadata(project_root))
    return info
