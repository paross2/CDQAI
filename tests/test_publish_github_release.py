# CDQAI file version: 2.3.7
from pathlib import Path

import pytest

from tools.publish_github_release import (
    release_notes_path,
    validate_version_bump,
)


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        ("2.3.6", "2.3.7", "v2.3.7"),
        ("2.9.9", "3.0.0", "v3.0.0"),
    ],
)
def test_main_push_requires_a_higher_semantic_version(previous, current, expected):
    assert validate_version_bump(previous, current) == expected


@pytest.mark.parametrize(
    ("previous", "current"),
    [
        ("2.3.6", "2.3.6"),
        ("2.3.6", "2.3.5"),
        ("2.3.6", "2.3"),
        ("invalid", "2.3.7"),
    ],
)
def test_main_push_rejects_missing_or_invalid_version_bump(previous, current):
    with pytest.raises(ValueError):
        validate_version_bump(previous, current)


def test_release_notes_must_be_in_public_inventory(tmp_path):
    (tmp_path / "release-files.txt").write_text("docs/RELEASE_NOTES_1.2.3.md\n")
    notes = tmp_path / "docs" / "RELEASE_NOTES_1.2.3.md"
    notes.parent.mkdir()
    notes.write_text("Release notes")
    assert release_notes_path(tmp_path, "1.2.3") == notes


def test_release_notes_missing_from_inventory_is_rejected(tmp_path):
    (tmp_path / "release-files.txt").write_text("README.md\n")
    (tmp_path / "README.md").write_text("Current project guide")
    with pytest.raises(ValueError, match="release-files.txt"):
        release_notes_path(tmp_path, "1.2.3")
