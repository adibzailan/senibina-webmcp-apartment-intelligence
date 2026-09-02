---
title: Font dependency intake
status: accepted
reviewed: 2026-09-02
---

# Font dependency intake

Apartment Intelligence self-hosts two font binaries from the official Google Fonts repository at commit `45b0855d499c093e4d1bd08926fec4e1a582e225`.

| Asset | Publisher and upstream | Licence | Runtime boundary |
|---|---|---|---|
| Newsreader variable roman | Production Type / `productiontype/NewsReader`, redistributed by `google/fonts` | SIL Open Font License 1.1 | Static browser asset only |
| Newsreader variable italic | Production Type / `productiontype/NewsReader`, redistributed by `google/fonts` | SIL Open Font License 1.1 | Static browser asset only |
| Inter variable roman | Rasmus Andersson / `rsms/inter`, redistributed by `google/fonts` | SIL Open Font License 1.1 | Static browser asset only |

The exact upstream metadata names Newsreader and Inter, their publishers, source repositories, and OFL licence. The font files have no package manager, installer, post-install script, build-time execution, runtime network request, or filesystem permission. They are fetched once from the pinned Google Fonts commit, checked with SHA-256, committed, and served from the same origin. No package ecosystem advisory applies to these static font binaries; the upstream repositories showed no active compromise notice during intake. If any checksum changes, stop and repeat intake rather than silently replacing an asset.

Checksums are recorded in `web/public/fonts/SHA256SUMS`. The complete OFL text for each family is retained beside the assets and the copyright notices are included in `THIRD_PARTY_NOTICES.md`.
