"""Deterministic writers: GLB (visual, provenance extras), OBJ (analytical), 3DM (professional)."""
from __future__ import annotations

import io
import json

import numpy as np
import trimesh

from .build import Scene, OPACITY


def write_glb(scene: Scene) -> bytes:
    sc = scene.visual_scene()
    data = sc.export(file_type="glb")
    return bytes(data)


def write_obj(mesh: trimesh.Trimesh) -> bytes:
    out = io.StringIO()
    out.write("# apartment-intelligence analytical mesh (blocks_sun elements only)\n")
    for v in mesh.vertices:
        out.write("v %.4f %.4f %.4f\n" % (v[0], v[1], v[2]))
    for f in mesh.faces:
        out.write("f %d %d %d\n" % (f[0] + 1, f[1] + 1, f[2] + 1))
    return out.getvalue().encode("utf-8")


def write_3dm(scene: Scene) -> bytes:
    import rhino3dm as r3

    model = r3.File3dm()
    layers = {}
    for name, rgb in (("context", (150, 150, 150)), ("tower", (120, 130, 150)), ("home", (240, 200, 60)), ("glass", (140, 190, 230)), ("analysis", (220, 60, 60))):
        layer = r3.Layer(); layer.Name = name; layer.Color = rgb + (255,)
        layers[name] = model.Layers.Add(layer)
    for b in sorted(scene.boxes, key=lambda b: b.id):
        m = b.mesh()
        rm = r3.Mesh()
        for v in m.vertices:
            rm.Vertices.Add(float(v[0]), float(v[1]), float(v[2]))
        for f in m.faces:
            rm.Faces.AddFace(int(f[0]), int(f[1]), int(f[2]))
        rm.Normals.ComputeNormals()
        attrs = r3.ObjectAttributes(); attrs.LayerIndex = layers[b.opacity_token]; attrs.Name = b.id
        attrs.SetUserString("provenance", json.dumps(b.extras, sort_keys=True))
        attrs.SetUserString("opacity", str(OPACITY[b.opacity_token]))
        model.Objects.AddMesh(rm, attrs)
    import os, tempfile
    fd, path = tempfile.mkstemp(suffix=".3dm"); os.close(fd)
    try:
        model.Write(path, 8)
        with open(path, "rb") as f:
            return f.read()
    finally:
        os.unlink(path)
