# Apartment Intelligence

Apartment Intelligence is a WebMCP-native consumer apartment environmental-study
application. It brings early-stage architectural solar analysis to a Singapore
resident evaluating an existing HDB apartment.

The guaranteed demonstration starts with 87 Dawson Road and storey 30. An
agent resolves the bundled public context, the resident confirms the
target unit and windows in a visible 3D scene, and deterministic analysis
produces sunpath, shadow, solar-access, and radiation evidence.

Status: implementation in progress. No validated analysis, public deployment,
or submitted challenge entry is claimed until the release gates pass.

## Product boundary

- V1 is an HDB-first consumer decision aid, not a professional certification or
  statutory compliance service.
- Public records provide contextual building information. Exact unit facade,
  window position, balcony geometry, and internal layout remain human-confirmed.
- Three.js is the proposed browser renderer. Ladybug's Python libraries are the
  proposed solar-analysis engine. `rhino3dm.py` is the proposed `.3dm` exporter.
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

Build instructions will be added with the first tested implementation. The
public target is `https://apartment.senibina.com.sg`; this is a target, not a
current deployment claim.
