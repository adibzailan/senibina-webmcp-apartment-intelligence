# Runbook: Apartment Intelligence v2

## Local (no Docker)

```bash
python3.13 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt && .venv/bin/pip install --no-deps -e .
# Radiance: unzip the pinned LBNL-ETA 39b99660 macOS arm64 build into .tools/radiance (bin/ and lib/)
(cd apps/web && npm ci && npm run build)
.venv/bin/uvicorn ai_api.main:app --port 8000
```

Open http://127.0.0.1:8000. Radiance is found via `RADIANCE_PATH`, then `.tools/radiance`, then `/usr/local/radiance`.

## Docker

```bash
docker compose -f deploy/compose.yaml build && docker compose -f deploy/compose.yaml up -d
curl -fsS http://127.0.0.1:8000/healthz
docker compose -f deploy/compose.yaml kill && docker compose -f deploy/compose.yaml up -d
curl -fsS http://127.0.0.1:8000/healthz
```

Studies live in memory for 30 minutes and are lost on restart; the page shows `STUDY_EXPIRED` with the next action.

## Tests

```bash
.venv/bin/python -m pytest tests/unit tests/api -q
(cd apps/web && npx vitest run)
(cd tests/e2e && npx playwright test)   # Chrome 152 with --enable-features=WebMCP
```

## Render

`deploy/render.yaml` describes one Git-backed Docker web service in Singapore on the Standard plan (1 CPU / 2 GB) with `/healthz`. Connect the repo in the Render dashboard and pick the blueprint; no secrets are needed. After that every push to `main` rebuilds and redeploys with zero downtime and instant rollback. Free instances (0.1 CPU, spin-down after 15 min) cannot meet the 15 s analysis budget.

## Limits

256 KB body, one analysis at a time, five per session per ten minutes, 15 s worker budget (0.25 m grid runs in about 3 s locally), 100 live studies, 20 MB export.
