"""
src/core/as9102_exporter.py
Generates AS9102 Rev C Form 3 (Characteristic Accountability, Verification and
Compatibility Evaluation) reports in Excel (.xlsx) and CSV formats.
"""
from dataclasses import dataclass
from io import BytesIO
from typing import List, Optional
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import pandas as pd


@dataclass
class InspectionCharacteristic:
    char_no: int               # Col 5: Char No / Balloon No
    reference_location: str    # Col 6: Drawing Sheet & Zone (e.g., "SH1-B3")
    characteristic_type: str   # Col 7: Dimension / Key Characteristic / GD&T
    requirement: str           # Col 8: Specification (Nominal + Limits)
    nominal: float
    lower_limit: float
    upper_limit: float
    inspection_tool: str       # Col 10: Inspection Equipment (CMM, Micrometer, etc.)
    results: Optional[float] = None
    pass_fail: Optional[str] = "PASS"


class AS9102RevCExporter:
    def __init__(self, part_number: str = "FLANGE-7075-T6", part_name: str = "STEPPED FLANGE"):
        self.part_number = part_number
        self.part_name = part_name

    @staticmethod
    def assign_tool(requirement_type: str, tolerance_band: float) -> str:
        """Assign measurement instrument according to tolerance fidelity."""
        req = requirement_type.upper()
        if "GD&T" in req or "POSITION" in req or "PROFILE" in req:
            return "Coordinate Measuring Machine (CMM)"
        elif "FLATNESS" in req or "RUNOUT" in req:
            return "Dial Test Indicator (DTI) & Surface Plate"
        elif tolerance_band <= 0.02:
            return "Digital Micrometer (0.001mm)"
        elif tolerance_band <= 0.10:
            return "Bore Gauge / Vernier Caliper"
        else:
            return "Standard Height Gauge / Caliper"

    def export_csv(self, records: List[InspectionCharacteristic]) -> str:
        data = [
            {
                "Char_No": r.char_no,
                "Reference_Location": r.reference_location,
                "Type": r.characteristic_type,
                "Design_Requirement": r.requirement,
                "Nominal": r.nominal,
                "Lower_Limit": r.lower_limit,
                "Upper_Limit": r.upper_limit,
                "Inspection_Tool": r.inspection_tool,
                "Results": r.results if r.results is not None else "",
                "Status": r.pass_fail,
            }
            for r in records
        ]
        return pd.DataFrame(data).to_csv(index=False)

    def export_excel(self, records: List[InspectionCharacteristic]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Form 3 - Characteristics"
        ws.views.sheetView[0].showGridLines = True

        hdr_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        hdr_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=14, bold=True, color="1F497D")
        sub_font = Font(name="Calibri", size=9, bold=True, color="333333")
        data_font = Font(name="Calibri", size=10)
        thin_border = Border(
            left=Side(style="thin", color="D3D3D3"),
            right=Side(style="thin", color="D3D3D3"),
            top=Side(style="thin", color="D3D3D3"),
            bottom=Side(style="thin", color="D3D3D3"),
        )
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center")

        # Header Block
        ws.merge_cells("A1:J1")
        ws["A1"] = "AS9102 REV C - FORM 3: CHARACTERISTIC ACCOUNTABILITY & VERIFICATION"
        ws["A1"].font = title_font
        ws["A1"].alignment = Alignment(horizontal="left", vertical="center")

        ws["A2"] = f"Part Number: {self.part_number}"
        ws["A2"].font = sub_font
        ws["E2"] = f"Part Name: {self.part_name}"
        ws["E2"].font = sub_font
        ws["H2"] = "Inspection Type: FAI Initial Baseline"
        ws["H2"].font = sub_font

        headers = [
            ("A4", "Char No\n(Col 5)"),
            ("B4", "Ref Loc\n(Col 6)"),
            ("C4", "Char Type\n(Col 7)"),
            ("D4", "Requirement / Specification\n(Col 8)"),
            ("E4", "Nominal"),
            ("F4", "Lower Limit"),
            ("G4", "Upper Limit"),
            ("H4", "Inspection Tool / Method\n(Col 10)"),
            ("I4", "Measured Results\n(Col 9)"),
            ("J4", "Accept / Reject\n(Col 11)"),
        ]

        for cell_coord, text in headers:
            cell = ws[cell_coord]
            cell.value = text
            cell.font = hdr_font
            cell.fill = hdr_fill
            cell.alignment = center_align

        row_idx = 5
        for item in records:
            ws.cell(row=row_idx, column=1, value=item.char_no).alignment = center_align
            ws.cell(row=row_idx, column=2, value=item.reference_location).alignment = center_align
            ws.cell(row=row_idx, column=3, value=item.characteristic_type).alignment = left_align
            ws.cell(row=row_idx, column=4, value=item.requirement).alignment = left_align
            ws.cell(row=row_idx, column=5, value=item.nominal).alignment = center_align
            ws.cell(row=row_idx, column=6, value=item.lower_limit).alignment = center_align
            ws.cell(row=row_idx, column=7, value=item.upper_limit).alignment = center_align
            ws.cell(row=row_idx, column=8, value=item.inspection_tool).alignment = left_align
            ws.cell(row=row_idx, column=9, value=item.results if item.results is not None else "").alignment = center_align
            ws.cell(row=row_idx, column=10, value=item.pass_fail).alignment = center_align

            for col in range(1, 11):
                cell = ws.cell(row=row_idx, column=col)
                cell.font = data_font
                cell.border = thin_border

            row_idx += 1

        widths = {"A": 10, "B": 12, "C": 18, "D": 34, "E": 12, "F": 12, "G": 12, "H": 30, "I": 16, "J": 14}
        for col_letter, width in widths.items():
            ws.column_dimensions[col_letter].width = width

        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
