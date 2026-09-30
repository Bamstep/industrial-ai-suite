"""
fcf_detector.py
---------------
Precision ASME Y14.5 Feature Control Frame detector.
Detects individual FCF compartment cells and groups horizontally adjacent
cells into unified multi-segment Feature Control Frames.
"""

from dataclasses import dataclass
from typing import List, Tuple
import cv2
import numpy as np


@dataclass
class SegmentedCell:
    cell_index: int
    bounding_box: Tuple[int, int, int, int]
    image_roi: np.ndarray


@dataclass
class DetectedFCF:
    frame_id: str
    bounding_box: Tuple[int, int, int, int]
    frame_roi: np.ndarray
    cells: List[SegmentedCell]


class FeatureControlFrameDetector:
    def __init__(self):
        pass

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        _, binary = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
        return binary

    def is_title_block_zone(self, box: Tuple[int, int, int, int], img_w: int, img_h: int) -> bool:
        x, y, w, h = box
        return x > (img_w - 480) and y > (img_h - 180)

    def find_fcf_cells(self, binary_img: np.ndarray, img_w: int, img_h: int) -> List[Tuple[int, int, int, int]]:
        contours, _ = cv2.findContours(binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cells = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Standard cell dimensions: h between 30 and 40, w between 35 and 150
            if 30 <= h <= 40 and 38 <= w <= 160:
                if not self.is_title_block_zone((x, y, w, h), img_w, img_h):
                    cells.append((x, y, w, h))

        # Sort cells horizontally (left-to-right)
        cells.sort(key=lambda b: (b[1], b[0]))
        return cells

    def cluster_cells_into_frames(
        self,
        cells: List[Tuple[int, int, int, int]]
    ) -> List[List[Tuple[int, int, int, int]]]:
        if not cells:
            return []

        # Group cells that share similar y-coordinates and are directly adjacent
        clusters: List[List[Tuple[int, int, int, int]]] = []
        visited = [False] * len(cells)

        for i in range(len(cells)):
            if visited[i]:
                continue
            curr_cluster = [cells[i]]
            visited[i] = True

            changed = True
            while changed:
                changed = False
                for j in range(len(cells)):
                    if visited[j]:
                        continue
                    cx, cy, cw, ch = cells[j]
                    for bx, by, bw, bh in curr_cluster:
                        # Shared horizontal band (y within 6px) and abutting horizontally (gap <= 8px)
                        if abs(cy - by) <= 6:
                            if abs((bx + bw) - cx) <= 8 or abs((cx + cw) - bx) <= 8:
                                curr_cluster.append(cells[j])
                                visited[j] = True
                                changed = True
                                break

            # An ASME Feature Control Frame must have at least 2 compartments (Symbol + Tolerance Zone)
            if len(curr_cluster) >= 2:
                curr_cluster.sort(key=lambda b: b[0])
                clusters.append(curr_cluster)

        clusters.sort(key=lambda cl: cl[0][0])
        return clusters

    def detect(self, drawing_bgr: np.ndarray) -> List[DetectedFCF]:
        h, w = drawing_bgr.shape[:2]
        binary = self.preprocess(drawing_bgr)
        raw_cells = self.find_fcf_cells(binary, w, h)
        frame_clusters = self.cluster_cells_into_frames(raw_cells)

        detected_fcfs = []
        for idx, cluster in enumerate(frame_clusters):
            x1 = cluster[0][0]
            y1 = min(b[1] for b in cluster)
            x2 = cluster[-1][0] + cluster[-1][2]
            y2 = max(b[1] + b[3] for b in cluster)
            w_box = x2 - x1
            h_box = y2 - y1

            frame_crop = drawing_bgr[y1:y2, x1:x2]

            segmented_cells = []
            for cell_idx, (cx, cy, cw, ch) in enumerate(cluster):
                cell_roi = drawing_bgr[cy:cy+ch, cx:cx+cw]
                segmented_cells.append(
                    SegmentedCell(
                        cell_index=cell_idx,
                        bounding_box=(cx, cy, cw, ch),
                        image_roi=cell_roi
                    )
                )

            detected_fcfs.append(
                DetectedFCF(
                    frame_id=f"FCF-{idx+1:02d}",
                    bounding_box=(x1, y1, w_box, h_box),
                    frame_roi=frame_crop,
                    cells=segmented_cells
                )
            )

        return detected_fcfs
