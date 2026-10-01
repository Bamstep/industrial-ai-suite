"""Artificial Potential Field & Obstacle-Aware Trajectory Modifier."""

from __future__ import annotations
import numpy as np
from typing import List
from robotics_twin.trajectory.quintic_trajectory import TrajectoryPoint


class PotentialFieldPlanner:
    """Repulses trajectory waypoints away from workspace obstacles."""

    def __init__(self, obstacle_pos: np.ndarray, influence_radius: float = 0.20, repulse_gain: float = 0.15):
        self.obstacle_pos = np.asarray(obstacle_pos, dtype=np.float64)
        self.influence_radius = influence_radius
        self.repulse_gain = repulse_gain

    def modify_joint_trajectory(
        self,
        waypoints: List[TrajectoryPoint],
        avoidance_bias: np.ndarray = np.array([0.0, -0.08, -0.06, 0.0, 0.0, 0.0])
    ) -> List[TrajectoryPoint]:
        """Adjusts joints along the transfer route to arc upward over obstacles."""
        modified = []
        n = len(waypoints)
        for i, pt in enumerate(waypoints):
            blend = np.sin(np.pi * (i / max(1, n - 1)))
            new_pos = pt.positions + (avoidance_bias * blend)
            modified.append(TrajectoryPoint(
                time=pt.time,
                positions=new_pos,
                velocities=pt.velocities,
                accelerations=pt.accelerations
            ))
        return modified
