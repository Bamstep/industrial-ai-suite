"""Damped Least-Squares (Levenberg-Marquardt) Inverse Kinematics solver."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

from robotics_twin.kinematics.forward_kinematics import SerialManipulator
from robotics_twin.kinematics.jacobian import KinematicsJacobian


@dataclass(frozen=True)
class IKResult:
    """Outcome of an Inverse Kinematics solve attempt.
    
    Attributes:
        success: Whether the solver converged within tolerance.
        joint_angles: Solved joint configuration in radians.
        iterations: Number of iterations executed.
        position_error_norm: Final Euclidean translation error (m).
        orientation_error_norm: Final angular error norm (rad).
    """
    success: bool
    joint_angles: np.ndarray
    iterations: int
    position_error_norm: float
    orientation_error_norm: float


class DLSInverseKinematics:
    """Iterative Inverse Kinematics solver using adaptive Damped Least-Squares."""

    def __init__(
        self,
        manipulator: SerialManipulator,
        max_iterations: int = 150,
        pos_tolerance: float = 1e-4,
        rot_tolerance: float = 1e-3,
        damping_max: float = 0.05,
        manipulability_threshold: float = 0.02,
    ):
        self.manipulator = manipulator
        self.jacobian_engine = KinematicsJacobian(manipulator)
        self.max_iterations = max_iterations
        self.pos_tolerance = pos_tolerance
        self.rot_tolerance = rot_tolerance
        self.damping_max = damping_max
        self.manipulability_threshold = manipulability_threshold

    @staticmethod
    def _compute_pose_error(
        current_t: np.ndarray, target_t: np.ndarray
    ) -> Tuple[np.ndarray, float, float]:
        """Compute 6D task-space error vector [e_p, e_o]."""
        # Position error
        e_pos = target_t[:3, 3] - current_t[:3, 3]

        # Orientation error using rotation columns
        r_c = current_t[:3, :3]
        r_d = target_t[:3, :3]

        e_rot = 0.5 * (
            np.cross(r_c[:, 0], r_d[:, 0])
            + np.cross(r_c[:, 1], r_d[:, 1])
            + np.cross(r_c[:, 2], r_d[:, 2])
        )

        error_6d = np.concatenate([e_pos, e_rot])
        pos_norm = float(np.linalg.norm(e_pos))
        rot_norm = float(np.linalg.norm(e_rot))
        return error_6d, pos_norm, rot_norm

    def solve(
        self,
        target_transform: np.ndarray,
        initial_q: Optional[np.ndarray] = None,
    ) -> IKResult:
        """Solve for joint angles matching target_transform SE(3).
        
        Args:
            target_transform: Desired 4x4 homogeneous transformation matrix.
            initial_q: Initial joint seed in radians (defaults to zeros).
            
        Returns:
            IKResult with convergence status and resolved joint angles.
        """
        if initial_q is None:
            q = np.zeros(self.manipulator.dof, dtype=np.float64)
        else:
            q = np.array(initial_q, dtype=np.float64, copy=True)

        for iteration in range(self.max_iterations):
            current_pose = self.manipulator.forward_kinematics(q)
            error_6d, pos_err, rot_err = self._compute_pose_error(
                current_pose.transform_matrix, target_transform
            )

            if pos_err <= self.pos_tolerance and rot_err <= self.rot_tolerance:
                return IKResult(
                    success=True,
                    joint_angles=q,
                    iterations=iteration,
                    position_error_norm=pos_err,
                    orientation_error_norm=rot_err,
                )

            # Compute Jacobian and manipulability
            j = self.jacobian_engine.compute_jacobian(q)
            w = self.jacobian_engine.manipulability(q)

            # Adaptive damping factor lambda
            if w < self.manipulability_threshold:
                lam = self.damping_max * (1.0 - (w / self.manipulability_threshold))
            else:
                lam = 0.0

            # DLS formulation: dq = J^T (J J^T + lambda^2 I)^-1 * error
            damped_identity = (lam**2) * np.eye(6, dtype=np.float64)
            dls_mat = j.T @ np.linalg.inv(j @ j.T + damped_identity)
            dq = dls_mat @ error_6d

            # Step integration with joint limits clamp
            q += dq
            for i, link in enumerate(self.manipulator.links):
                q[i] = np.clip(q[i], link.joint_min, link.joint_max)

        # Final evaluation if iterations exhausted
        final_pose = self.manipulator.forward_kinematics(q)
        _, final_pos_err, final_rot_err = self._compute_pose_error(
            final_pose.transform_matrix, target_transform
        )

        return IKResult(
            success=(final_pos_err <= self.pos_tolerance and final_rot_err <= self.rot_tolerance),
            joint_angles=q,
            iterations=self.max_iterations,
            position_error_norm=final_pos_err,
            orientation_error_norm=final_rot_err,
        )