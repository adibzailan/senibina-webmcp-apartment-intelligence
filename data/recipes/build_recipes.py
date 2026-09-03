"""Write the plate and 4R recipes as JSON with digests. Usage: .venv/bin/python data/recipes/build_recipes.py"""
from __future__ import annotations

import json
from pathlib import Path

from ai_geometry.plate import build_block87_plate
from ai_geometry.unit_4r import build_4r

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/recipes"


def main():
    precinct = json.loads((ROOT / "data/precinct/dawson-v2.json").read_text())
    b = next(x for x in precinct["buildings"] if x["block"] == "87")
    plate = build_block87_plate(b)
    (OUT / "skyville-block87-plate.recipe.json").write_text(json.dumps(plate.model_dump(mode="json", by_alias=True), indent=1, sort_keys=True) + "\n")
    print("plate", plate.digest())
    for v in "ABC":
        r = build_4r(v)
        (OUT / f"4r-type-{v.lower()}.recipe.json").write_text(json.dumps(r.model_dump(mode="json", by_alias=True), indent=1, sort_keys=True) + "\n")
        print(v, r.digest())


if __name__ == "__main__":
    main()
