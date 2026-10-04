from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import cv2
import numpy as np

from pipeline_vision.detector import PipelineCorrosionDetector, InspectionResult


@dataclass
class AnomalyEvent:
    event_id: int
    frame_number: int
    timestamp_sec: float
    chainage_meters: float  # Linear distance along pipe (KP)
    severity: str
    corrosion_percentage: float
    cluster_count: int
    keyframe_bgr: np.ndarray = field(repr=False)


@dataclass
class VideoInspectionSummary:
    total_frames: int
    fps: float
    duration_sec: float
    total_distance_inspected_m: float
    anomalies: List[AnomalyEvent]
    worst_severity: str


class PipelineVideoInspector:
    def __init__(
        self,
        crawler_speed_mps: float = 0.2,  # Typical crawler travel velocity: 0.2 m/s
        detector: Optional[PipelineCorrosionDetector] = None,
        frame_sample_rate: int = 5,  # Process every 5th frame for high performance
    ):
        self.crawler_speed_mps = crawler_speed_mps
        self.detector = detector or PipelineCorrosionDetector()
        self.frame_sample_rate = frame_sample_rate

    def inspect_video(self, video_path: str | Path) -> VideoInspectionSummary:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Unable to open video stream at: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_frames / fps
        total_distance = duration_sec * self.crawler_speed_mps

        anomalies: List[AnomalyEvent] = []
        frame_idx = 0
        event_counter = 1
        worst_severity = "ACCEPTABLE"

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % self.frame_sample_rate == 0:
                result = self.detector.analyze(frame)
                timestamp = frame_idx / fps
                chainage = timestamp * self.crawler_speed_mps

                if result.integrity_status in ["MONITOR", "REPAIR_REQUIRED"]:
                    anomalies.append(
                        AnomalyEvent(
                            event_id=event_counter,
                            frame_number=frame_idx,
                            timestamp_sec=round(timestamp, 2),
                            chainage_meters=round(chainage, 3),
                            severity=result.integrity_status,
                            corrosion_percentage=result.corrosion_percentage,
                            cluster_count=len(result.defect_clusters),
                            keyframe_bgr=result.annotated_image,
                        )
                    )
                    event_counter += 1

                    if result.integrity_status == "REPAIR_REQUIRED":
                        worst_severity = "REPAIR_REQUIRED"
                    elif worst_severity != "REPAIR_REQUIRED":
                        worst_severity = "MONITOR"

            frame_idx += 1

        cap.release()

        return VideoInspectionSummary(
            total_frames=total_frames,
            fps=fps,
            duration_sec=round(duration_sec, 2),
            total_distance_inspected_m=round(total_distance, 3),
            anomalies=anomalies,
            worst_severity=worst_severity,
        )
