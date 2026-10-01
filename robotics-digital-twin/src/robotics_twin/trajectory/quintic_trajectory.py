"""Quintic (5th-order) polynomial trajectory generator for smooth C2 motion."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass(frozen=True)
class TrajectoryPoint:
    """State of an N-DOF manipulator at time t."""
    time: float
    positions: np.ndarray
    velocities: np.ndarray
    accelerations: np.ndarray


class QuinticTrajectoryGenerator:
    """Generates jerk-continuous multi-joint quintic trajectories."""

    def __init__(self, dof: int = 6):
        self.dof = dof

    def plan_segment(
        self,
        q_start: np.ndarray,
        q_goal: np.ndarray,
        duration: float,
        num_points: int = 100,
        dq_start: np.ndarray | None = None,
        dq_goal: np.ndarray | None = None,
        ddq_start: np.ndarray | None = None,
        ddq_goal: np.ndarray | None = None,
    ) -> List[TrajectoryPoint]:
        """Generate smooth trajectory points from start to goal.
        
        Args:
            q_start: Initial joint coordinates (rad).
            q_goal: Target joint coordinates (rad).
            duration: Total movement time T (seconds).
            num_points: Number of discrete trajectory waypoints to evaluate.
            dq_start, dq_goal: Boundary velocities (rad/s). Defaults to 0.
            ddq_start, ddq_goal: Boundary accelerations (rad/s^2). Defaults to 0.
            
        Returns:
            List of evaluated TrajectoryPoint instances across [0, duration].
        """
        if duration <= 0:
            raise ValueError("Duration must be strictly positive.")

        q0 = np.asarray(q_start, dtype=np.float64)
        q1 = np.asarray(q_goal, dtype=np.float64)
        v0 = np.zeros(self.dof) if dq_start is None else np.asarray(dq_start, dtype=np.float64)
        v1 = np.zeros(self.dof) if dq_goal is None else np.asarray(dq_goal, dtype=np.float64)
        a0 = np.zeros(self.dof) if ddq_start is None else np.asarray(ddq_start, dtype=np.float64)
        a1 = np.zeros(self.dof) if ddq_goal is None else np.asarray(ddq_goal, dtype=np.float64)

        T = float(duration)
        T2, T3, T4, T5 = T**2, T**3, T**4, T**5

        # Closed-form matrix inversion for 5th order polynomial coefficients:
        c0 = q0
        c1 = v0
        c2 = 0.5 * a0

        delta_q = q1 - q0 - v0 * T - 0.5 * a0 * T2
        delta_v = v1 - v0 - a0 * T
        delta_a = a1 - a0

        # Linear solve for [c3, c4, c5]
        m = np.array([
            [T3,     T4,      T5],
            [3 * T2, 4 * T3,  5 * T4],
            [6 * T,  12 * T2, 20 * T3],
        ])
        rhs = np.vstack([delta_q, delta_v, delta_a])
        sol = np.linalg.solve(m, rhs)

        c3, c4, c5 = sol[0], sol[1], sol[2]

        # Sample trajectory points along time horizon
        time_steps = np.linspace(0.0, T, num_points)
        trajectory: List[TrajectoryPoint] = []

        for t in time_steps:
            t2, t3, t4, t5 = t**2, t**3, t**4, t**5
            pos = c0 + c1 * t + c2 * t2 + c3 * t3 + c4 * t4 + c5 * t5
            vel = c1 + 2 * c2 * t + 3 * c3 * t2 + 4 * c4 * t3 + 5 * c5 * t4
            acc = 2 * c2 + 6 * c3 * t + 12 * c4 * t2 + 20 * c5 * t3

            trajectory.append(
                TrajectoryPoint(
                    time=float(t),
                    positions=pos,
                    velocities=vel,
                    accelerations=acc,
                )
            )

        return trajectory