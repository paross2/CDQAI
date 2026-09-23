# Local development

Open the intended working checkout itself in VS Code. The code, configuration,
and runtime paths are resolved from the working directory; opening a second clone
does not automatically use the first checkout's private configuration or caches.

## Python and VS Code

Use Python 3.11 and a project-local `.venv`. Reuse an existing working environment;
do not recreate it simply because its original creation path has changed.
For a fresh checkout, run these commands from its root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
```

If the Python launcher cannot find 3.11, use the full path to an installed
Python 3.11 executable for the first command. Activation is optional when using
the explicit executable paths above. `requirements-dev.txt` includes the runtime
requirements and pytest. Dependencies currently have minimum versions, not a lockfile.

Install the Microsoft Python extension in VS Code. Run **Python: Select Interpreter**
and select `.venv\Scripts\python.exe` in this checkout. Enable pytest and select
`tests` when prompted. Local `.vscode` settings are intentionally ignored by Git.
The setup provided for this checkout includes a synthetic smoke debug configuration.

## Configuration and verification

Keep a working `config/config.yaml` unchanged. On a new installation only:

```powershell
if (-not (Test-Path config/config.yaml)) {
    Copy-Item config/config.example.yaml config/config.yaml
}
```

Edit the ignored local file for approved database settings. The example must retain
placeholder database values. Do not paste the private file, database errors, or
record-level output into public issues or pull requests.

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m cdqai.main --health-check
.\.venv\Scripts\python.exe -m cdqai.main --smoke-test
```

The health check verifies configuration and creates runtime directories; it does
not verify SQL connectivity or model availability. The smoke command ignores
private configuration and existing caches. It uses 128 fabricated records,
structured Isolation Forest scoring, deterministic rules, findings, and dashboard
generation. Open `outputs/smoke/dashboard.html` and keep its companion
`dashboard_narratives.js` beside it. Smoke runs reuse only the `outputs/smoke/`
location. Percentiles and priorities in this tiny dataset do not validate model quality.

The smoke command disables semantic embeddings and DVMT enrichment. The test suite
separately checks the supplied 2025 DVMT workbook. Full narrative execution, SQL
access, and production-scale performance require separate validation.

## Full private run

```powershell
.\.venv\Scripts\python.exe -m cdqai.main --run-all
```

This command can process the entire cached or configured dataset and writes private
reports into the configured output directory. Do not use it as a small-run test.
`--refresh-cache` rebuilds data and embedding caches; it is not needed for normal
setup. An uncached embedding model may be downloaded on first use. Prepare model
files within the approved environment before an offline production run.

See [GIT_SETUP.md](../GIT_SETUP.md) before publishing changes and
[DEVELOPMENT_REVIEW.md](DEVELOPMENT_REVIEW.md) for the implementation review.
