"""Autonomous Pick-and-Place State Machine coordinating IBVS and Trajectory Generation."""

from __future__ import annotations
import threading
from typing import Callable, Optional
import numpy as np

from robotics_twin.simulation.simulator import MuJoCoSimulator
from robotics_twin.trajectory.quintic_trajectory import QuinticTrajectoryGenerator
from robotics_twin.vision.ibvs_controller import ClosedLoopIBVS


class PickAndPlaceSequencer:
    """Orchestrates an end-to-end industrial pick-and-place routine."""

    def __init__(self, simulator: MuJoCoSimulator, ibvs: ClosedLoopIBVS, render_lock: Optional[threading.RLock] = None):
        self.sim = simulator
        self.ibvs = ibvs
        self.render_lock = render_lock or threading.RLock()
        self.traj_gen = QuinticTrajectoryGenerator(dof=6)

        self.home_pose = np.array([np.pi, -0.828, 0.086, -2.034, 0.0, 0.0])
        # Drop table approach directly at +Y droptable center
        self.drop_approach_pose = np.array([-np.pi / 2.0, -0.95, 0.80, -2.0, 0.0, 0.0])
        # Lower directly onto droptable surface (z ~ 0.44)
        self.drop_deposit_pose = np.array([-np.pi / 2.0, -0.95, 1.35, -2.0, 0.0, 0.0])

    def execute_move(self, target_q: np.ndarray, duration: float = 1.0) -> None:
        current_q = np.array(self.sim.get_telemetry().joint_positions, dtype=np.float64)
        num_steps = max(10, int(duration / 0.002))
        waypoints = self.traj_gen.plan_segment(current_q, target_q, duration=duration, num_points=num_steps)

        for pt in waypoints:
            self.sim.step(target_q=pt.positions, target_dq=pt.velocities)

        for _ in range(25):
            self.sim.step(target_q=target_q)

    def run_full_cycle(self, status_callback: Optional[Callable[[str], None]] = None) -> bool:
        def log(msg: str):
            if status_callback:
                status_callback(msg)

        # Stage 1: Move to Observation / Home Pose
        log("Stage 1/4: Moving to Home Observation Pose...")
        self.sim.set_gripper(False)
        self.execute_move(self.home_pose, duration=0.8)

        # Stage 2: IBVS Visual Alignment
        log("Stage 2/4: Closed-loop IBVS Visual Alignment...")
        current_q = np.array(self.sim.get_telemetry().joint_positions, dtype=np.float64)
        for _ in range(35):
            with self.render_lock:
                current_q, res = self.ibvs.step_servo(current_q, dt=0.05)
            for _ in range(25):
                self.sim.step(target_q=current_q)
            if res.error_norm < 10.0:
                break

        # Stage 3: Cartesian Descent & Magnetic Grasp
        log("Stage 3/4: Descending and grasping workpiece...")
        q_grasp = current_q.copy()
        q_grasp[1] -= 0.12
        q_grasp[2] += 0.18
        self.execute_move(q_grasp, duration=0.6)
        self.sim.set_gripper(True)

        for _ in range(25):
            self.sim.step(target_q=q_grasp)

        # Stage 4: Lift and Transfer to Dropoff Table
        log("Stage 4/4: Transferring to Dropoff Table...")
        self.execute_move(self.home_pose, duration=0.7)
        self.execute_move(self.drop_approach_pose, duration=1.0)
        self.execute_move(self.drop_deposit_pose, duration=0.6)

        # Release gently onto table surface
        self.sim.set_gripper(False)
        for _ in range(35):
            self.sim.step(target_q=self.drop_deposit_pose)

        # Retract back up to approach pose
        self.execute_move(self.drop_approach_pose, duration=0.6)

        log("Cycle Complete: Workpiece successfully transferred.")
        return True
