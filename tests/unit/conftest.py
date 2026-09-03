import json
from pathlib import Path

import pytest

from ai_geometry.build import Placement
from ai_geometry.schema import PlateRecipe, UnitRecipe

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def precinct():
    return json.loads((ROOT / "data/precinct/dawson-v2.json").read_text())


@pytest.fixture(scope="session")
def plate():
    return PlateRecipe.model_validate(json.loads((ROOT / "data/recipes/skyville-block87-plate.recipe.json").read_text()))


@pytest.fixture(scope="session")
def units():
    return {v: UnitRecipe.model_validate(json.loads((ROOT / f"data/recipes/4r-type-{v}.recipe.json").read_text())) for v in "abc"}


@pytest.fixture
def placement():
    return Placement(storey=30, facade="NE", stack_position="end", variant="A")
