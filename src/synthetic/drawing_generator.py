"""
src/synthetic/drawing_generator.py
Generates technical blueprints with multi-cell FCFs, datums, dimensions,
and dedicated AS9102 inspection balloons (1, 2, 3, 4).
"""
import cv2
import numpy as np
from pathlib import Path


class SyntheticDrawingGenerator:
    def __init__(self, width: int = 1280, height: int = 800):
        self.w = width
        self.h = height

    def _draw_balloon(self, img: np.ndarray, center: tuple, number: int, radius: int = 18):
        """Draw an inspection balloon in red (BGR: 0, 0, 220)."""
        cv2.circle(img, center, radius, (0, 0, 220), 2)
        text = str(number)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        thickness = 2
        (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
        tx = center[0] - tw // 2
        ty = center[1] + th // 2
        cv2.putText(img, text, (tx, ty), font, font_scale, (0, 0, 220), thickness)

    def generate_mechanical_part_drawing(self, output_path: str) -> np.ndarray:
        img = np.ones((self.h, self.w, 3), dtype=np.uint8) * 255

        # Drawing Borders
        cv2.rectangle(img, (40, 40), (self.w - 40, self.h - 40), (40, 40, 40), 2)
        cv2.rectangle(img, (48, 48), (self.w - 48, self.h - 48), (80, 80, 80), 1)

        # Flange Geometry
        cv2.rectangle(img, (200, 360), (550, 600), (30, 30, 30), 2)
        cv2.rectangle(img, (550, 420), (680, 560), (30, 30, 30), 2)

        # Centerline
        cv2.line(img, (150, 480), (730, 480), (220, 100, 100), 1, cv2.LINE_AA)

        # Title Block
        tb_x, tb_y = self.w - 380, self.h - 140
        cv2.rectangle(img, (tb_x, tb_y), (self.w - 48, self.h - 48), (40, 40, 40), 1)
        cv2.line(img, (tb_x, tb_y + 30), (self.w - 48, tb_y + 30), (100, 100, 100), 1)
        cv2.line(img, (tb_x, tb_y + 60), (self.w - 48, tb_y + 60), (100, 100, 100), 1)
        cv2.putText(img, "DWG NO: ENG-2026-X41   REV: C", (tb_x + 12, tb_y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 40, 40), 1)
        cv2.putText(img, "TITLE: STEPPED DRIVE FLANGE", (tb_x + 12, tb_y + 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 40, 40), 1)
        cv2.putText(img, "UNITS: MM | ASME Y14.5M-2018", (tb_x + 12, tb_y + 82), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (60, 60, 60), 1)

        # Datums
        cv2.rectangle(img, (270, 615), (310, 645), (30, 30, 30), 2)
        cv2.putText(img, "-A-", (277, 637), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (30, 30, 30), 2)
        cv2.line(img, (290, 600), (290, 615), (30, 30, 30), 2)

        cv2.rectangle(img, (570, 580), (610, 610), (30, 30, 30), 2)
        cv2.putText(img, "-B-", (577, 602), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (30, 30, 30), 2)
        cv2.line(img, (590, 560), (590, 580), (30, 30, 30), 2)

        # DIMENSION 1: Linear 620.00 +/- 0.15
        cv2.line(img, (200, 665), (680, 665), (50, 50, 50), 1)
        cv2.line(img, (200, 600), (200, 675), (80, 80, 80), 1)
        cv2.line(img, (680, 560), (680, 675), (80, 80, 80), 1)
        cv2.putText(img, "620.00 +/- 0.15", (370, 660), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1)
        self._draw_balloon(img, (330, 655), 1)

        # DIMENSION 2: Diametral Ø320.00 +0.05/-0.00 (Shifted text right, balloon placed to the left)
        cv2.line(img, (135, 360), (135, 600), (50, 50, 50), 1)
        cv2.line(img, (120, 360), (200, 360), (80, 80, 80), 1)
        cv2.line(img, (120, 600), (200, 600), (80, 80, 80), 1)
        cv2.putText(img, "%%C320.00 +0.05/-0.00", (125, 485), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (20, 20, 20), 1)
        self._draw_balloon(img, (85, 480), 2)

        # FCF-01: Flatness
        fcf1_x, fcf1_y = 250, 280
        cv2.rectangle(img, (fcf1_x, fcf1_y), (fcf1_x + 130, fcf1_y + 35), (20, 20, 20), 2)
        cv2.line(img, (fcf1_x + 50, fcf1_y), (fcf1_x + 50, fcf1_y + 35), (20, 20, 20), 2)
        cv2.putText(img, "FLAT", (fcf1_x + 8, fcf1_y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1)
        cv2.putText(img, "0.02", (fcf1_x + 60, fcf1_y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (20, 20, 20), 1)
        cv2.line(img, (fcf1_x + 65, fcf1_y + 35), (fcf1_x + 65, 360), (40, 40, 40), 1)
        self._draw_balloon(img, (fcf1_x - 30, fcf1_y + 18), 3)

        # FCF-02: Position
        fcf2_x, fcf2_y = 560, 280
        cv2.rectangle(img, (fcf2_x, fcf2_y), (fcf2_x + 220, fcf2_y + 35), (20, 20, 20), 2)
        cv2.line(img, (fcf2_x + 45, fcf2_y), (fcf2_x + 45, fcf2_y + 35), (20, 20, 20), 2)
        cv2.line(img, (fcf2_x + 145, fcf2_y), (fcf2_x + 145, fcf2_y + 35), (20, 20, 20), 2)
        cv2.line(img, (fcf2_x + 180, fcf2_y), (fcf2_x + 180, fcf2_y + 35), (20, 20, 20), 2)
        cv2.putText(img, "POS", (fcf2_x + 6, fcf2_y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1)
        cv2.putText(img, "%%C 0.05 (M)", (fcf2_x + 50, fcf2_y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1)
        cv2.putText(img, "A", (fcf2_x + 155, fcf2_y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (20, 20, 20), 2)
        cv2.putText(img, "B", (fcf2_x + 192, fcf2_y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (20, 20, 20), 2)
        cv2.line(img, (fcf2_x + 110, fcf2_y + 35), (fcf2_x + 110, 420), (40, 40, 40), 1)
        self._draw_balloon(img, (fcf2_x + 255, fcf2_y + 18), 4)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(output_path, img)
        return img
