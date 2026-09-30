"""
schema.py
---------
Pydantic data models for ASME Y14.5 GD&T callouts and dimensional characteristics.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ToleranceCategory(str, Enum):
    FORM = "FORM"
    ORIENTATION = "ORIENTATION"
    LOCATION = "LOCATION"
    PROFILE = "PROFILE"
    RUNOUT = "RUNOUT"
    LINEAR = "LINEAR"


class MaterialCondition(str, Enum):
    NONE = "NONE"
    MMC = "MMC"  # Maximum Material Condition (Circle M)
    LMC = "LMC"  # Least Material Condition (Circle L)
    RFS = "RFS"  # Regardless of Feature Size


class DatumReference(BaseModel):
    label: str = Field(..., description="Datum letter (e.g., 'A', 'B', 'C')")
    material_condition: MaterialCondition = MaterialCondition.NONE


class FeatureControlFrame(BaseModel):
    """Represents a segmented ASME Y14.5 GD&T Feature Control Frame (FCF)."""
    characteristic: str = Field(..., description="e.g., 'position', 'perpendicularity'")
    category: ToleranceCategory
    is_diameter_zone: bool = Field(default=False, description="True if tolerance is preceded by Ø")
    tolerance_value: float = Field(..., description="Tolerance band width, e.g., 0.05")
    material_modifier: MaterialCondition = MaterialCondition.NONE
    primary_datum: Optional[DatumReference] = None
    secondary_datum: Optional[DatumReference] = None
    tertiary_datum: Optional[DatumReference] = None
    bounding_box: Optional[List[int]] = Field(default=None, description="[x, y, w, h] on the drawing")


class LinearDimension(BaseModel):
    """Represents standard linear/angular dimensions with tolerances."""
    feature_id: str = Field(..., description="Balloon index or tag, e.g., 'DIM-01'")
    nominal_value: float = Field(..., description="Target dimension value")
    upper_tolerance: float = Field(default=0.0)
    lower_tolerance: float = Field(default=0.0)
    unit: str = Field(default="mm")
    upper_limit: float = 0.0
    lower_limit: float = 0.0
    bounding_box: Optional[List[int]] = None

    def model_post_init(self, __context: Any) -> None:
        object.__setattr__(self, "upper_limit", round(self.nominal_value + self.upper_tolerance, 4))
        object.__setattr__(self, "lower_limit", round(self.nominal_value + self.lower_tolerance, 4))


class InspectionCharacteristicItem(BaseModel):
    """A standardized row item for an AS9102 / FAI Inspection Bill of Characteristics."""
    char_index: int
    char_type: str  # "DIMENSION" or "GDT_FCF"
    description: str
    nominal: Optional[float] = None
    lower_spec_limit: Optional[float] = None
    upper_spec_limit: Optional[float] = None
    gdt_callout: Optional[str] = None
    datums: Optional[str] = None
    measured_value: Optional[float] = None
    status: str = "PENDING"  # PASS, FAIL, PENDING


class DrawingAnalysisResult(BaseModel):
    drawing_name: str
    dimensions: List[LinearDimension] = []
    feature_control_frames: List[FeatureControlFrame] = []
    bill_of_characteristics: List[InspectionCharacteristicItem] = []
