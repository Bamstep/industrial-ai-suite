"""
src/parsers/document_ingestor.py
Handles multi-page engineering drawing documents (PDF, multi-frame TIFF)
and extracts high-resolution rendering arrays for computer vision pipelines.
"""
from io import BytesIO
from typing import List, Tuple
import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageSequence


class DocumentIngestor:
    def __init__(self, target_dpi: int = 300):
        self.target_dpi = target_dpi
        self.scale = target_dpi / 72.0

    def ingest_pdf_bytes(self, pdf_bytes: bytes) -> List[Tuple[int, np.ndarray]]:
        """
        Renders each page of a multi-page PDF into an RGB OpenCV image.
        Returns list of tuples: (page_number, cv2_image_ndarray)
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        matrix = fitz.Matrix(self.scale, self.scale)

        for page_idx in range(len(doc)):
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            img_bgr = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
            pages.append((page_idx + 1, img_bgr))

        return pages

    def ingest_tiff_bytes(self, tiff_bytes: bytes) -> List[Tuple[int, np.ndarray]]:
        """
        Extracts frames from a multi-page TIFF into OpenCV BGR numpy arrays.
        """
        img = Image.open(BytesIO(tiff_bytes))
        pages = []

        for frame_idx, frame in enumerate(ImageSequence.Iterator(img)):
            frame_rgb = frame.convert("RGB")
            frame_np = np.array(frame_rgb)
            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
            pages.append((frame_idx + 1, frame_bgr))

        return pages
