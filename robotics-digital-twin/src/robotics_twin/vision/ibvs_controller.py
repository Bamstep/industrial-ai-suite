"""Closed-loop Image-Based Visual Servoing (IBVS) with calibrated proportional convergence."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import mujoco
import numpy as np

from robotics_twin.simulation.simulator import MuJoCoSimulator
from robotics_twin.vision.visual_servoing import VisualServoingController, VisualFeature


@dataclass
class VisualServoStepResult:
    """Telemetry of an individual IBVS iteration."""
    iteration: int
    feature: VisualFeature
    error_pixels: np.ndarray
    error_norm: float
    joint_positions: np.ndarray
    camera_velocity: np.ndarray


class ClosedLoopIBVS:
    """Drives the robotic arm to center a workpiece in the eye-in-hand optical frame."""

    def __init__(
        self,
        simulator: MuJoCoSimulator,
        kp_u: float = 0.22,
        kp_v: float = 0.45,
        pixel_tolerance: float = 5.0,
    ):
        self.sim = simulator
        self.vision = VisualServoingController(img_width=320, img_height=240)
        self.kp_u = kp_u
        self.kp_v = kp_v
        self.pixel_tolerance = pixel_tolerance

    def step_servo(self, current_q: np.ndarray, dt: float = 0.05) -> Tuple[np.ndarray, VisualServoStepResult]:
        """Execute a single perception-action step with decoupled visual translation."""
        frame = self.sim.render_eye_in_hand(width=320, height=240)
        feature = self.vision.detect_workpiece(frame)

        if not feature.detected:
            result = VisualServoStepResult(
                iteration=0,
                feature=feature,
                error_pixels=np.array([0.0, 0.0]),
                error_norm=0.0,
                joint_positions=current_q.copy(),
                camera_velocity=np.zeros(6),
            )
            return current_q, result

        # Image error: (u - u*, v - v*)
        du = feature.u - self.vision.u_star
        dv = feature.v - self.vision.v_star
        err_2d = np.array([du, dv])
        error_norm = float(np.linalg.norm(err_2d))

        # Deadband for sub-pixel noise rejection
        if abs(du) < self.pixel_tolerance:
            du = 0.0
        if abs(dv) < self.pixel_tolerance:
            dv = 0.0

        # Normalized camera linear velocities
        norm_u = du / (self.vision.width / 2.0)
        norm_v = dv / (self.vision.height / 2.0)

        vx_c = self.kp_u * norm_u
        vy_c = -self.kp_v * norm_v
        vz_c = 0.0
        v_cam_lin = np.array([vx_c, vy_c, vz_c])

        # Transform from camera frame to world coordinates
        cam_mat = self.sim.data.cam_xmat[self.sim.camera_id].reshape(3, 3)
        v_world_lin = cam_mat @ v_cam_lin

        # Compute translation Jacobian of the end-effector site
        jacp = np.zeros((3, self.sim.model.nv))
        jacr = np.zeros((3, self.sim.model.nv))
        mujoco.mj_jacSite(self.sim.model, self.sim.data, jacp, jacr, self.sim.ee_site_id)
        j_trans = jacp[:, self.sim.arm_dof_indices]

        # Damped Least Squares: J^+ = J^T (J J^T + lambda^2 I)^-1
        damping = 1e-4
        j_dls = j_trans.T @ np.linalg.inv(j_trans @ j_trans.T + damping * np.eye(3))
        dq = j_dls @ v_world_lin

        # Bound joint velocity increments
        dq = np.clip(dq, -0.3, 0.3)
        next_q = current_q + dq * dt

        result = VisualServoStepResult(
            iteration=0,
            feature=feature,
            error_pixels=err_2d,
            error_norm=error_norm,
            joint_positions=next_q.copy(),
            camera_velocity=np.concatenate([v_cam_lin, np.zeros(3)]),
        )

        return next_q, result