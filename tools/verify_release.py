# CDQAI file version: 2.3.6
"""Run isolated synthetic tests in a temporary directory, removed on exit."""
from contextlib import contextmanager
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.release_version import release_paths


@contextmanager
def verification_workspace(root=ROOT):
    # Only public inventory files are copied, never private runtime directories.
    with tempfile.TemporaryDirectory(prefix="cdqai-verify-") as temporary:
        workspace = Path(temporary)
        for relative in release_paths(root):
            destination = workspace / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, destination)
        yield workspace


def main():
    with verification_workspace() as workspace:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-k",
             "not test_all_annual_context_workbooks_are_present and not test_2025_workbook_parses_120_counties",
             "--basetemp", str(workspace / ".test-temp")],
            cwd=workspace,
        )
    print("Temporary verification workspace removed.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
