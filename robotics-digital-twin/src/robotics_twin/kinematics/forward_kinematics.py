"""Forward Kinematics computation for serial manipulators."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from scipy.spatial.transform import Rotation as R

from robotics_twin.kinematics.dh_parameters import DHLink


@dataclass(frozen=True)
class EndEffectorPose:
    """End-effector state representation.
    
    Attributes:
        position: Cartesian coordinates [x, y, z] in meters.
        rotation_matrix: 3x3 rotation matrix SO(3).
        quaternion: Unit quaternion [x, y, z, w].
        transform_matrix: 4x4 homogeneous transformation matrix SE(3).
    """
    position: np.ndarray
    rotation_matrix: np.ndarray
    quaternion: np.ndarray
    transform_matrix: np.ndarray


class SerialManipulator:
    """Arbitrary N-DOF serial arm defined by Standard D-H link parameters."""

    def __init__(self, links: List[DHLink], name: str = "6dof_manipulator"):
        self.links = links
        self.dof = len(links)
        self.name = name

    def compute_all_transforms(self, joint_angles: np.ndarray | list[float]) -> List[np.ndarray]:
        """Compute all cumulative transformations from base frame to each frame i (T_0_to_i).
        
        Args:
            joint_angles: Array or list of joint positions in radians (length == dof).
            
        Returns:
            List of 4x4 homogeneous transformation matrices [T_0_1, T_0_2, ..., T_0_n].
        """
        if len(joint_angles) != self.dof:
            raise ValueError(f"Expected {self.dof} joint angles, got {len(joint_angles)}")

        transforms: List[np.ndarray] = []
        cumulative_t = np.eye(4, dtype=np.float64)

        for link, q in zip(self.links, joint_angles):
            a_i = link.transformation_matrix(q)
            cumulative_t = cumulative_t @ a_i
            transforms.append(cumulative_t.copy())

        return transforms

    def forward_kinematics(self, joint_angles: np.ndarray | list[float]) -> EndEffectorPose:
        """Compute the end-effector pose for given joint configuration.
        
        Args:
            joint_angles: Array or list of joint angles in radians.
            
        Returns:
            EndEffectorPose containing position, orientation, and 4x4 transform.
        """
        all_transforms = self.compute_all_transforms(joint_angles)
        t_0_ee = all_transforms[-1]

        position = t_0_ee[:3, 3]
        rot_mat = t_0_ee[:3, :3]
        quaternion = R.from_matrix(rot_mat).as_quat()  # [x, y, z, w]

        return EndEffectorPose(
            position=position,
            rotation_matrix=rot_mat,
            quaternion=quaternion,
            transform_matrix=t_0_ee
        )