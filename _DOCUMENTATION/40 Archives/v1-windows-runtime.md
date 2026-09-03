---
title: v1 runtime (Windows VM)
para: archive
status: superseded-implementation
decision_date: 2026-09-03
---

# v1 runtime (Windows VM)

The first implementation (1–2 September 2026) ran a FastAPI app from `server/`
and a React app from `web/` on a Windows 11 ARM VM behind a Cloudflare Tunnel,
serving `apartment.senibina.com.sg`. It used a custom solar loop
(`apartment-intelligence-solar-v5`) with at most 256 floor sensors, an outline-only
unit plan compiled from the brochure, six WebMCP tools, and five 1600 × 2400 PNG
cards. Its deployment receipt and dependency intake remain in
`20 Areas/security-and-operations.md`.

It was superseded by the v2 clean-room rebuild because the apartment showed no
walls, the radiation grid was too coarse, the tower was nearly invisible, and
the analysis was not the practice's Ladybug + Radiance method. The `server/` and
`web/` trees were removed from `main` in commit `461e344`; the last commit
containing them is `b9d3f37`. The VM continues to run its own checkout until
v2 is deployed and the hostname is repointed.
