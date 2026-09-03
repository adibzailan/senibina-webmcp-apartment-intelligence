from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

from ladybug.epw import EPW

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EPW = ROOT / "data/weather/singapore-changi-2011-2025.epw"


@lru_cache(maxsize=4)
def load_epw(path: str | None = None) -> EPW:
    return EPW(str(path or DEFAULT_EPW))


@lru_cache(maxsize=4)
def epw_sha256(path: str | None = None) -> str:
    return hashlib.sha256(Path(path or DEFAULT_EPW).read_bytes()).hexdigest()


def weather_record(path: str | None = None) -> dict:
    e = load_epw(path)
    return {
        "station": f"{e.location.city} ({e.location.station_id})",
        "source": "Climate.OneBuilding.Org TMYx 2011-2025 (Lawrie & Crawley); citation only, no redistribution licence stated",
        "latitude": e.location.latitude, "longitude": e.location.longitude, "time_zone": e.location.time_zone,
        "period": "TMYx 2011-2025", "sha256": epw_sha256(path), "file": Path(path or DEFAULT_EPW).name,
        "annual_ghi_kwh_m2": round(sum(e.global_horizontal_radiation.values) / 1000.0, 3),
    }
