"""Sky matrix via Radiance gendaymtx (Tregenza 145 patches), cached per weather digest."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import radiance_env  # noqa: F401  (configure BINPATH before ladybug_radiance import)
from ladybug_radiance.skymatrix import SkyMatrix

from .weather import DEFAULT_EPW, epw_sha256

CACHE_DIR = Path(__file__).resolve().parents[3] / ".cache" / "sky"


@lru_cache(maxsize=4)
def sky_matrix(epw_path: str | None = None, high_density: bool = True, ground_reflectance: float = 0.2) -> SkyMatrix:
    path = str(epw_path or DEFAULT_EPW)
    sm = SkyMatrix.from_epw(path, high_density=high_density, ground_reflectance=ground_reflectance)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = CACHE_DIR / f"{epw_sha256(path)[:16]}-{int(high_density)}-{ground_reflectance}.json"
    if key.exists():
        d = json.loads(key.read_text())
        sm._metadata = tuple(d["metadata"])  # noqa: SLF001
        sm._direct_values = tuple(d["direct"])  # noqa: SLF001
        sm._diffuse_values = tuple(d["diffuse"])  # noqa: SLF001
        return sm
    sm.compute_sky()
    meta, direct, diffuse = sm.data
    key.write_text(json.dumps({"metadata": [str(m) for m in meta], "direct": list(direct), "diffuse": list(diffuse)}))
    return sm


def sky_record(sm: SkyMatrix) -> dict:
    meta, direct, diffuse = sm.data
    return {"discretisation": "Reinhart" if sm.high_density else "Tregenza", "patches": len(direct), "generator": "Radiance gendaymtx -m 1 -O1 -A (direct -d, diffuse -s)", "ground_reflectance": sm.ground_reflectance, "direct_sum_kwh_m2": round(sum(direct), 3), "diffuse_sum_kwh_m2": round(sum(diffuse), 3)}
