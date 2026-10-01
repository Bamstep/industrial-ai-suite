"""Tests for Potential Field obstacle replanning and Analytics Logger."""

import numpy as np
import pytest
from robotics_twin.trajectory.quintic_trajectory import QuinticTrajectoryGenerator
from robotics_twin.trajectory.potential_field import PotentialFieldPlanner
from robotics_twin.analytics.logger import AnalyticsLogger


def test_potential_field_trajectory_elevation():
    gen = QuinticTrajectoryGenerator(dof=6)
    q0 = np.zeros(6)
    q1 = np.ones(6) * 0.5
    waypoints = gen.plan_segment(q0, q1, duration=1.0, num_points=50)

    planner = PotentialFieldPlanner(obstacle_pos=np.array([0.22, 0.22, 0.35]))
    modified = planner.modify_joint_trajectory(waypoints)

    assert len(modified) == 50
    # Midpoint should have vertical avoidance bias applied
    mid_orig = waypoints[25].positions
    mid_mod = modified[25].positions
    assert mid_mod[1] < mid_orig[1]


def test_analytics_logger_power_and_csv(tmp_path):
    logger = AnalyticsLogger(output_dir=str(tmp_path))

    for t in np.linspace(0, 1.0, 50):
        power = logger.record_step(
            timestamp=float(t),
            qvel=[0.2] * 6,
            torques=[15.0] * 6,
            collision=False
        )
        assert power > 0.0

    summary = logger.get_summary()
    assert summary["sample_count"] == 50
    assert summary["cumulative_energy_joules"] > 0.0
    assert summary["collision_detected"] is False

    csv_file = logger.export_csv("test_log.csv")
    assert csv_file.exists()
