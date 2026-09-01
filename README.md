# Apartment Intelligence

Apartment Intelligence is a WebMCP-native consumer apartment environmental-study
application. It brings early-stage architectural solar analysis to a Singapore
resident evaluating an existing HDB apartment.

The guaranteed demonstration starts with 87 Dawson Road and storey 30. An
agent resolves the bundled public context, the resident confirms the
target unit and windows in a visible 3D scene, and deterministic analysis
produces sunpath, shadow, solar-access, and radiation evidence.

Status: implementation gates 1–5 pass. The Windows VM, named Cloudflare Tunnel,
public hostname, Chrome WebMCP journey, restart recovery, and complete artifact
bundle have been exercised. Demo-video preparation and challenge submission
remain open.

## Product boundary

- V1 is an HDB-first consumer decision aid, not a professional certification or
  statutory compliance service.
- Public records provide contextual building information. Exact unit facade,
  window position, balcony geometry, and internal layout remain human-confirmed.
- Three.js renders the browser scene. Ladybug Core and Geometry compute the
  bounded solar studies. `rhino3dm.py` writes the layered `.3dm` export.
- The MVP uses a frozen, attributed Dawson fixture; it has no runtime listing
  scraper, floorplan upload, OneMap dependency, database, account, or LLM.
- Rhino.Compute is excluded from the MVP unless an approved requirement cannot
  be met by the simpler stack.
- Results must distinguish sourced, inferred, generated, and human-confirmed
  information.

## Documentation

Repository knowledge follows PARA. Start at
[`_DOCUMENTATION/README.md`](_DOCUMENTATION/README.md).

Founder-only competition evaluation and deployment notes live under the
Git-ignored `private/` directory. Ignored files are local working material and
are not backed up by Git.

## Local development

Prerequisites are Node 22.22.3 and CPython 3.13.2. Install only from the
committed locks after reviewing the recorded dependency decision:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r server/requirements.txt
npm --prefix web ci --ignore-scripts
npm --prefix web run build
```

Run the single-process local build at `http://localhost:8000`:

```sh
COOKIE_SECURE=false EXPECTED_ORIGIN=http://localhost:8000 PYTHONPATH=server \
  .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run verification with:

```sh
PYTHONPATH=server .venv/bin/python -m pytest server/tests
npm --prefix web test -- --run
npm --prefix web run build
```

To test WebMCP in Chrome, enable `chrome://flags/#enable-webmcp-testing`, visit
the localhost URL, and inspect `document.modelContext.getTools()` in DevTools.
The verified public deployment is <https://apartment.senibina.com.sg>. Windows
deployment is documented in
[`WINDOWS_DEPLOYMENT.md`](WINDOWS_DEPLOYMENT.md).
