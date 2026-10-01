"""Denavit-Hartenberg (D-H) parameter specification and single-link transformation."""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class DHLink:
    """Represents a single joint-link pair using Standard Denavit-Hartenberg parameters.
    
    Attributes:
        a: Link length along x_i (meters).
        alpha: Link twist about x_i (radians).
        d: Link offset along z_{i-1} (meters).
        theta_offset: Fixed angular offset added to variable theta_i (radians).
        joint_min: Minimum joint travel limit (radians).
        joint_max: Maximum joint travel limit (radians).
    """
    a: float
    alpha: float
    d: float
    theta_offset: float = 0.0
    joint_min: float = -np.pi
    joint_max: float = np.pi

    def transformation_matrix(self, theta: float) -> np.ndarray:
        """Compute the 4x4 homogeneous transformation matrix A_i = ^{i-1}T_i.
        
        Args:
            theta: Variable joint angle (radians).
            
        Returns:
            A 4x4 numpy ndarray representing the SE(3) transformation matrix.
        """
        th = theta + self.theta_offset
        ct, st = np.cos(th), np.sin(th)
        ca, sa = np.cos(self.alpha), np.sin(self.alpha)

        return np.array([
            [ct, -st * ca,  st * sa, self.a * ct],
            [st,  ct * ca, -ct * sa, self.a * st],
            [0.0,      sa,       ca,      self.d],
            [0.0,     0.0,      0.0,         1.0]
        ], dtype=np.float64)