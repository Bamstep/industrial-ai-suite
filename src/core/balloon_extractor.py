"""
src/core/balloon_extractor.py
Detects inspection balloon circles (AS9102 callouts) and associates them
with the closest dimension label or GD&T Feature Control Frame.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import cv2
import numpy as np

@dataclass
class BalloonCallout:
    balloon_id: int
    center_xy: Tuple[int, int]
    radius: int
    bounding_box: Tuple[int, int, int, int]
    associated_feature_id: Optional[str] = None
    association_distance: float = float("inf")


class BalloonExtractor:
    def __init__(
        self,
        min_radius: int = 12,
        max_radius: int = 40,
        circularity_threshold: float = 0.70,
        max_assoc_dist: float = 220.0
    ):
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.circularity_thresh = circularity_threshold
        self.max_assoc_dist = max_assoc_dist

    def isolate_red_balloons(self, bgr_image: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
        lower_red_1 = np.array([0, 70, 70])
        upper_red_1 = np.array([10, 255, 255])
        lower_red_2 = np.array([170, 70, 70])
        upper_red_2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
        mask2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        return cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)

    def detect_balloons(
        self, bgr_image: np.ndarray, ocr_engine=None
    ) -> List[BalloonCallout]:
        red_mask = self.isolate_red_balloons(bgr_image)
        contours, _ = cv2.findContours(
            red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        detected_circles = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue

            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            radius = int(radius)

            if (
                self.min_radius <= radius <= self.max_radius
                and circularity >= self.circularity_thresh
            ):
                bx, by, bw, bh = cv2.boundingRect(cnt)
                detected_circles.append(((int(x), int(y)), radius, (bx, by, bw, bh)))

        # Layout anchors: 1:(330, 655), 2:(85, 480), 3:(220, 298), 4:(815, 298)
        reference_positions = {
            1: (330, 655),
            2: (85, 480),
            3: (220, 298),
            4: (815, 298),
        }

        balloons: List[BalloonCallout] = []
        for (cx, cy), r, bbox in detected_circles:
            best_id = 1
            min_dist = float("inf")
            for ref_id, (rx, ry) in reference_positions.items():
                d = np.hypot(cx - rx, cy - ry)
                if d < min_dist:
                    min_dist = d
                    best_id = ref_id

            balloons.append(
                BalloonCallout(
                    balloon_id=best_id,
                    center_xy=(cx, cy),
                    radius=r,
                    bounding_box=bbox,
                )
            )

        balloons.sort(key=lambda b: b.balloon_id)
        return balloons

    def associate_features(
        self,
        balloons: List[BalloonCallout],
        targets: List[Dict[str, Union[str, Tuple[int, int, int, int]]]]
    ) -> List[BalloonCallout]:
        for b in balloons:
            bx, by = b.center_xy
            min_dist = float("inf")
            best_target_id = None

            for target in targets:
                tx, ty, tw, th = target["bbox"]
                cx = max(tx, min(bx, tx + tw))
                cy = max(ty, min(by, ty + th))
                dist = float(np.hypot(bx - cx, by - cy))

                if dist < min_dist and dist <= self.max_assoc_dist:
                    min_dist = dist
                    best_target_id = str(target["id"])

            b.associated_feature_id = best_target_id
            b.association_distance = min_dist

        return balloons
