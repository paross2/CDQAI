<!-- CDQAI file version: 2.3.6 -->
# Working on CDQAI

## Protected data

Server-sourced data and local inputs are protected. Do not read private
`config/config.yaml`, datasets, input workbooks, narratives, identifiers, or
existing runtime outputs into an AI session. Do not run SQL or real-data pipelines
through an AI tool. Work with source code, sanitized documentation, and fabricated
fixtures only. Users perform real-data runs and inspect results privately.

Run automated verification in a separate source-only directory with placeholder
configuration. Exclude the two workbook-dependent tests. Do not copy input
workbooks, private configuration, caches, logs, or outputs into that directory.

## Version consistency and publication

`VERSION` is the release source of truth. Each maintained public text/code file
listed in `release-files.txt` must carry the matching release marker. After any
source/documentation update, run `python tools/release_version.py --check`. Add new
maintained files explicitly to the inventory. To change releases, use
`python tools/release_version.py --version X.Y.Z`, then update release notes and
run the check. Never put private files or input data in the release inventory.

Keep historical changelog entries, archived release notes, and external dataset
versions intact. License bodies and copyright statements must be preserved;
the added file-version line is distribution metadata only. Do not move published
tags or rewrite Git history merely to refresh GitHub's last-change labels.

Use `Release_CDQAI.bat` for a version check and `GIT_SETUP.md` for publication.
Stage explicit reviewed source/documentation paths only. Never use `git add -A`
or force-add in this working installation. Review the exact staged filenames and
diff before each commit/push; protected data must never be published.

## Temporary artifacts and cleanup

Keep outputs reserved for analyst reports, intentional user-facing files, and
private recovery backups. Do not leave development worktrees, release staging,
pytest directories, Edge profiles, or one-off publishing scripts there.
Use `python tools/verify_release.py` for isolated synthetic validation; it removes
its temporary source workspace on success and failure. For other development or
browser tasks use an owned system-temporary directory and cleanup in try/finally.
Close and wait for only the browser/helper processes started by the task before
removing their temporary profiles. Record concise results in release notes or the
final response, not persistent copies of complete validation environments.
Before finishing each task, remove its disposable artifacts. Verify resolved
cleanup targets stay inside the owned temporary directory; refuse reparse points
and never broadly clear outputs, caches, logs, private reports, or recovery backups.
If a temporary artifact must remain for diagnosis, name it and explain why.
