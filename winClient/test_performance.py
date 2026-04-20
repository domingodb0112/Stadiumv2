import cv2
import numpy as np
import time
from segmentation_engine import SegmentationEngine, apply_mask


def benchmark():
    print("[*] Initializing camera and SegmentationEngine...")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    try:
        engine = SegmentationEngine()
    except RuntimeError as e:
        print(f"[!] Model error: {e}")
        cap.release()
        return

    bg = np.zeros((1080, 1920, 3), dtype=np.uint8)
    bg[:, :] = (50, 100, 150)

    frame_count = 0
    total_latency = 0.0
    frame_times = []

    print("[*] Running benchmark for 120 frames...")
    print("-" * 60)

    while frame_count < 120:
        start_time = time.perf_counter()

        ret, frame = cap.read()
        if not ret:
            print("[!] Error reading frame")
            break

        mask = engine.process(frame)
        result = apply_mask(frame, bg, mask, blur_kernel=5)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        fps = 1.0 / (end_time - start_time) if (end_time - start_time) > 0 else 0

        total_latency += latency_ms
        frame_times.append(latency_ms)
        frame_count += 1

        if frame_count % 30 == 0:
            print(f"[Frame {frame_count}] FPS: {fps:.2f} | Latency: {latency_ms:.2f}ms")

    print("-" * 60)

    cap.release()
    engine.release()

    avg_latency = total_latency / frame_count
    avg_fps = frame_count / (total_latency / 1000)

    print(f"\n[RESULTS]")
    print(f"  Total Frames: {frame_count}")
    print(f"  Average FPS: {avg_fps:.2f}")
    print(f"  Average Latency: {avg_latency:.2f}ms")
    print(f"  Min Latency: {min(frame_times):.2f}ms")
    print(f"  Max Latency: {max(frame_times):.2f}ms")

    print(f"\n[QUALITY CHECK]")
    if avg_fps < 24:
        print(f"  ⚠️  WARNING: FPS {avg_fps:.2f} < 24")
        print(f"      → Lower resolution to 1280x720 or 960x540")
    else:
        print(f"  ✓ Performance OK: {avg_fps:.2f} FPS >= 24")


if __name__ == "__main__":
    benchmark()
