# AGENTS.md — Running Hotpass with Codex

This note tells Codex how to run Hotpass end‑to‑end and what internet access it may need. Keep it short, explicit, and safe-by-default.

---

## 1) Codex Cloud: environment recipe

**Purpose:** build/install the project, then run the pipeline on a dataset.

### 1.1 Internet access policy

- **Mode:** On, with an allowlist.
- **Preset:** _Common dependencies_ (for builds), **plus** the runtime API domains you actually use (see §3).
- **HTTP methods:** start with `GET, HEAD, OPTIONS` only; enable `POST` only if a provider requires it.

### 1.2 Environment variables vs secrets

- Put **runtime API keys** in **environment variables** (available to the agent while it runs).
- Use **secrets only for setup** (they are removed before the agent phase).

### 1.3 Setup script (runs before the agent, has full internet)

Use either _pip_ or _uv_. Pick one block.

**Option A — pip only**

```bash
python -m pip install -U pip
python -m pip install -e ".[orchestration,enrichment,geospatial,compliance]"
```

**Option B — uv**

```bash
python -m pip install -U uv
uv venv
uv sync --extra orchestration --extra enrichment --extra geospatial --extra compliance
```

> Notes
>
> - The _Common dependencies_ preset already allowlists PyPI domains; you shouldn’t need to add them manually.
> - Keep the setup fast: avoid heavyweight toolchains you don’t need.

### 1.4 Agent run command (what Codex should execute)

Baseline run into `dist/refined.xlsx`:

```bash
uv run hotpass --input-dir ./data --output-path ./dist/refined.xlsx --archive
```

If you used Option A (pip), replace `uv run` with `python -m hotpass`:

```bash
python -m hotpass --input-dir ./data --output-path ./dist/refined.xlsx --archive
```

**Artifacts**: `dist/` will contain the refined output and any reports Hotpass produces.

---

## 2) Expected network calls (and domains to allowlist)

### 2.1 During setup (always on)

PyPI + friends for dependency installs (already covered by _Common dependencies_):

- `pypi.org`, `pypa.io`, `pythonhosted.org` (package index / wheels)
- `github.com`, `githubusercontent.com` (occasional source downloads)

### 2.2 During the agent run (depends on enabled extras)

- **Core pipeline:** local only; no network needed.
- **Enrichment / Geospatial / Compliance extras:** may call your chosen providers. Add only what you use, e.g.:
  - Geocoding/examples: `nominatim.openstreetmap.org`, `api.opencagedata.com`, `api.geoapify.com`
  - Company/people enrichment (examples): provider-specific API domains

> Keep the list tight. Prefer read‑only `GET` where possible; enable `POST` only if strictly required.

---

## 3) Runtime configuration

Set provider credentials as environment variables in the Codex **Environment** (not in Secrets if they’re needed at runtime), for example:

```text
HOTPASS_GEOCODE_API_KEY=...
HOTPASS_ENRICH_API_KEY=...
```

Document any additional variables your chosen providers expect.

---

## 4) Quick verification (sanity check task)

Have Codex run the following first to confirm network policy and imports:

```bash
python - <<'PY'
import sys, requests
print('py ok', sys.version.split()[0])
print('net ok', requests.get('https://pypi.org', timeout=10).status_code)
PY
```

If this is blocked, expand the allowlist or allowed methods and retry.

---

## 5) Troubleshooting

- **ImportError / missing wheel** → rerun the task; ensure _Common dependencies_ is selected.
- **HTTP 403/429 from a provider** → your key or method is wrong, or the domain/method is not allowlisted.
- **Agent cannot see your key** → keys must be Environment Variables for runtime.

---

## 6) Local use with Codex CLI (optional)

If running locally, enable network in the `workspace-write` sandbox and reuse the commands above.
Example `~/.codex/config.toml` snippet:

```toml
[sandbox_workspace_write]
network_access = true
```

---

### Checklist (copy/paste into a Codex task)

1. Use Cloud environment **Hotpass**; Internet Access: _Common dependencies_ + required provider domains; Methods: `GET,HEAD,OPTIONS`.
2. Run **Setup script** (Option A or B).
3. Execute the **Agent run command**.
4. Upload `dist/refined.xlsx` as artifact.
