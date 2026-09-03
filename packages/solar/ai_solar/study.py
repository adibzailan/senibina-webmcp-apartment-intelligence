"""Radiation, direct sun and shadow studies on the analytical mesh via Radiance rcontrib.

Grasshopper-faithful pipeline: Wea -> gendaymtx sky matrix -> rcontrib intersection matrix
(sensor x 290 sky+ground patches, cosine-weighted) -> radiation per sensor (kWh/m2).
Direct sun: sun vectors per timestep -> rcontrib boolean intersection -> hours."""
from __future__ import annotations

import math
import tempfile
from pathlib import Path

import numpy as np
from ladybug_geometry.geometry3d import Mesh3D, Point3D, Vector3D

from . import radiance_env  # noqa: F401
from ladybug_radiance.intersection import intersection_matrix, sky_intersection_matrix

from .sunpath import KEY_DATES, sun_at, sunpath_for

SHADOW_INSTANTS = [(m, d, h) for (m, d) in KEY_DATES for h in (9.0, 12.0, 15.0, 17.0)]


def mesh3d_from_trimesh(mesh) -> Mesh3D:
    verts = [Point3D(*map(float, v)) for v in mesh.vertices]
    faces = [tuple(int(i) for i in f) for f in mesh.faces]
    return Mesh3D(verts, faces)


def _sim_folder(tag: str) -> str:
    d = Path(tempfile.gettempdir()) / "ai-radiance" / tag
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def radiation_study(sky, sensors_xyz, context_mesh3d, tag="rad") -> dict:
    pts = [Point3D(*p) for p in sensors_xyz]
    normals = [Vector3D(0, 0, 1)] * len(pts)
    mtx = sky_intersection_matrix(sky, pts, normals, [context_mesh3d], offset_distance=0.0, numericalize=True, sim_folder=_sim_folder(tag))
    meta, direct, diffuse = sky.data
    sky_rad = np.array(direct) + np.array(diffuse)
    grd = np.full(len(sky_rad), (sky_rad.sum() / len(sky_rad)) * sky.ground_reflectance)
    all_rad = np.concatenate([sky_rad, grd])
    total = np.dot(np.asarray(mtx), all_rad)
    direct_part = np.dot(np.asarray(mtx)[:, : len(sky_rad)], np.array(direct))
    diffuse_part = np.dot(np.asarray(mtx)[:, : len(sky_rad)], np.array(diffuse))
    ground_part = total - direct_part - diffuse_part
    return {"total_kwh_m2": [round(float(v), 4) for v in total], "direct_kwh_m2": [round(float(v), 4) for v in direct_part], "diffuse_kwh_m2": [round(float(v), 4) for v in diffuse_part], "ground_kwh_m2": [round(float(v), 4) for v in ground_part]}


def direct_sun_study(sp, sensors_xyz, context_mesh3d, dates=KEY_DATES, timestep_per_hour=2, tag="sun") -> dict:
    """Direct sun hours per sensor for each key date (half-hour timestep)."""
    pts = [Point3D(*p) for p in sensors_xyz]
    normals = [Vector3D(0, 0, 1)] * len(pts)
    out = {}
    for m, d in dates:
        vecs, hours = [], []
        h = 0.0
        while h < 24.0:
            s = sun_at(sp, m, d, h)
            if s["is_up"] and s["altitude_deg"] > 0.5:
                v = s["vector"]
                vecs.append(Vector3D(-v[0], -v[1], -v[2]))  # toward the sun
                hours.append(h)
            h += 1.0 / timestep_per_hour
        mtx = intersection_matrix(vecs, pts, normals, [context_mesh3d], numericalize=False, sim_folder=_sim_folder(f"{tag}-{m:02d}{d:02d}"))
        arr = np.asarray(mtx, dtype=bool)
        out[f"{m:02d}-{d:02d}"] = {"timestep_per_hour": timestep_per_hour, "sun_hours": [round(float(x) / timestep_per_hour, 3) for x in arr.sum(axis=1)], "instants": hours, "lit_matrix_packed": _pack_bits(arr)}
    return out


def shadow_instants(sp, sensors_xyz, context_mesh3d, instants=SHADOW_INSTANTS, tag="shadow") -> list[dict]:
    pts = [Point3D(*p) for p in sensors_xyz]
    normals = [Vector3D(0, 0, 1)] * len(pts)
    vecs, recs = [], []
    for m, d, h in instants:
        s = sun_at(sp, m, d, h)
        if s["is_up"]:
            v = s["vector"]
            vecs.append(Vector3D(-v[0], -v[1], -v[2]))
            recs.append(s)
    mtx = np.asarray(intersection_matrix(vecs, pts, normals, [context_mesh3d], numericalize=False, sim_folder=_sim_folder(tag)), dtype=bool)
    out = []
    for i, s in enumerate(recs):
        lit = mtx[:, i]
        out.append({**s, "lit_fraction": round(float(lit.mean()), 4) if len(lit) else 0.0, "lit_packed": _pack_bits(lit.reshape(1, -1))})
    return out


def _pack_bits(arr: np.ndarray) -> str:
    """Row-major bit string per row joined by '|' (compact, deterministic, human-checkable)."""
    return "|".join("".join("1" if x else "0" for x in row) for row in np.asarray(arr, dtype=bool))
