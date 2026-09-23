# Publishing local CDQAI changes

Develop in the working checkout that contains the private configuration and local
runtime files. That checkout can publish source changes directly to GitHub; a second
copy or replacement of the private configuration is unnecessary.

Before committing, from that checkout:

```powershell
git status --short
git diff --stat
git diff
git check-ignore config/config.yaml .venv outputs/dashboard.html outputs/dashboard_narratives.js cache/merged_crash_dataset.parquet
git ls-files config/config.yaml .env .venv cache logs outputs
```

The last command should list only the runtime directories' `.gitkeep` files.
`config/config.yaml` must remain ignored and untracked. Keep database placeholders
in `config/config.example.yaml`; update it manually when the configuration schema
changes, never by copying the private file over it.

Stage explicitly reviewed source, tests, and documentation paths. Then inspect the
exact proposed publication:

```powershell
git diff --cached --name-status
git diff --cached --check
git diff --cached
```

Check the staged content for credentials, hostnames, connection strings, local
private paths, narratives, MFNs, and record-level exports. Dashboard HTML, companion
JavaScript, CSV/Parquet reports, caches, logs, and run manifests are private runtime
artifacts even if filenames sound like summaries. Review new binary files separately;
ordinary text diffs cannot establish that they are sanitized. The versioned county
DVMT workbooks are documented context data, not a precedent for adding crash exports.

After tests pass and the staged diff is reviewed, commit with a descriptive message.
Verify `git remote -v` locally and publish to the intended `paross2/CDQAI` remote and
branch. Do not reinitialize an existing repository or create a release tag for routine
development changes. Do not use force-add to bypass the private-file exclusions.
