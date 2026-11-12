# CDQAI file version: 2.3.7
"""Validate a main-branch version bump and publish its GitHub release."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if __package__:
    from tools.release_version import inventory_gaps, release_paths, synchronize
else:
    from release_version import inventory_gaps, release_paths, synchronize


REPOSITORY = "paross2/CDQAI"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
ZERO_SHA = "0" * 40


def version_tuple(version: str) -> tuple[int, int, int]:
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"Invalid release version: {version}")
    return tuple(int(part) for part in version.split("."))


def validate_version_bump(previous: str, current: str) -> str:
    if version_tuple(current) <= version_tuple(previous):
        raise ValueError(
            f"Every push to main needs a version higher than {previous}; found {current}"
        )
    return f"v{current}"


def release_notes_path(root: Path, version: str) -> Path:
    relative = f"docs/RELEASE_NOTES_{version}.md"
    if relative not in release_paths(root):
        raise ValueError(f"{relative} must exist and be listed in release-files.txt")
    return root / relative


def validate_checkout(root: Path, before: str) -> tuple[str, str, Path]:
    if not before or before == ZERO_SHA:
        raise ValueError("A main push must have a previous commit to compare")
    result = subprocess.run(
        ["git", "show", f"{before}:VERSION"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    previous = result.stdout.strip()
    current = (root / "VERSION").read_text(encoding="utf-8-sig").strip()
    tag = validate_version_bump(previous, current)
    if synchronize(root, check=True):
        raise ValueError("Maintained release-file versions are not synchronized")
    gaps = inventory_gaps(root)
    if gaps:
        raise ValueError("Unclassified tracked paths: " + ", ".join(gaps))
    return current, tag, release_notes_path(root, current)


def github_request(
    url: str, token: str, *, method: str = "GET", payload: dict | None = None
) -> dict | None:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "CDQAI-release-publisher",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return None
        detail = json.load(error).get("message", "GitHub API request failed")
        raise RuntimeError(f"GitHub API returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError("Could not reach the GitHub API") from error


def tag_commit(token: str, tag: str) -> str | None:
    api = f"https://api.github.com/repos/{REPOSITORY}"
    reference = github_request(f"{api}/git/ref/tags/{tag}", token)
    if reference is None:
        return None
    target = reference["object"]
    for _ in range(5):
        if target["type"] == "commit":
            return target["sha"]
        if target["type"] != "tag":
            raise RuntimeError(f"Release tag {tag} does not resolve to a commit")
        annotated = github_request(f"{api}/git/tags/{target['sha']}", token)
        if annotated is None:
            raise RuntimeError(f"Could not resolve annotated release tag {tag}")
        target = annotated["object"]
    raise RuntimeError(f"Release tag {tag} exceeds the supported annotation depth")


def publish_release(tag: str, version: str, commit: str, notes: str, token: str) -> str:
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise ValueError(f"Release publishing is restricted to {REPOSITORY}")
    api = f"https://api.github.com/repos/{REPOSITORY}"
    existing = github_request(f"{api}/releases/tags/{tag}", token)
    tagged_commit = tag_commit(token, tag)
    if existing is not None:
        if tagged_commit != commit:
            raise RuntimeError(f"Existing release tag {tag} does not point to this commit")
        return existing["html_url"]
    if tagged_commit is not None and tagged_commit != commit:
        raise RuntimeError(f"Existing tag {tag} points to a different commit")
    release = github_request(
        f"{api}/releases",
        token,
        method="POST",
        payload={
            "tag_name": tag,
            "target_commitish": commit,
            "name": f"Release CDQAI {version}: AI Powered Crash Data Anomaly Detector",
            "body": notes,
            "draft": False,
            "prerelease": False,
            "make_latest": "true",
        },
    )
    if release is None:
        raise RuntimeError("GitHub did not return the created release")
    return release["html_url"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without publishing")
    args = parser.parse_args(argv)
    try:
        version, tag, notes_path = validate_checkout(
            ROOT, os.environ.get("GITHUB_EVENT_BEFORE", "")
        )
        if args.check:
            print(f"Validated {version} release as {tag}.")
            return 0
        token = os.environ.get("GITHUB_TOKEN")
        commit = os.environ.get("GITHUB_SHA")
        if not token or not commit:
            raise ValueError("GITHUB_TOKEN and GITHUB_SHA are required to publish")
        url = publish_release(
            tag, version, commit, notes_path.read_text(encoding="utf-8-sig"), token
        )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Release publishing failed: {error}", file=sys.stderr)
        return 1
    print(f"Published {tag}: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
