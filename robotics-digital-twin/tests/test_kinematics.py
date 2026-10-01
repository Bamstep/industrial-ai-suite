"""Unit tests for DH parameters, Forward Kinematics, Jacobian, and Inverse Kinematics."""

import numpy as np
import pytest

from robotics_twin.kinematics.dh_parameters import DHLink
from robotics_twin.kinematics.forward_kinematics import SerialManipulator
from robotics_twin.kinematics.jacobian import KinematicsJacobian
from robotics_twin.kinematics.inverse_kinematics import DLSInverseKinematics


@pytest.fixture
def ur5_robot() -> SerialManipulator:
    links = [
        DHLink(a=0.0, alpha=np.pi / 2, d=0.089159),
        DHLink(a=-0.425, alpha=0.0, d=0.0),
        DHLink(a=-0.39225, alpha=0.0, d=0.0),
        DHLink(a=0.0, alpha=np.pi / 2, d=0.10915),
        DHLink(a=0.0, alpha=-np.pi / 2, d=0.09465),
        DHLink(a=0.0, alpha=0.0, d=0.0823),
    ]
    return SerialManipulator(links, name="UR5")


def test_dh_link_transformation():
    link = DHLink(a=0.5, alpha=0.0, d=0.2)
    mat = link.transformation_matrix(0.0)
    assert mat.shape == (4, 4)
    assert np.allclose(mat[3, :], [0.0, 0.0, 0.0, 1.0])
    assert np.isclose(mat[0, 3], 0.5)
    assert np.isclose(mat[2, 3], 0.2)


def test_forward_kinematics_orthonormality(ur5_robot):
    q = np.array([0.1, -0.4, 0.8, -1.2, 0.3, -0.5])
    pose = ur5_robot.forward_kinematics(q)

    # R * R^T must equal I
    r = pose.rotation_matrix
    assert np.allclose(r @ r.T, np.eye(3), atol=1e-6)
    assert np.isclose(np.linalg.det(r), 1.0, atol=1e-6)

    # Unit quaternion magnitude must equal 1.0
    assert np.isclose(np.linalg.norm(pose.quaternion), 1.0, atol=1e-6)


def test_jacobian_dimensions_and_manipulability(ur5_robot):
    jac_engine = KinematicsJacobian(ur5_robot)
    q = np.array([0.0, -np.pi / 4, np.pi / 3, -np.pi / 2, np.pi / 4, 0.0])

    j = jac_engine.compute_jacobian(q)
    assert j.shape == (6, 6)

    w = jac_engine.manipulability(q)
    assert w > 0.0
    assert np.isfinite(w)


def test_inverse_kinematics_roundtrip(ur5_robot):
    ik_solver = DLSInverseKinematics(
        ur5_robot, max_iterations=100, pos_tolerance=1e-3, rot_tolerance=1e-2
    )

    q_expected = np.array([0.2, -0.6, 1.0, -0.8, 0.4, -0.1])
    target_pose = ur5_robot.forward_kinematics(q_expected)

    # Solve from small offset seed
    q_seed = q_expected + np.random.uniform(-0.1, 0.1, size=6)
    result = ik_solver.solve(target_pose.transform_matrix, initial_q=q_seed)

    assert result.success is True
    assert result.position_error_norm < 1e-3
    assert result.orientation_error_norm < 1e-2