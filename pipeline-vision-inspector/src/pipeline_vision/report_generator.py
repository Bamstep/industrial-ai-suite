import io
from pathlib import Path
from typing import List
import cv2
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as OpenpyxlImage
from pipeline_vision.video_processor import VideoInspectionSummary, AnomalyEvent


def generate_asme_b31g_report(summary: VideoInspectionSummary, output_path: Path | str) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ASME B31G Inspection Audit"

    # Styling definitions
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    section_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    section_font = Font(name="Calibri", size=11, bold=True, color="38BDF8")
    table_header_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    table_header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Document Header
    ws.merge_cells("A1:G1")
    ws["A1"] = "PIPELINE CRAWLER NDT INTEGRITY AUDIT REPORT (ASME B31G / API 570)"
    ws["A1"].font = header_font
    ws["A1"].fill = header_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 40

    # Summary Section
    ws.merge_cells("A3:G3")
    ws["A3"] = "1. EXECUTIVE SURVEY SUMMARY"
    ws["A3"].font = section_font
    ws["A3"].fill = section_fill

    metadata = [
        ("Total Distance Inspected:", f"{summary.total_distance_inspected_m:.3f} meters"),
        ("Survey Duration / Frame Count:", f"{summary.duration_sec}s ({summary.total_frames} frames @ {summary.fps} FPS)"),
        ("Cumulative Anomalies Logged:", f"{len(summary.anomalies)} events"),
        ("Governing Integrity Status:", summary.worst_severity),
    ]

    for r_idx, (label, val) in enumerate(metadata, start=4):
        ws[f"A{r_idx}"] = label
        ws[f"A{r_idx}"].font = Font(bold=True)
        ws[f"C{r_idx}"] = val
        if label == "Governing Integrity Status:":
            color = "EF4444" if val == "REPAIR_REQUIRED" else ("F59E0B" if val == "MONITOR" else "10B981")
            ws[f"C{r_idx}"].font = Font(bold=True, color=color)

    # Anomaly Log Table
    start_row = 9
    ws.merge_cells(f"A{start_row}:G{start_row}")
    ws[f"A{start_row}"] = "2. CHRONOLOGICAL CHAINAGE ANOMALY REGISTER"
    ws[f"A{start_row}"].font = section_font
    ws[f"A{start_row}"].fill = section_fill

    headers = ["Event ID", "Timestamp (s)", "Chainage (KP)", "Severity Level", "Coverage %", "Clusters", "Audit Triage Action"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=start_row + 1, column=col_idx, value=h)
        cell.font = table_header_font
        cell.fill = table_header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    curr_row = start_row + 2
    for a in summary.anomalies:
        action = "Immediate Hydrostatic Recalibration & Sleeving" if a.severity == "REPAIR_REQUIRED" else "Schedule Next-Cycle UT Thickness Scan"
        row_vals = [a.event_id, a.timestamp_sec, f"KP {a.chainage_meters:.3f} m", a.severity, f"{a.corrosion_percentage}%", a.cluster_count, action]
        for c_idx, val in enumerate(row_vals, start=1):
            c = ws.cell(row=curr_row, column=c_idx, value=val)
            c.border = thin_border
            c.alignment = Alignment(horizontal="center" if c_idx != 7 else "left")
            if c_idx == 4:
                c.font = Font(bold=True, color="EF4444" if a.severity == "REPAIR_REQUIRED" else "F59E0B")
        curr_row += 1

    # Keyframe Gallery
    curr_row += 2
    ws.merge_cells(f"A{curr_row}:G{curr_row}")
    ws[f"A{curr_row}"] = "3. CRITICAL DEFECT KEYFRAME EVIDENCE"
    ws[f"A{curr_row}"].font = section_font
    ws[f"A{curr_row}"].fill = section_fill

    curr_row += 2
    img_temp_paths = []
    
    # Take up to 3 worst or representative keyframes
    sample_anomalies = summary.anomalies[:3]
    for i, anom in enumerate(sample_anomalies):
        # Resize thumbnail to fit cleanly
        thumb = cv2.resize(anom.keyframe_bgr, (240, 160))
        t_path = Path(f"_thumb_temp_{i}.jpg")
        cv2.imwrite(str(t_path), thumb)
        img_temp_paths.append(t_path)

        col_letter = chr(ord('A') + (i * 2))
        ws.cell(row=curr_row, column=i * 2 + 1, value=f"Event #{anom.event_id} - KP {anom.chainage_meters:.3f}m ({anom.severity})").font = Font(bold=True, size=9)
        img = OpenpyxlImage(str(t_path))
        ws.add_image(img, f"{col_letter}{curr_row + 1}")

    # Set column widths
    ws.column_dimensions['A'].width = 16
    ws.column_dimensions['B'].width = 16
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 18
    ws.column_dimensions['E'].width = 14
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 42

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)

    # Clean up thumbnail scratch files
    for p in img_temp_paths:
        if p.exists():
            p.unlink()

    return output_path
