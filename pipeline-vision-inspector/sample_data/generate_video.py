from pathlib import Path
import cv2
import numpy as np


def generate_synthetic_crawler_video(output_file: Path, duration_sec: int = 5, fps: int = 25):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    h, w = 480, 640
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_file), fourcc, fps, (w, h))

    total_frames = duration_sec * fps
    y, x = np.ogrid[:h, :w]
    center_y, center_x = h // 2, w // 2
    dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
    max_dist = np.sqrt(center_x**2 + center_y**2)
    vignette = 1.0 - 0.45 * (dist_from_center / max_dist)

    for i in range(total_frames):
        # Base steel texture
        base_steel = np.full((h, w), 140, dtype=np.float32)
        noise = np.random.normal(0, 7, (h, w))
        frame_gray = np.clip((base_steel + noise) * vignette, 0, 255).astype(np.uint8)
        frame_bgr = cv2.cvtColor(frame_gray, cv2.COLOR_GRAY2BGR)

        # Introduce defect as crawler progresses through frame index
        # Defect enters at frame 40, peaks at frame 80, exits at 110
        if 40 <= i <= 110:
            shift_x = int((i - 40) * 4.5)
            rust_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(rust_mask, (100 + shift_x, 240), (75, 45), 15, 0, 360, 255, -1)
            rust_mask = cv2.GaussianBlur(rust_mask, (25, 25), 0)

            rust_layer = np.zeros_like(frame_bgr)
            rust_layer[:, :] = [30, 75, 160]
            alpha = (rust_mask.astype(np.float32) / 255.0)[:, :, None]
            frame_bgr = (frame_bgr * (1.0 - alpha) + rust_layer * alpha).astype(np.uint8)

            # Severe pit cavity inside rust bloom
            if 65 <= i <= 95:
                cv2.circle(frame_bgr, (100 + shift_x, 240), 20, (15, 25, 55), -1)

        # Add simulated crawler telemetry overlay (HUD)
        chainage = (i / fps) * 0.2
        hud_text = f"ODO: KP {chainage:06.3f} m | FPS: {fps} | CH: B1"
        cv2.putText(frame_bgr, hud_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        out.write(frame_bgr)

    out.release()
    print(f"Generated synthetic crawler inspection run: {output_file} ({total_frames} frames)")


if __name__ == "__main__":
    generate_synthetic_crawler_video(Path("pipeline-vision-inspector/sample_data/crawler_run_sample.mp4"))
