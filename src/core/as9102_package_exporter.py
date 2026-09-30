"""
src/core/as9102_package_exporter.py
Generates the complete aerospace AS9102 Revision C 3-Tier FAI package:
- Form 1: Part Number Accountability
- Form 2: Product Process Accountability & Special Processes
- Form 3: Characteristic Accountability & Verification Evaluation
"""
from dataclasses import dataclass
from io import BytesIO
from typing import List, Optional
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from src.core.as9102_exporter import InspectionCharacteristic


@dataclass
class FAIPackageMetadata:
    part_number: str = "FLANGE-7075-T6"
    part_name: str = "STEPPED DRIVE FLANGE"
    drawing_number: str = "DWG-ENG-2026-X41"
    drawing_rev: str = "C"
    po_number: str = "PO-AERO-9982"
    serial_number: str = "SN-2026-0042"
    material: str = "AL 7075-T6 AMS 4045"
    special_processes: str = "Anodize Type II Cl. 1 MIL-A-8625; Heat Treat AMS-H-6088"
    inspector: str = "QC-INSP-04"


class AS9102PackageExporter:
    def __init__(self, metadata: Optional[FAIPackageMetadata] = None):
        self.meta = metadata or FAIPackageMetadata()

    def generate_full_package(self, characteristics: List[InspectionCharacteristic]) -> bytes:
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        hdr_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        hdr_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=13, bold=True, color="1F497D")
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

        # -----------------------------------------------------------------
        # TAB 1: FORM 1 - PART NUMBER ACCOUNTABILITY
        # -----------------------------------------------------------------
        ws1 = wb.create_sheet(title="Form 1 - Part Account")
        ws1.views.sheetView[0].showGridLines = True
        ws1.merge_cells("A1:G1")
        ws1["A1"] = "AS9102 REV C — FORM 1: PART NUMBER ACCOUNTABILITY"
        ws1["A1"].font = title_font
        ws1["A1"].alignment = left_align

        f1_fields = [
            ("A3", "1. Part Number", "B3", self.meta.part_number),
            ("A4", "2. Part Name", "B4", self.meta.part_name),
            ("A5", "3. Serial Number", "B5", self.meta.serial_number),
            ("A6", "4. FAI Report No.", "B6", f"FAI-{self.meta.serial_number}"),
            ("D3", "5. Drawing Number", "E3", self.meta.drawing_number),
            ("D4", "6. Drawing Rev", "E4", self.meta.drawing_rev),
            ("D5", "7. Purchase Order", "E5", self.meta.po_number),
            ("D6", "8. Baseline Status", "E6", "Initial Full FAI"),
        ]
        for l_pos, l_txt, v_pos, v_val in f1_fields:
            ws1[l_pos] = l_txt
            ws1[l_pos].font = sub_font
            ws1[v_pos] = v_val
            ws1[v_pos].font = data_font

        # -----------------------------------------------------------------
        # TAB 2: FORM 2 - PRODUCT PROCESS ACCOUNTABILITY
        # -----------------------------------------------------------------
        ws2 = wb.create_sheet(title="Form 2 - Processes")
        ws2.views.sheetView[0].showGridLines = True
        ws2.merge_cells("A1:F1")
        ws2["A1"] = "AS9102 REV C — FORM 2: PRODUCT PROCESS ACCOUNTABILITY"
        ws2["A1"].font = title_font
        ws2["A1"].alignment = left_align

        f2_headers = [
            ("A3", "Item"), ("B3", "Process / Material Spec"), ("C3", "Specification / Code"),
            ("D3", "Supplier / Source"), ("E3", "Cert # / Ref"), ("F3", "Status")
        ]
        for coord, text in f2_headers:
            ws2[coord] = text
            ws2[coord].font = hdr_font
            ws2[coord].fill = hdr_fill
            ws2[coord].alignment = center_align

        f2_data = [
            (1, "Raw Material", self.meta.material, "AeroMetals Inc.", "CERT-MAT-2026-99", "PASS"),
            (2, "Heat Treatment", "AMS-H-6088 Solution & Age", "ThermalTech Ltd.", "CERT-HT-2026-44", "PASS"),
            (3, "Surface Treatment", "MIL-A-8625 Type II Anodize", "Apex Coating Corp.", "CERT-ANOD-2026-12", "PASS"),
            (4, "Non-Destructive Test", "ASTM E1417 Fluorescent Penetrant", "Apex NDT Labs", "CERT-NDT-2026-07", "PASS"),
        ]
        for r_idx, row in enumerate(f2_data, start=4):
            for c_idx, val in enumerate(row, start=1):
                cell = ws2.cell(row=r_idx, column=c_idx, value=val)
                cell.font = data_font
                cell.border = thin_border
                cell.alignment = center_align if c_idx in [1, 6] else left_align

        # -----------------------------------------------------------------
        # TAB 3: FORM 3 - CHARACTERISTIC ACCOUNTABILITY
        # -----------------------------------------------------------------
        ws3 = wb.create_sheet(title="Form 3 - Characteristics")
        ws3.views.sheetView[0].showGridLines = True
        ws3.merge_cells("A1:J1")
        ws3["A1"] = "AS9102 REV C — FORM 3: CHARACTERISTIC ACCOUNTABILITY & VERIFICATION"
        ws3["A1"].font = title_font

        ws3["A2"] = f"Part Number: {self.meta.part_number}"
        ws3["A2"].font = sub_font
        ws3["E2"] = f"Drawing: {self.meta.drawing_number} Rev {self.meta.drawing_rev}"
        ws3["E2"].font = sub_font

        f3_headers = [
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
        for cell_coord, text in f3_headers:
            c = ws3[cell_coord]
            c.value = text
            c.font = hdr_font
            c.fill = hdr_fill
            c.alignment = center_align

        for r_idx, item in enumerate(characteristics, start=5):
            ws3.cell(row=r_idx, column=1, value=item.char_no).alignment = center_align
            ws3.cell(row=r_idx, column=2, value=item.reference_location).alignment = center_align
            ws3.cell(row=r_idx, column=3, value=item.characteristic_type).alignment = left_align
            ws3.cell(row=r_idx, column=4, value=item.requirement).alignment = left_align
            ws3.cell(row=r_idx, column=5, value=item.nominal).alignment = center_align
            ws3.cell(row=r_idx, column=6, value=item.lower_limit).alignment = center_align
            ws3.cell(row=r_idx, column=7, value=item.upper_limit).alignment = center_align
            ws3.cell(row=r_idx, column=8, value=item.inspection_tool).alignment = left_align
            ws3.cell(row=r_idx, column=9, value=item.results if item.results is not None else "").alignment = center_align
            ws3.cell(row=r_idx, column=10, value=item.pass_fail).alignment = center_align

            for col in range(1, 11):
                c = ws3.cell(row=r_idx, column=col)
                c.font = data_font
                c.border = thin_border

        # Adjust widths on all 3 sheets
        for sheet in [ws1, ws2, ws3]:
            for col in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]:
                sheet.column_dimensions[col].width = 18

        buf = BytesIO()
        wb.save(buf)
        return buf.getvalue()
