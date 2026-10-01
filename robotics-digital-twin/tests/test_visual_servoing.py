"""Unit and integration tests for the Visual Servoing (IBVS) pipeline."""

import numpy as np
import pytest

from robotics_twin.simulation.simulator import MuJoCoSimulator
from robotics_twin.vision.visual_servoing import VisualServoingController, VisualFeature
from robotics_twin.vision.ibvs_controller import ClosedLoopIBVS


def test_interaction_matrix_properties():
    controller = VisualServoingController(img_width=320, img_height=240, focal_length=200.0)
    l_s = controller.compute_interaction_matrix(u=160.0, v=120.0, depth_z=0.4)

    assert l_s.shape == (2, 6)
    assert np.all(np.isfinite(l_s))
    assert np.isclose(l_s[0, 1], 0.0)
    assert np.isclose(l_s[1, 0], 0.0)


def test_workpiece_synthetic_detection():
    controller = VisualServoingController(img_width=320, img_height=240)
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    image[140:160, 90:110] = [220, 20, 20]

    feature = controller.detect_workpiece(image)
    assert feature.detected is True
    assert np.isclose(feature.u, 99.5, atol=2.0)
    assert np.isclose(feature.v, 149.5, atol=2.0)
    assert feature.area > 50


def test_closed_loop_ibvs_error_reduction():
    sim = MuJoCoSimulator()
    q_init = np.array([np.pi, -0.828, 0.086, -2.034, 0.0, 0.0])
    sim.reset(initial_q=q_init)

    for _ in range(50):
        sim.step(target_q=q_init)

    ibvs = ClosedLoopIBVS(sim, kp_u=0.22, kp_v=0.45)
    current_q = q_init.copy()

    next_q, res_start = ibvs.step_servo(current_q, dt=0.05)
    assert res_start.feature.detected is True
    initial_error = res_start.error_norm

    # Run 30 servo steps with matched physics simulation
    for _ in range(30):
        next_q, res = ibvs.step_servo(current_q, dt=0.05)
        for _ in range(25):
            sim.step(target_q=next_q)
        current_q = next_q

    assert res.feature.detected is True
    assert res.error_norm < initial_error
