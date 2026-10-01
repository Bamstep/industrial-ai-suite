"""Image-Based Visual Servoing (IBVS) with Eye-in-Hand target tracking."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import cv2
import numpy as np


@dataclass(frozen=True)
class VisualFeature:
    """Detected 2D centroid and bounding area in image coordinates."""
    u: float
    v: float
    area: float
    detected: bool


class VisualServoingController:
    """Computes camera velocity corrections to center and align onto a target workpiece."""

    def __init__(
        self,
        img_width: int = 320,
        img_height: int = 240,
        focal_length: float = 200.0,
        lambda_gain: float = 1.2,
    ):
        self.width = img_width
        self.height = img_height
        self.focal_length = focal_length
        self.lambda_gain = lambda_gain

        # Desired feature location (center of image frame)
        self.u_star = img_width / 2.0
        self.v_star = img_height / 2.0

    def detect_workpiece(self, rgb_image: np.ndarray) -> VisualFeature:
        """Detect the red workpiece centroid using HSV thresholding and spatial moments.
        
        Args:
            rgb_image: (H, W, 3) uint8 image array from eye-in-hand camera.
            
        Returns:
            VisualFeature with centroid (u, v) and detection status.
        """
        hsv = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)

        # Workpiece red mask
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        moments = cv2.moments(mask)
        area = moments["m00"]

        if area > 20:  # Minimum pixel threshold
            u = moments["m10"] / area
            v = moments["m01"] / area
            return VisualFeature(u=float(u), v=float(v), area=float(area), detected=True)

        return VisualFeature(u=self.u_star, v=self.v_star, area=0.0, detected=False)

    def compute_interaction_matrix(
        self, u: float, v: float, depth_z: float = 0.4
    ) -> np.ndarray:
        """Compute the 2x6 Image Jacobian (Interaction Matrix L_s) for a 2D point feature."""
        x = (u - self.u_star) / self.focal_length
        y = (v - self.v_star) / self.focal_length
        z = max(0.05, depth_z)

        l_s = np.array([
            [-self.focal_length / z, 0.0, (u - self.u_star) / z, x * y * self.focal_length, -(self.focal_length + (x**2) * self.focal_length), (v - self.v_star)],
            [0.0, -self.focal_length / z, (v - self.v_star) / z, self.focal_length + (y**2) * self.focal_length, -x * y * self.focal_length, -(u - self.u_star)],
        ], dtype=np.float64)

        return l_s

    def compute_camera_velocity(
        self, feature: VisualFeature, depth_z: float = 0.4
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute task-space 6D camera velocity command v_c = [vx, vy, vz, wx, wy, wz].
        
        Args:
            feature: Current detected VisualFeature.
            depth_z: Estimated distance to workpiece (m).
            
        Returns:
            Tuple of (v_camera_6d, error_2d).
        """
        if not feature.detected:
            return np.zeros(6, dtype=np.float64), np.zeros(2, dtype=np.float64)

        error_2d = np.array([feature.u - self.u_star, feature.v - self.v_star], dtype=np.float64)
        l_s = self.compute_interaction_matrix(feature.u, feature.v, depth_z=depth_z)

        # Damped Moore-Penrose pseudo-inverse: L_s^+ = L_s^T (L_s L_s^T + eps I)^-1
        l_s_pinv = np.linalg.pinv(l_s)
        v_c = -self.lambda_gain * (l_s_pinv @ error_2d)

        return v_c, error_2d