"""Recipe schema `apartment-intelligence.recipe.v1` (closed pydantic models)."""
from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceState = Literal["published", "reconstructed", "inferred", "assumed", "resident_confirmed", "sourced"]
ElementKind = Literal["wall", "column", "opening", "slab", "balcony", "ledge", "overhang", "core", "void", "railing"]
OpacityToken = Literal["context", "tower", "home", "glass"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(Strict):
    state: SourceState
    document: str
    page: str | int | None = None
    calibration_id: str | None = None
    confidence_m: float = Field(ge=0.0, le=5.0)
    note: str | None = None


Point2 = tuple[float, float]


class Element(Strict):
    id: str
    kind: ElementKind
    polyline: list[Point2] | None = None  # centreline for walls, outline for slabs
    rect: tuple[float, float, float, float] | None = None  # x0 y0 x1 y1 in plan frame
    thickness_m: float = Field(default=0.2, ge=0.0, le=2.0)
    base_m: float = Field(default=0.0, ge=-5.0, le=200.0)
    height_m: float = Field(default=2.6, ge=0.0, le=200.0)
    blocks_sun: bool = True
    opacity_token: OpacityToken = "home"
    source: Source
    host_wall: str | None = None  # openings only
    along_m: tuple[float, float] | None = None  # openings: start,end along host wall centreline
    enabled_by_default: bool = True
    room: str | None = None

    @model_validator(mode="after")
    def _geometry_present(self) -> "Element":
        if self.kind == "opening":
            if not self.host_wall or self.along_m is None:
                raise ValueError(f"opening {self.id} needs host_wall and along_m")
            return self
        if self.polyline is None and self.rect is None:
            raise ValueError(f"element {self.id} needs polyline or rect")
        if self.kind == "wall" and (self.polyline is None or len(self.polyline) < 2):
            raise ValueError(f"wall {self.id} needs a polyline of >= 2 points")
        return self


class Room(Strict):
    id: str
    label: str
    polygon: list[Point2]


class UnitRecipe(Strict):
    schema_id: Literal["apartment-intelligence.recipe.v1"] = Field(alias="schema", default="apartment-intelligence.recipe.v1")
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str
    project: str
    unit_type: str
    variant: str
    label: str
    frame_note: str
    envelope: list[Point2]
    frontage_edge: tuple[int, int] = (0, 1)
    storey_height_m: float = 2.8
    elements: list[Element]
    rooms: list[Room]
    source: Source
    limitations: list[str] = []

    def digest(self) -> str:
        return sha256_canonical(self.model_dump(mode="json", by_alias=True))


class Wing(Strict):
    id: str
    label: str
    origin: Point2  # frontage midpoint of the whole wing (outer long edge midpoint)
    axis_deg: float  # direction of the wing long axis (x of wing frame), degrees CCW from east
    inward_deg: float  # direction from frontage toward core (y of wing frame)
    length_m: float
    depth_m: float
    slots: list[dict]  # {"id","unit_type","start_m","width_m"}
    source: Source


class StoreyBand(Strict):
    id: str
    storeys: tuple[int, int]
    kind: Literal["podium", "typical", "sky_garden", "roof"]
    storey_height_m: float
    base_m: float
    top_m: float
    source: Source


class PlateRecipe(Strict):
    schema_id: Literal["apartment-intelligence.recipe.v1"] = Field(alias="schema", default="apartment-intelligence.recipe.v1")
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str
    project: str
    block: str
    address: str
    postal_code: str
    footprint: list[Point2]  # world ENU metres, sourced
    core: list[Point2]
    wings: list[Wing]
    bands: list[StoreyBand]
    storeys: int
    height_published_m: float | None = None
    sky_garden_storeys: list[int]
    overhang_depth_m: float
    source: Source
    limitations: list[str] = []

    def digest(self) -> str:
        return sha256_canonical(self.model_dump(mode="json", by_alias=True))


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_canonical(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def round_floats(obj, ndigits=4):
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, dict):
        return {k: round_floats(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [round_floats(v, ndigits) for v in obj]
    return obj
