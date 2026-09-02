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
        plate = scene.get("result", {}).get("plate")
        if not plate:
            raise ValueError("Floor plate result is required for the v5 export")
        confirmed = rhino3dm.ObjectAttributes(); confirmed.LayerIndex = 2
        confirmed.Name = "Human-confirmed typical apartment floor plate outline"
        confirmed.SetUserString("state", "human-confirmed")
        confirmed.SetUserString("method", "visible first-party confirmation")
        confirmed.SetUserString("assumption", "published typical 4-room reference transformed to the selected facade; not a verified stack")
        confirmed.SetUserString("plan_id", plate["plan"]["plan_id"])
        confirmed.SetUserString("fixture_digest", plate["plan"]["fixture_digest"])
        confirmed.SetUserString("units", "metres")
        confirmed.SetUserString("digest", scene["digest"])
        model.Objects.AddCurve(rhino3dm.PolylineCurve([rhino3dm.Point3d(*point) for point in plate["outline_xyz"]]), confirmed)
        cols, rows = plate["grid"]
        origin = plate["grid_origin_xyz"]
        u_vector = plate["grid_u_vector"]
        v_vector = plate["grid_v_vector"]
        def grid_point(column: int, row: int) -> rhino3dm.Point3d:
            return rhino3dm.Point3d(*(origin[index] + u_vector[index] * column + v_vector[index] * row for index in range(3)))
        for row in range(rows):
            for col in range(cols):
                if not plate["mask"][row * cols + col]:
                    continue
                points = [grid_point(col, row), grid_point(col + 1, row), grid_point(col + 1, row + 1), grid_point(col, row + 1), grid_point(col, row)]
                model.Objects.AddCurve(rhino3dm.PolylineCurve(points), confirmed)

        aperture = plate["aperture"]
        anchor = plate["anchor_xy"]; tangent = plate["wall_direction"]
        floor_z = plate["elevation_m"] - .02
        width = aperture["width_m"]; height = aperture["height_m"]; z0 = floor_z + aperture["sill_m"]
        point = lambda u, v: rhino3dm.Point3d(anchor[0] + tangent[0] * u, anchor[1] + tangent[1] * u, z0 + v)
        window = rhino3dm.PolylineCurve([point(-width / 2, 0), point(width / 2, 0), point(width / 2, height), point(-width / 2, height), point(-width / 2, 0)])
        window_attributes = rhino3dm.ObjectAttributes(); window_attributes.LayerIndex = 2
        window_attributes.Name = "Human-confirmed exterior window aperture"
        window_attributes.SetUserString("state", "human-confirmed")
        window_attributes.SetUserString("method", "visible first-party confirmation")
        window_attributes.SetUserString("digest", scene["digest"])
        model.Objects.AddCurve(window, window_attributes)

        mesh = rhino3dm.Mesh()
        values = scene.get("result", {}).get("radiation", {}).get("sensor_values_kwh_m2", [0.0] * (cols * rows))
        included_values = [value for value, mask in zip(values, plate["mask"]) if mask]
        minimum, maximum = min(included_values), max(included_values)
        for row in range(rows + 1):
            for col in range(cols + 1):
                point = grid_point(col, row)
                vertex = [point.X, point.Y, point.Z]
                mesh.Vertices.Add(*vertex)
                sample = values[min(row, rows - 1) * cols + min(col, cols - 1)]
                ratio = .5 if maximum == minimum else (sample - minimum) / (maximum - minimum)
                red, green, blue = colorsys.hls_to_rgb((45 - ratio * 33) / 360, .55, .78)
                mesh.VertexColors.Add(int(red * 255), int(green * 255), int(blue * 255))
        for row in range(rows):
            for col in range(cols):
                if not plate["mask"][row * cols + col]:
                    continue
                a = row * (cols + 1) + col
                mesh.Faces.AddFace(a, a + 1, a + cols + 2, a + cols + 1)
        generated = rhino3dm.ObjectAttributes(); generated.LayerIndex = 3
        generated.Name = "Generated horizontal radiation sensor mesh"
        generated.SetUserString("state", "generated")
        generated.SetUserString("method", "aperture-gated direct DNI plus isotropic diffuse aperture factor")
        generated.SetUserString("units", "kWh/m2 approximate")
        generated.SetUserString("digest", scene["digest"])
        model.Objects.AddMesh(mesh, generated)

        result = rhino3dm.ObjectAttributes(); result.LayerIndex = 4
        result.Name = "Result digest"
        result.SetUserString("state", "result")
        result.SetUserString("digest", scene["digest"])
        model.Objects.AddTextDot(f"Result {scene['digest']}", rhino3dm.Point3d(anchor[0], anchor[1], z0 + height + 1), result)
    if not model.Write(str(path), 8):
        raise RuntimeError("Failed to write 3dm")
