# Apartment Intelligence

Apartment Intelligence is both a WebMCP Challenge project and a Senibina
goodwill project for the public good. It brings early-stage architectural solar
analysis to a Singapore resident evaluating an existing HDB apartment.

We entered architecture because we love buildings, drawing, and 3D modelling.
This project asks how those same tools can help residents evaluate the
environmental conditions of a home empirically and objectively, with evidence,
provenance, and uncertainty kept visible.

The guaranteed demonstration starts with 87 Dawson Road and storey 30. An
agent resolves the bundled public context, the resident places and confirms a
published typical 4-room reference plan and window in a visible 3D scene, and deterministic analysis
produces sunpath, shadow, solar-access, and radiation evidence.

Status: implementation gates 1–5 pass. The Windows VM, named Cloudflare Tunnel,
public hostname, Chrome WebMCP journey, restart recovery, and complete artifact
bundle have been exercised. Demo-video preparation and challenge submission
remain open.

## Public-interest research

Apartment Intelligence begins in Singapore because this is where Senibina
practises and can evaluate the work responsibly. Its longer-term hypothesis is
that useful architectural knowledge about existing homes should not remain
available only to professionals: residents should be able to understand
sunlight, obstruction, environmental exposure, and the provenance and
uncertainty behind each conclusion.

The Dawson study is one deliberately bounded beginning. Future research may
reconstruct and validate reference floor plans for a wider subset of Singapore
housing, creating a transparent and reusable public-interest knowledge base.
Any reconstructed plan must retain its source, method, confidence, and limits;
it must never be presented as an authoritative unit survey or verified stack
without supporting evidence.

If the approach survives local scrutiny, the ambition is to extend the practice
across ASEAN and, eventually, other housing contexts globally. Singapore remains
the first case study, not a claim of official status or government endorsement.

## Product boundary

- V1 is an HDB-first consumer decision aid, not a professional certification or
  statutory compliance service.
- Public records provide contextual building information. A compiler-derived
  SkyVille @ Dawson 4R Type A reference boundary is uniformly scaled to 87 m²;
  facade placement, handedness, and window geometry remain human-confirmed.
- Three.js renders the browser scene. Ladybug Core and Geometry compute the
  bounded solar studies. `rhino3dm.py` writes the layered `.3dm` export.
- The MVP uses a frozen, attributed Dawson fixture; it has no runtime listing
  scraper, floorplan upload, OneMap dependency, database, account, or LLM.
- Results must distinguish sourced, inferred, generated, and human-confirmed
  information.

## Documentation

Repository knowledge follows PARA. Start at
[`_DOCUMENTATION/README.md`](_DOCUMENTATION/README.md).
The interface, architectural graphics, and evidence exports follow the
repository-local [`DESIGN.md`](DESIGN.md).

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

The brochure raster is not redistributed. To regenerate the tracked unit-plan
fixture from a locally retained reviewed page image, create the isolated
authoring environment from `data/compiler-requirements.txt` and follow
[`data/README.md`](data/README.md). NumPy and OpenCV are authoring-only and are
not installed on the deployed VM.

To test WebMCP in Chrome, enable `chrome://flags/#enable-webmcp-testing`, visit
the localhost URL, and inspect `document.modelContext.getTools()` in DevTools.
The verified public deployment is <https://apartment.senibina.com.sg>. Windows
deployment is documented in
[`WINDOWS_DEPLOYMENT.md`](WINDOWS_DEPLOYMENT.md).

## v2 clean room (branch `v2-clean-room`)

A headless rebuild on this branch: published 4-room plans traced to coordinate recipes with real
walls, columns, openings and balcony; the Block 87 plate reconstructed from the sourced HDB
footprint; Ladybug + Radiance (`gendaymtx`, `rcontrib`) computing sunpath, shadow, direct sun and
annual radiation on a 0.25 m floor grid; eight WebMCP tools on `document.modelContext` with no
confirmation tool; deterministic GLB, OBJ, SVG, evidence.json and ZIP exports; one Docker image.
See `_DOCUMENTATION/10 Projects/2026-09-clean-room-reconstruction.md` and `deploy/RUNBOOK.md`.
