import numpy as np
import pytest

from robotics_twin.simulation.mujoco_sim import MuJoCoSimulator
from robotics_twin.vision.servoing import ClosedLoopIBVS
from robotics_twin.tasks.task_sequencer import PickAndPlaceSequencer


def test_pick_and_place_sequencer_execution():
    sim = MuJoCoSimulator()
    q_home = np.array([np.pi, -0.828, 0.086, -2.034, 0.0, 0.0])
    sim.reset(initial_q=q_home)

    for _ in range(30):
        sim.step(target_q=q_home)

    ibvs = ClosedLoopIBVS(sim, kp_u=0.22, kp_v=0.45)
    sequencer = PickAndPlaceSequencer(sim, ibvs)

    success = sequencer.run_full_cycle()
    assert success is True

    t = sim.get_telemetry()
    wp_pos = np.array(t.workpiece_position)

    assert np.isfinite(wp_pos).all()
    # Check that workpiece moved away from initial pick position [0.5, 0.0, 0.425]
    initial_wp = np.array([0.5, 0.0, 0.425])
    distance_moved = np.linalg.norm(wp_pos[:2] - initial_wp[:2])
    assert distance_moved > 0.25
    # Workpiece should remain supported on table surface height (floor is 0.0)
    assert wp_pos[2] > 0.30
