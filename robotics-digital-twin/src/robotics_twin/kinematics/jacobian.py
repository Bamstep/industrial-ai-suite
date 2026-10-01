"""Geometric Jacobian computation and singularity/manipulability analysis."""

from __future__ import annotations
from typing import Tuple
import numpy as np

from robotics_twin.kinematics.forward_kinematics import SerialManipulator


class KinematicsJacobian:
    """Computes the 6xN Geometric Jacobian and kinematic performance metrics."""

    def __init__(self, manipulator: SerialManipulator):
        self.manipulator = manipulator
        self.dof = manipulator.dof

    def compute_jacobian(self, joint_angles: np.ndarray | list[float]) -> np.ndarray:
        """Compute the 6xN Geometric Jacobian matrix.
        
        Args:
            joint_angles: Joint configuration in radians.
            
        Returns:
            A 6xN numpy ndarray representing linear and angular velocity mappings.
        """
        transforms = self.manipulator.compute_all_transforms(joint_angles)
        p_e = transforms[-1][:3, 3]  # End-effector position

        jacobian = np.zeros((6, self.dof), dtype=np.float64)

        for i in range(self.dof):
            if i == 0:
                # Base frame (frame 0)
                z_prev = np.array([0.0, 0.0, 1.0], dtype=np.float64)
                p_prev = np.array([0.0, 0.0, 0.0], dtype=np.float64)
            else:
                t_prev = transforms[i - 1]
                z_prev = t_prev[:3, 2]  # z-axis is 3rd column
                p_prev = t_prev[:3, 3]  # origin translation

            # Linear velocity Jacobian J_v = z_{i-1} x (p_e - p_{i-1})
            j_v = np.cross(z_prev, (p_e - p_prev))
            # Angular velocity Jacobian J_w = z_{i-1}
            j_w = z_prev

            jacobian[:3, i] = j_v
            jacobian[3:, i] = j_w

        return jacobian

    def manipulability(self, joint_angles: np.ndarray | list[float]) -> float:
        """Compute Yoshikawa's Manipulability Measure w = sqrt(det(J * J^T)).
        
        A value approaching 0 indicates proximity to a kinematic singularity.
        """
        j = self.compute_jacobian(joint_angles)
        jjt = j @ j.T
        det = np.linalg.det(jjt)
        return float(np.sqrt(np.maximum(0.0, det)))

    def condition_number(self, joint_angles: np.ndarray | list[float]) -> float:
        """Compute the condition number of the Jacobian (ratio of max to min singular value).
        
        Values close to 1 represent isotropic dexterity; infinite values denote singularity.
        """
        j = self.compute_jacobian(joint_angles)
        s = np.linalg.svd(j, compute_uv=False)
        if s[-1] < 1e-12:
            return float("inf")
        return float(s[0] / s[-1])