from typing import List, Tuple
from pydantic import BaseModel


class DefectClusterResponse(BaseModel):
    defect_id: int
    centroid: Tuple[int, int]
    bounding_box: Tuple[int, int, int, int]
    area_pixels: int
    severity: str
    estimated_depth_score: float


class InspectionResponse(BaseModel):
    total_surface_pixels: int
    corrosion_percentage: float
    integrity_status: str
    clusters_detected: int
    defect_clusters: List[DefectClusterResponse]
