from pathlib import Path
from src.parsers.cad_3d_engine import CAD3DEngine

def test_generate_and_parse_3d_mesh():
    engine = CAD3DEngine()
    stl_path = "data/drawings/test_rotor.stl"
    engine.generate_synthetic_turbine_rotor(stl_path)
    assert Path(stl_path).exists()
    result = engine.load_model(stl_path, file_type="stl")
    assert "metadata" in result
    assert "mesh_data" in result
    meta = result["metadata"]
    assert meta["vertex_count"] > 50
    assert meta["face_count"] > 50
    assert len(meta["extents_xyz_mm"]) == 3
    assert meta["volume_mm3"] > 0
