from dataclasses import dataclass
from typing import List, Tuple
import cv2
import numpy as np


@dataclass
class DefectCluster:
    defect_id: int
    centroid: Tuple[int, int]
    bounding_box: Tuple[int, int, int, int]
    area_pixels: int
    severity: str
    estimated_depth_score: float


@dataclass
class InspectionResult:
    total_surface_pixels: int
    corroded_pixels: int
    corrosion_percentage: float
    defect_clusters: List[DefectCluster]
    integrity_status: str
    annotated_image: np.ndarray


class PipelineCorrosionDetector:
    def __init__(self, pixel_to_mm_ratio: float = 0.5):
        self.pixel_to_mm_ratio = pixel_to_mm_ratio

    def preprocess(self, bgr_image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        enhanced_lab = cv2.merge((cl, a_channel, b_channel))
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        return enhanced_bgr, cl

    def segment_corrosion(self, enhanced_bgr: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2HSV)
        lower_rust = np.array([5, 50, 40], dtype=np.uint8)
        upper_rust = np.array([28, 255, 220], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_rust, upper_rust)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        return mask

    def analyze(self, bgr_image: np.ndarray) -> InspectionResult:
        enhanced_bgr, l_channel = self.preprocess(bgr_image)
        mask = self.segment_corrosion(enhanced_bgr)

        total_pixels = bgr_image.shape[0] * bgr_image.shape[1]
        corroded_pixels = int(np.count_nonzero(mask))
        corrosion_pct = round((corroded_pixels / total_pixels) * 100.0, 2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        clusters: List[DefectCluster] = []
        annotated = bgr_image.copy()

        defect_idx = 1
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 100:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            moments = cv2.moments(cnt)
            cx = int(moments["m10"] / moments["m00"]) if moments["m00"] != 0 else x + w // 2
            cy = int(moments["m01"] / moments["m00"]) if moments["m00"] != 0 else y + h // 2

            roi_l = l_channel[y:y+h, x:x+w]
            mean_l = float(np.mean(roi_l)) if roi_l.size > 0 else 128.0
            depth_score = max(0.0, min(1.0, (180.0 - mean_l) / 140.0))

            if area > 8000 or depth_score > 0.65:
                severity = "CRITICAL"
                box_color = (0, 0, 255)
            elif area > 2000 or depth_score > 0.40:
                severity = "MODERATE"
                box_color = (0, 165, 255)
            else:
                severity = "LOW"
                box_color = (0, 255, 255)

            clusters.append(
                DefectCluster(
                    defect_id=defect_idx,
                    centroid=(cx, cy),
                    bounding_box=(x, y, w, h),
                    area_pixels=int(area),
                    severity=severity,
                    estimated_depth_score=round(depth_score, 2),
                )
            )

            cv2.rectangle(annotated, (x, y), (x + w, y + h), box_color, 2)
            label = f"#{defect_idx} {severity} ({int(area)}px)"
            cv2.putText(
                annotated,
                label,
                (x, max(18, y - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                box_color,
                2,
                cv2.LINE_AA,
            )
            defect_idx += 1

        has_critical = any(c.severity == "CRITICAL" for c in clusters)
        if has_critical or corrosion_pct > 15.0:
            status = "REPAIR_REQUIRED"
        elif corrosion_pct > 2.0 or len(clusters) > 0:
            status = "MONITOR"
        else:
            status = "ACCEPTABLE"

        return InspectionResult(
            total_surface_pixels=total_pixels,
            corroded_pixels=corroded_pixels,
            corrosion_percentage=corrosion_pct,
            defect_clusters=clusters,
            integrity_status=status,
            annotated_image=annotated,
        )
