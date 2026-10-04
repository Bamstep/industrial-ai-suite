from pathlib import Path
import cv2
import numpy as np

def generate_pipeline_samples(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    h, w = 480, 640

    y, x = np.ogrid[:h, :w]
    center_y, center_x = h // 2, w // 2
    dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
    max_dist = np.sqrt(center_x**2 + center_y**2)

    vignette = 1.0 - 0.45 * (dist_from_center / max_dist)
    base_steel = np.full((h, w), 140, dtype=np.float32)
    noise = np.random.normal(0, 8, (h, w))
    clean_pipe = np.clip((base_steel + noise) * vignette, 0, 255).astype(np.uint8)
    clean_bgr = cv2.cvtColor(clean_pipe, cv2.COLOR_GRAY2BGR)
    cv2.imwrite(str(output_dir / "pipe_clean.jpg"), clean_bgr)

    corroded_bgr = clean_bgr.copy()
    rust_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(rust_mask, (220, 200), (90, 50), 25, 0, 360, 255, -1)
    cv2.ellipse(rust_mask, (400, 280), (110, 65), -15, 0, 360, 255, -1)
    rust_mask = cv2.GaussianBlur(rust_mask, (35, 35), 0)

    rust_layer = np.zeros_like(corroded_bgr)
    rust_layer[:, :] = [30, 75, 160]
    rust_noise = np.random.normal(0, 15, (h, w, 3)).astype(np.int16)
    rust_textured = np.clip(rust_layer.astype(np.int16) + rust_noise, 0, 255).astype(np.uint8)

    alpha = (rust_mask.astype(np.float32) / 255.0)[:, :, None]
    corroded_bgr = (corroded_bgr * (1.0 - alpha) + rust_textured * alpha).astype(np.uint8)
    cv2.imwrite(str(output_dir / "pipe_moderate_corrosion.jpg"), corroded_bgr)

    severe_bgr = corroded_bgr.copy()
    cv2.circle(severe_bgr, (230, 210), 22, (15, 25, 55), -1)
    cv2.circle(severe_bgr, (410, 270), 30, (10, 20, 45), -1)
    cv2.circle(severe_bgr, (430, 300), 18, (12, 22, 50), -1)
    severe_bgr = cv2.GaussianBlur(severe_bgr, (5, 5), 0)
    cv2.imwrite(str(output_dir / "pipe_severe_pitting.jpg"), severe_bgr)
    print(f"Generated 3 synthetic pipeline inspection test images in: {output_dir}")

if __name__ == "__main__":
    generate_pipeline_samples(Path("sample_data"))
