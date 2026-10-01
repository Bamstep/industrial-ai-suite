"""MuJoCo Headless Physics Simulation Engine for 6-DOF Industrial Twin."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import mujoco
import numpy as np


@dataclass
class RobotTelemetry:
    timestamp: float
    joint_positions: List[float]
    joint_velocities: List[float]
    joint_torques: List[float]
    ee_position: List[float]
    ee_orientation: List[float]
    workpiece_position: List[float]
    collision_detected: bool


class MuJoCoSimulator:
    """Headless physical simulator for the 6-DOF UR5 digital twin."""

    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = str(Path(__file__).parent / "models" / "robot_arm.xml")

        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)

        self.renderer = mujoco.Renderer(self.model, height=240, width=320)

        self.arm_dof_indices = np.arange(6)
        self.ee_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "ee_site")
        self.camera_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, "eye_in_hand")
        self.workpiece_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "workpiece")
        self.workpiece_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "workpiece_joint")

        self.wp_qpos_adr = int(self.model.jnt_qposadr[self.workpiece_joint_id])
        self.wp_dof_adr = int(self.model.jnt_dofadr[self.workpiece_joint_id])
        self.eq_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_EQUALITY, "gripper_weld")

        self.kp = np.array([450.0, 450.0, 350.0, 150.0, 100.0, 100.0])
        self.kd = np.array([35.0, 35.0, 25.0, 12.0, 8.0, 8.0])
        self._gripped = False

    def reset(self, initial_q: Optional[np.ndarray] = None) -> None:
        mujoco.mj_resetData(self.model, self.data)
        if initial_q is not None:
            self.data.qpos[:6] = np.asarray(initial_q, dtype=np.float64).copy()
        else:
            self.data.qpos[:6] = 0.0
        self.data.qvel[:6] = 0.0
        self._gripped = False

        self.reset_workpiece(pos=np.array([0.5, 0.0, 0.425]))
        mujoco.mj_forward(self.model, self.data)

    def reset_workpiece(self, pos: np.ndarray = np.array([0.5, 0.0, 0.425])) -> None:
        adr = self.wp_qpos_adr
        v_adr = self.wp_dof_adr
        self.data.qpos[adr:adr+3] = pos
        self.data.qpos[adr+3:adr+7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[v_adr:v_adr+6] = 0.0

    def set_gripper(self, active: bool) -> None:
        self._gripped = active
        if self.eq_id != -1:
            self.data.eq_active[self.eq_id] = 1 if active else 0

        v_adr = self.wp_dof_adr
        self.data.qvel[v_adr:v_adr+6] = 0.0

        adr = self.wp_qpos_adr
        if active:
            ee_pos = self.data.site_xpos[self.ee_site_id].copy()
            self.data.qpos[adr:adr+3] = [ee_pos[0], ee_pos[1], ee_pos[2] - 0.02]
            self.data.qpos[adr+3:adr+7] = [1.0, 0.0, 0.0, 0.0]
        else:
            # Place workpiece stably on top of the drop table (Z = 0.425)
            curr_pos = self.data.qpos[adr:adr+3].copy()
            self.data.qpos[adr:adr+3] = [curr_pos[0], curr_pos[1], 0.425]
            self.data.qpos[adr+3:adr+7] = [1.0, 0.0, 0.0, 0.0]

        mujoco.mj_forward(self.model, self.data)

    def step(self, target_q: np.ndarray, target_dq: Optional[np.ndarray] = None) -> RobotTelemetry:
        if target_dq is None:
            target_dq = np.zeros(6)

        q = self.data.qpos[:6]
        dq = self.data.qvel[:6]
        grav = self.data.qfrc_bias[:6]

        tau = self.kp * (target_q - q) + self.kd * (target_dq - dq) + grav
        tau = np.clip(tau, -250.0, 250.0)

        self.data.ctrl[:6] = tau
        mujoco.mj_step(self.model, self.data)

        if self._gripped:
            ee_pos = self.data.site_xpos[self.ee_site_id].copy()
            adr = self.wp_qpos_adr
            v_adr = self.wp_dof_adr
            self.data.qpos[adr:adr+3] = [ee_pos[0], ee_pos[1], ee_pos[2] - 0.02]
            self.data.qvel[v_adr:v_adr+6] = 0.0
            mujoco.mj_forward(self.model, self.data)

        if not np.all(np.isfinite(self.data.qpos)) or not np.all(np.isfinite(self.data.qvel)):
            self.data.qvel[:] = 0.0
            mujoco.mj_forward(self.model, self.data)

        return self.get_telemetry()

    def render_eye_in_hand(self, width: int = 320, height: int = 240) -> np.ndarray:
        self.renderer.update_scene(self.data, camera=self.camera_id)
        return self.renderer.render()

    def get_telemetry(self) -> RobotTelemetry:
        ee_pos = self.data.site_xpos[self.ee_site_id].copy()
        cam_quat = np.zeros(4)
        mujoco.mju_mat2Quat(cam_quat, self.data.site_xmat[self.ee_site_id])
        wp_pos = self.data.xpos[self.workpiece_body_id].copy()
        has_collision = self.data.ncon > 0

        return RobotTelemetry(
            timestamp=float(self.data.time),
            joint_positions=self.data.qpos[:6].tolist(),
            joint_velocities=self.data.qvel[:6].tolist(),
            joint_torques=self.data.ctrl[:6].tolist(),
            ee_position=ee_pos.tolist(),
            ee_orientation=cam_quat.tolist(),
            workpiece_position=wp_pos.tolist(),
            collision_detected=has_collision,
        )
