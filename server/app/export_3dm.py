from pathlib import Path
import colorsys

import rhino3dm


LAYERS = [
    "01_SOURCED_CONTEXT",
    "02_INFERRED_MASSING",
    "03_HUMAN_CONFIRMED_UNIT",
    "04_GENERATED_ANALYSIS",
    "05_RESULTS",
]


def write_study_3dm(path: Path, scene: dict) -> None:
    model = rhino3dm.File3dm()
    model.Settings.ModelUnitSystem = rhino3dm.UnitSystem.Meters
    for name in LAYERS:
        layer = rhino3dm.Layer()
        layer.Name = name
        model.Layers.Add(layer)
    model.Strings["digest"] = scene["digest"]
    model.Strings["units"] = "metres"
    model.Strings["method"] = scene.get("result", {}).get("method_version", "apartment-intelligence-solar-v2")
    for building in scene.get("buildings", []):
        points = [rhino3dm.Point3d(x, y, 0) for x, y in building["footprint"]]
        curve = rhino3dm.PolylineCurve(points)
        sourced = rhino3dm.ObjectAttributes(); sourced.LayerIndex = 0
        sourced.Name = f"Block {building['block']} sourced footprint"
        sourced.SetUserString("source", "data.gov.sg HDB Existing Building")
        sourced.SetUserString("state", "sourced")
        sourced.SetUserString("units", "metres")
        sourced.SetUserString("digest", scene["digest"])
        model.Objects.AddCurve(curve, sourced)

        inferred = rhino3dm.ObjectAttributes(); inferred.LayerIndex = 1
        inferred.Name = f"Block {building['block']} inferred massing"
        inferred.SetUserString("assumption", "max_floor_level × 3.0 m")
        inferred.SetUserString("state", "inferred")
        inferred.SetUserString("units", "metres")
        inferred.SetUserString("digest", scene["digest"])
        model.Objects.AddExtrusion(rhino3dm.Extrusion.Create(curve, building["height_m"], True), inferred)

    target = scene.get("target")
    if target:
        footprint = target["building"]["footprint"]
        xs = [point[0] for point in footprint]; ys = [point[1] for point in footprint]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        facade = target.get("facade", "east")
        z0 = (target["storey"] - 1) * 3 + target.get("sill_height", .9)
        width = target.get("window_width", 4); height = target.get("window_height", 1.2)
        factor = {"left": .25, "centre": .5, "right": .75}[target.get("position", "centre")]
        if facade in {"east", "west"}:
            fixed = x1 if facade == "east" else x0; centre = y0 + (y1 - y0) * factor
            point = lambda u, v: rhino3dm.Point3d(fixed, centre + u, z0 + v)
        else:
            fixed = y1 if facade == "north" else y0; centre = x0 + (x1 - x0) * factor
            point = lambda u, v: rhino3dm.Point3d(centre + u, fixed, z0 + v)

        window = rhino3dm.PolylineCurve([
            point(-width / 2, 0), point(width / 2, 0), point(width / 2, height),
            point(-width / 2, height), point(-width / 2, 0),
        ])
        confirmed = rhino3dm.ObjectAttributes(); confirmed.LayerIndex = 2
        confirmed.Name = "Human-confirmed target window band"
        confirmed.SetUserString("state", "human-confirmed")
        confirmed.SetUserString("method", "visible first-party confirmation")
        confirmed.SetUserString("digest", scene["digest"])
        model.Objects.AddCurve(window, confirmed)

        cols, rows = 16, 8
        mesh = rhino3dm.Mesh()
        values = scene.get("result", {}).get("radiation", {}).get("sensor_values_kwh_m2", [0.0] * (cols * rows))
        minimum, maximum = min(values), max(values)
        for row in range(rows + 1):
            for col in range(cols + 1):
                vertex = point(-width / 2 + width * col / cols, height * row / rows)
                mesh.Vertices.Add(vertex.X, vertex.Y, vertex.Z)
                sample = values[min(row, rows - 1) * cols + min(col, cols - 1)]
                ratio = .5 if maximum == minimum else (sample - minimum) / (maximum - minimum)
                red, green, blue = colorsys.hls_to_rgb((45 - ratio * 33) / 360, .55, .78)
                mesh.VertexColors.Add(int(red * 255), int(green * 255), int(blue * 255))
        for row in range(rows):
            for col in range(cols):
                a = row * (cols + 1) + col
                mesh.Faces.AddFace(a, a + 1, a + cols + 2, a + cols + 1)
        generated = rhino3dm.ObjectAttributes(); generated.LayerIndex = 3
        generated.Name = "Generated 16 x 8 radiation sensor mesh"
        generated.SetUserString("state", "generated")
        generated.SetUserString("method", "occluded direct DNI plus isotropic DHI")
        generated.SetUserString("units", "kWh/m2 approximate")
        generated.SetUserString("digest", scene["digest"])
        model.Objects.AddMesh(mesh, generated)

        result = rhino3dm.ObjectAttributes(); result.LayerIndex = 4
        result.Name = "Result digest"
        result.SetUserString("state", "result")
        result.SetUserString("digest", scene["digest"])
        model.Objects.AddTextDot(f"Result {scene['digest']}", point(0, height + 1), result)
    if not model.Write(str(path), 8):
        raise RuntimeError("Failed to write 3dm")
