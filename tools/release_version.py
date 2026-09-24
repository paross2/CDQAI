# CDQAI file version: 2.2.5
"""Synchronize reviewed public text files without opening private inputs."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MARKER = "CDQAI file version:"
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
PRIVATE_ROOTS = {"cache", "logs", "outputs", ".venv", ".vscode", "context"}


def release_paths(root: Path) -> list[str]:
    """Read only the reviewed inventory; never discover files in data folders."""
    paths = []
    for line in (root / "release-files.txt").read_text(encoding="utf-8-sig").splitlines():
        relative = line.strip()
        if not relative or relative.startswith("#"):
            continue
        path = Path(relative)
        allowed_placeholder = relative in {"cache/.gitkeep", "logs/.gitkeep", "outputs/.gitkeep"}
        allowed_context_doc = relative == "context/kentucky_dvmt/README.md"
        if (path.is_absolute() or ".." in path.parts or "\\" in relative or ":" in relative
                or path.parts[0] == ".git" or path.name.startswith(".env")
                or (path.parts[0] == "config" and relative != "config/config.example.yaml")
                or (path.parts[0] in PRIVATE_ROOTS and not allowed_placeholder and not allowed_context_doc)):
            raise ValueError(f"Disallowed release inventory path: {relative}")
        if not (path.suffix in {".py", ".md", ".txt", ".yaml", ".toml", ".cff", ".bat"}
                or relative in {"VERSION", "LICENSE", "LICENSE-DOCS", ".gitignore"}
                or allowed_placeholder):
            raise ValueError(f"Unsupported release file type: {relative}")
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise ValueError(f"Release path escapes project: {relative}")
        if not resolved.is_file():
            raise ValueError(f"Missing release file: {relative}")
        if relative in paths:
            raise ValueError(f"Duplicate release path: {relative}")
        paths.append(relative)
    return paths


def with_marker(relative: str, text: str, version: str) -> str:
    if relative == "VERSION":
        return version + "\n"
    text = re.sub(r"(?m)^(?:# |REM |<!-- )?CDQAI file version: [^\n]*\n?", "", text)
    suffix = Path(relative).suffix
    if suffix == ".md":
        marker = f"<!-- {MARKER} {version} -->"
    elif suffix == ".bat":
        marker = f"REM {MARKER} {version}"
    elif (suffix in {".py", ".yaml", ".toml", ".cff"}
          or Path(relative).name in {"requirements.txt", "requirements-dev.txt", "release-files.txt", ".gitignore", ".gitkeep"}):
        marker = f"# {MARKER} {version}"
    else:
        marker = f"{MARKER} {version}"
    # Keep batch echo suppression and Python shebang/encoding declarations in place.
    lines = text.splitlines(keepends=True)
    offset = 0
    if lines and (lines[0].strip().lower() == "@echo off" or lines[0].startswith("#!")):
        offset = 1
    if suffix == ".py":
        for index, line in enumerate(lines[:2]):
            if re.match(r"\s*#.*coding[:=]", line):
                offset = max(offset, index + 1)
    lines.insert(offset, marker + "\n")
    return "".join(lines)


def synchronized_text(relative: str, text: str, old: str, version: str) -> str:
    if relative == "cdqai/core/build_info.py":
        text = re.sub(r'(?m)^VERSION = "[^"]+"', f'VERSION = "{version}"', text)
        text = re.sub(r'(?m)^DEFAULT_TAG = "[^"]+"', f'DEFAULT_TAG = "v{version}"', text)
    elif relative == "pyproject.toml":
        text = re.sub(r'(?m)^version = "[^"]+"', f'version = "{version}"', text)
    elif relative == "config/config.example.yaml":
        text = re.sub(r'(?m)^  version: "[^"]+"', f'  version: "{version}"', text)
    elif relative == "CITATION.cff":
        text = re.sub(r"(?m)^version: .+$", f"version: {version}", text)
        if old != version:
            text = re.sub(r"(?m)^date-released: .+$", f"date-released: {date.today().isoformat()}", text)
    elif relative in {"README.md", "INSTALL.txt", "How To Run.txt", "docs/USER_GUIDE.md", "docs/TECHNICAL_ARCHITECTURE.md"}:
        # These are current-use documents. Historical release notes are not in the inventory.
        text = re.sub(r"\b(Version |version |VERSION |CDQAI )\d+\.\d+\.\d+", lambda m: m[1] + version, text)
    return with_marker(relative, text, version)


def synchronize(root: Path, *, version: str | None = None, check: bool = False) -> list[str]:
    old = (root / "VERSION").read_text(encoding="utf-8-sig").strip()
    version = version or old
    if not VERSION_RE.fullmatch(version) or not VERSION_RE.fullmatch(old):
        raise ValueError("VERSION must use MAJOR.MINOR.PATCH, for example 2.2.5")
    paths = release_paths(root)
    changes = {}
    for relative in paths:
        text = (root / relative).read_text(encoding="utf-8-sig")
        expected = synchronized_text(relative, text, old, version)
        if text != expected:
            changes[relative] = expected
    if not check:
        for relative, text in changes.items():
            with (root / relative).open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
    return list(changes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="Set a new MAJOR.MINOR.PATCH release and synchronize current files")
    parser.add_argument("--check", action="store_true", help="Report stale file versions without writing")
    args = parser.parse_args(argv)
    if args.check and args.version:
        parser.error("Use --version to update, then --check to verify")
    try:
        changes = synchronize(ROOT, version=args.version, check=args.check)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Version check failed: {exc}\n")
    for relative in changes:
        print(("Stale: " if args.check else "Updated: ") + relative)
    if args.check and changes:
        return 1
    print("Release file versions are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
