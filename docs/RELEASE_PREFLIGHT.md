<!-- CDQAI file version: 2.3.6 -->
# Release version preflight

Run this checklist for every release. `VERSION` is the intended source version;
a GitHub release does not update local installations or previously generated HTML.
Do not edit a report's version label to make an old analysis look newly generated.

## 1. Confirm the checkout before editing

- [ ] Record the absolute project directory, `git branch --show-current`,
  `git status --short`, and `git log -1 --oneline`. Resolve local changes first.
- [ ] Fetch the intended remote and compare against its current `main`.
  Confirm the intended release builds on that commit and the new tag is unused.
- [ ] Check that the IDE, terminal, Windows shortcut, and batch launcher point
  to this same directory. Close obsolete version-named launcher tabs.
- [ ] Run the following locally to identify the imported code without loading
  private configuration or running a data pipeline:

```powershell
Get-Location
Get-Content VERSION
.\.venv\Scripts\python.exe -c "import sys, cdqai; from cdqai.core import build_info; print(sys.executable); print(cdqai.__file__); print(build_info.__file__); print(cdqai.__version__)"
```

## 2. Synchronize source and documentation

- [ ] Choose the next release number, then run
  `.\.venv\Scripts\python.exe tools/release_version.py --version X.Y.Z`.
- [ ] Confirm `VERSION`, runtime `build_info.VERSION`, `DEFAULT_TAG`, package
  metadata, citation version/date, and example configuration agree.
- [ ] Update the release name in build metadata, README, example configuration,
  and its metadata test. The version updater does not choose release names.
- [ ] Add the new release notes; update both changelogs and the README notes link.
- [ ] Review current-use documentation headings and prose, not just file markers.
- [ ] Add every new maintained public file to `release-files.txt`. Classify
  archived documents and external data explicitly in `release-exclusions.txt`.
  Never put private configuration, records, generated reports, or caches in either
  list as a way to publish them. External workbook contents are not versioned as software.
- [ ] Preserve historical release numbers, changelog history, dependency versions,
  test fixture versions, license bodies, and external dataset dates.
- [ ] Run both checks from the publishing checkout:

```powershell
.\.venv\Scripts\python.exe tools/release_version.py --check
.\.venv\Scripts\python.exe tools/release_version.py --check-git
```

The first checks maintained files. The second also compares every Git-tracked
filename against the maintained inventory and explicit exclusions, without opening
excluded data. Stage new files explicitly, then repeat the second check to include
them. Source archives without Git can use the first check only.

## 3. Validate runtime and generated output

- [ ] Run `.\.venv\Scripts\python.exe tools/verify_release.py`. It copies only
  the public inventory into a temporary source-only workspace, runs the synthetic
  tests with the two workbook-dependent tests excluded, and removes the workspace
  on success or failure. Do not make persistent verify/release/edge folders in outputs.
- [ ] For additional browser checks, use an owned temporary directory and a
  try/finally cleanup block; terminate only the browser process you started and
  wait for it to exit before removing its profile. Preserve a short validation
  result in the release notes rather than whole worktrees or browser profiles.
- [ ] Confirm stale local project metadata is overridden by application metadata.
- [ ] Run the synthetic smoke pipeline and check its `run_manifest.json` version.
- [ ] Open the synthetic dashboard and check browser title, header, footer,
  project metadata, system provenance, and generated timestamp. All release labels
  must equal `VERSION`; package/Python/OS versions are separate provenance values.
- [ ] Expand a synthetic finding and verify yellow spans. Verify a selected-crash
  print/PDF report inherits the dashboard version in its report metadata.
- [ ] Keep the HTML and its narrative companion from the same successful run.

## 4. Publish and verify

- [ ] Use `Release CDQAI X.Y.Z: AI Powered Crash Data Anomaly Detector` for the
  release commit and GitHub release title. Describe incremental features in the notes.
- [ ] Review exact staged names and `git diff --cached`, including version markers;
  run `git diff --cached --check`. Do not use `git add -A`.
- [ ] Commit, create an unused annotated `vX.Y.Z` tag, and push `main` and the tag.
  Never move an existing release tag or force-push to correct a version display.
- [ ] Verify remote `main` and the peeled tag resolve to the reviewed commit.
- [ ] Publish the GitHub release with the matching tag, title, and notes, and verify
  its Latest status. GitHub's per-file last-commit labels are not application versions.
- [ ] Check a fresh source download for metadata consistency. No generated private
  dashboard belongs in release assets.

## 5. Update the installation and regenerate locally

- [ ] Update the actual installation directory, not just another checkout.
- [ ] Repeat the path/import checks in step 1. The launcher now prints its directory
  and refuses to run when the maintained source version check fails.
- [ ] The user runs `Run_CDQAI.bat` against real data locally and confirms success.
  A failed run can leave an older dashboard in place.
- [ ] Open the exact newly generated output path, reload the browser, and confirm
  the version and timestamp. Keep its companion file alongside it.
- [ ] If the header is older, compare the imported code path, output path, timestamp,
  and local manifest privately. Do not assume a GitHub release updated that file.

See [the version audit](VERSION_AUDIT.md) for the complete file classification and
the version propagation chain. An offline static dashboard cannot know whether a
new release has been published elsewhere.
