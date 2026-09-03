"""Locate Radiance for ladybug-radiance before it is imported.

Order: RADIANCE_PATH env (folder with bin/ and lib/), BINPATH env, repo-local .tools/radiance,
/usr/local/radiance (Docker default). ladybug_radiance reads BINPATH at import time."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def configure() -> str | None:
    cands = []
    if os.environ.get("RADIANCE_PATH"):
        cands.append(Path(os.environ["RADIANCE_PATH"]))
    cands += [ROOT / ".tools/radiance", Path("/usr/local/radiance")]
    for c in cands:
        if (c / "bin" / "gendaymtx").exists():
            os.environ.setdefault("BINPATH", str(c / "bin"))
            os.environ["BINPATH"] = str(c / "bin")
            os.environ["RAYPATH"] = str(c / "lib")
            os.environ["PATH"] = str(c / "bin") + os.pathsep + os.environ.get("PATH", "")
            return str(c)
    if os.environ.get("BINPATH"):
        return os.environ["BINPATH"]
    return None


RADIANCE_HOME = configure()
