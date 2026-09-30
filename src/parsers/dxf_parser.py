"""
src/parsers/dxf_parser.py
Parses native AutoCAD / DraftSight DXF vector files to extract
dimension entities, text blocks, leaders, and bounding coordinates.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import ezdxf


@dataclass
class DXFDimensionEntity:
    entity_id: str
    dimension_type: str  # LINEAR, RADIAL, DIAMETER, ANGULAR
    actual_measurement: float
    override_text: str
    defpoint_xy: Tuple[float, float]
    text_midpoint_xy: Tuple[float, float]
    layer: str


class DXFBlueprintParser:
    def __init__(self):
        pass

    def parse_dxf(self, file_path: str) -> List[DXFDimensionEntity]:
        """Reads a DXF file and extracts all native dimension entities."""
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        extracted: List[DXFDimensionEntity] = []

        counter = 1
        for dim in msp.query("DIMENSION"):
            dim_type = dim.dimtype
            meas = float(dim.dxf.get("actual_measurement", 0.0) or 0.0)
            text = str(dim.dxf.get("text", "") or "")
            layer = str(dim.dxf.get("layer", "0"))

            defpoint = dim.dxf.get("defpoint", (0.0, 0.0, 0.0))
            text_midpoint = dim.dxf.get("text_midpoint", (0.0, 0.0, 0.0))

            type_label = "LINEAR"
            if dim_type == 3:
                type_label = "DIAMETER"
            elif dim_type == 4:
                type_label = "RADIAL"
            elif dim_type == 2:
                type_label = "ANGULAR"

            extracted.append(
                DXFDimensionEntity(
                    entity_id=f"DXF-DIM-{counter:02d}",
                    dimension_type=type_label,
                    actual_measurement=meas,
                    override_text=text,
                    defpoint_xy=(float(defpoint[0]), float(defpoint[1])),
                    text_midpoint_xy=(float(text_midpoint[0]), float(text_midpoint[1])),
                    layer=layer,
                )
            )
            counter += 1

        return extracted

    @staticmethod
    def create_synthetic_dxf(output_path: str):
        """Generates a reference DXF test file with stepped flange dimensions."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        msp.add_lwpolyline([
            (200, 360), (550, 360), (550, 420), (680, 420),
            (680, 560), (550, 560), (550, 600), (200, 600), (200, 360)
        ])

        dim = msp.add_linear_dim(
            base=(200, 665),
            p1=(200, 600),
            p2=(680, 600),
            text="620.00 +/- 0.15",
            dimstyle="EZDXF",
        )
        dim.render()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc.saveas(output_path)
        return output_path
