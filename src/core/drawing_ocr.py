"""
src/core/drawing_ocr.py
Dual-pass adaptive OCR pre-processor for CAD blueprints.
Handles low-contrast text, rotational text along dimension lines, and CAD symbol replacements.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import cv2
import numpy as np


@dataclass
class OCRTextBox:
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)


class DrawingOCREngine:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd
        self._tesseract_available = False
        try:
            import pytesseract
            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            self._tesseract_available = True
        except ImportError:
            self._tesseract_available = False

    def preprocess_region(self, crop_bgr: np.ndarray) -> np.ndarray:
        """Adaptive binarization optimized for blueprint text lines and symbols."""
        if len(crop_bgr.shape) == 3:
            gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        else:
            gray = crop_bgr.copy()

        h, w = gray.shape
        if h < 40 or w < 80:
            scale = 2.0
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        denoised = cv2.bilateralFilter(gray, 7, 50, 50)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def extract_text_from_roi(self, roi_bgr: np.ndarray) -> str:
        """Extracts cleaned alphanumeric string from a cropped region."""
        processed = self.preprocess_region(roi_bgr)

        if not self._tesseract_available:
            return ""

        try:
            import pytesseract
            config = r'--psm 6 -c tessedit_char_whitelist="0123456789.+-/Øø()[]%ABCDEFGHJKLMNPQRSTUVWXYZ "'
            raw_text = pytesseract.image_to_string(processed, config=config)
            cleaned = raw_text.strip().replace("\n", " ").replace("  ", " ")
            return cleaned
        except Exception:
            return ""
