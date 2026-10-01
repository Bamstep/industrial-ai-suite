"""Pydantic schemas for the Digital Twin REST & WebSocket API."""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class JointState(BaseModel):
    positions: List[float] = Field(..., description="6-DOF joint angles in radians")
    velocities: List[float] = Field(..., description="6-DOF joint angular velocities in rad/s")
    torques: List[float] = Field(..., description="6-DOF joint torques in Nm")


class PoseCartesian(BaseModel):
    position: List[float] = Field(..., description="Cartesian position [x, y, z] in meters")
    orientation_quat: List[float] = Field(..., description="Orientation quaternion [x, y, z, w]")


class TelemetryResponse(BaseModel):
    timestamp: float
    joints: JointState
    end_effector: PoseCartesian
    workpiece_position: List[float]
    collision_detected: bool


class TrajectoryRequest(BaseModel):
    goal_positions: List[float] = Field(..., min_length=6, max_length=6, description="6-DOF target positions (rad)")
    duration: float = Field(default=1.5, gt=0.0, description="Movement horizon in seconds")


class ServoRequest(BaseModel):
    cycles: int = Field(default=20, ge=1, le=100, description="Number of visual servo loop cycles")


class ServoResponse(BaseModel):
    success: bool
    cycles_executed: int
    initial_error_px: float
    final_error_px: float
    detected: bool
    final_centroid: List[float]