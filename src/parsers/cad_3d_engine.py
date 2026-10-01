import trimesh
from pathlib import Path
from typing import Dict, Any

class CAD3DEngine:
    @staticmethod
    def generate_synthetic_turbine_rotor(output_path: str = "data/drawings/sample_rotor.stl") -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        hub = trimesh.creation.cylinder(radius=60.0, height=80.0, sections=36)
        shaft = trimesh.creation.cylinder(radius=20.0, height=140.0, sections=24)
        shaft.apply_translation([0, 0, 70])
        flange = trimesh.creation.cylinder(radius=75.0, height=15.0, sections=36)
        flange.apply_translation([0, 0, -40])
        assembly = trimesh.util.concatenate([hub, shaft, flange])
        assembly.export(output_path)
        return output_path

    def load_model(self, file_path_or_bytes: Any, file_type: str = "stl") -> Dict[str, Any]:
        if isinstance(file_path_or_bytes, (str, Path)):
            mesh = trimesh.load(str(file_path_or_bytes), file_type=file_type)
        else:
            mesh = trimesh.load(trimesh.util.wrap_as_stream(file_path_or_bytes), file_type=file_type)

        if isinstance(mesh, trimesh.Scene):
            mesh = mesh.dump(concatenate=True)

        bounds = mesh.bounds.tolist() if hasattr(mesh, "bounds") else [[0,0,0],[0,0,0]]
        extents = mesh.extents.tolist() if hasattr(mesh, "extents") else [0, 0, 0]
        center_mass = mesh.center_mass.tolist() if hasattr(mesh, "center_mass") else [0, 0, 0]
        volume = float(mesh.volume) if hasattr(mesh, "is_watertight") and mesh.is_watertight else float(mesh.convex_hull.volume)
        surface_area = float(mesh.area) if hasattr(mesh, "area") else 0.0

        return {
            "metadata": {
                "vertex_count": len(mesh.vertices),
                "face_count": len(mesh.faces),
                "extents_xyz_mm": [round(x, 3) for x in extents],
                "bounding_box_min": [round(x, 3) for x in bounds[0]],
                "bounding_box_max": [round(x, 3) for x in bounds[1]],
                "center_of_mass": [round(x, 3) for x in center_mass],
                "volume_mm3": round(volume, 2),
                "surface_area_mm2": round(surface_area, 2)
            },
            "mesh_data": {
                "vertices": mesh.vertices.flatten().tolist(),
                "faces": mesh.faces.flatten().tolist()
            }
        }
