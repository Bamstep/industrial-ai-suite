"""Unit and convergence tests for Quintic Trajectory Generation."""

import numpy as np
import pytest

from robotics_twin.trajectory.quintic_trajectory import QuinticTrajectoryGenerator
from robotics_twin.simulation.simulator import MuJoCoSimulator


@pytest.fixture
def simulator():
    sim = MuJoCoSimulator()
    q_start = np.array([np.pi, -0.828, 0.086, -2.034, 0.0, 0.0])
    sim.reset(initial_q=q_start)
    for _ in range(50):
        sim.step(target_q=q_start)
    return sim


def test_trajectory_tracking_convergence(simulator):
    generator = QuinticTrajectoryGenerator(dof=6)
    q_start = np.array([np.pi, -0.828, 0.086, -2.034, 0.0, 0.0])
    q_goal = np.array([np.pi + 0.1, -0.75, 0.15, -1.9, 0.05, -0.05])
    duration = 1.0
    dt_sim = 0.002
    num_steps = int(duration / dt_sim)

    waypoints = generator.plan_segment(
        q_start, q_goal, duration=duration, num_points=num_steps
    )

    for pt in waypoints:
        simulator.step(target_q=pt.positions, target_dq=pt.velocities)

    final_telemetry = None
    for _ in range(120):
        final_telemetry = simulator.step(target_q=q_goal)

    assert final_telemetry is not None
    error = np.abs(np.array(final_telemetry.joint_positions) - q_goal)
    assert np.all(error < 0.03), f"Tracking error exceeded threshold: {error}"
