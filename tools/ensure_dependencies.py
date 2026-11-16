# CDQAI file version: 2.5.0
"""Install missing runtime packages declared in requirements.txt."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import subprocess
import sys
from collections.abc import Callable


ROOT = Path(__file__).resolve().parents[1]
IMPORT_NAMES = {
    "pyyaml": "yaml",
    "sqlalchemy": "sqlalchemy",
    "scikit-learn": "sklearn",
    "sentence-transformers": "sentence_transformers",
    "huggingface-hub": "huggingface_hub",
}


def missing_requirements(
    requirements_text: str,
    module_exists: Callable[[str], bool] | None = None,
) -> list[str]:
    exists = module_exists or (
        lambda module: importlib.util.find_spec(module) is not None
    )
    missing = []
    for raw_line in requirements_text.splitlines():
        requirement = raw_line.split("#", 1)[0].strip()
        if not requirement:
            continue
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
        if not match:
            raise ValueError(f"Unsupported requirement entry: {raw_line}")
        distribution = match.group(1).lower()
        module = IMPORT_NAMES.get(distribution, distribution.replace("-", "_").replace(".", "_"))
        if not exists(module):
            missing.append(requirement)
    return missing


def main() -> int:
    requirements = ROOT / "requirements.txt"
    missing = missing_requirements(requirements.read_text(encoding="utf-8"))
    if not missing:
        print("All declared runtime dependencies are available.")
        return 0

    print("Installing missing runtime dependencies: " + ", ".join(missing), flush=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", *missing],
        check=True,
    )
    still_missing = missing_requirements(requirements.read_text(encoding="utf-8"))
    if still_missing:
        print(
            "Dependencies are still unavailable after installation: "
            + ", ".join(still_missing),
            file=sys.stderr,
        )
        return 1
    print("Missing runtime dependencies installed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
