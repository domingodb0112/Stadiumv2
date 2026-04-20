import cv2
import numpy as np
from pathlib import Path
from typing import Optional
import urllib.request
import mediapipe as mp


class SegmentationEngine:
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"
    MODEL_NAME = "selfie_segmenter.tflite"

    def __init__(self):
        self.model_path = Path(self.MODEL_NAME)
        self._ensure_model()
        self._init_segmenter()
        self._mask_cache = None

    def _ensure_model(self) -> None:
        if self.model_path.exists():
            return
        print(f"[*] Downloading {self.MODEL_NAME}...")
        try:
            urllib.request.urlretrieve(self.MODEL_URL, str(self.model_path))
            print("[✓] Model ready")
        except Exception as e:
            raise RuntimeError(f"Model download failed: {e}")

    def _init_segmenter(self) -> None:
        base_options = mp.tasks.BaseOptions(
            model_asset_path=str(self.model_path)
        )
        options = mp.tasks.vision.ImageSegmenterOptions(
            base_options=base_options,
            output_category_mask=True,
        )
        self.segmenter = mp.tasks.vision.ImageSegmenter.create_from_options(
            options
        )

    def process(self, frame: np.ndarray) -> np.ndarray:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self.segmenter.segment(mp_image)

        mask_view = None
        if hasattr(result, 'confidence_masks') and result.confidence_masks:
            mask_view = result.confidence_masks[0].numpy_view()
        elif hasattr(result, 'category_mask') and result.category_mask:
            mask_view = result.category_mask.numpy_view()
        else:
            print(f"[!] Unknown result structure. Available attributes:")
            for attr in dir(result):
                if not attr.startswith('_'):
                    print(f"    - {attr}")
            raise AttributeError("Cannot extract mask from segmentation result")

        mask = (mask_view > 0.5).astype(np.uint8) * 255
        self._mask_cache = mask
        return mask

    def get_mask(self) -> Optional[np.ndarray]:
        return self._mask_cache

    def release(self) -> None:
        if hasattr(self, "segmenter"):
            del self.segmenter


def apply_mask(
    frame: np.ndarray,
    background: np.ndarray,
    mask: np.ndarray,
    blur_kernel: int = 5,
) -> np.ndarray:
    h, w = frame.shape[:2]
    bg_h, bg_w = background.shape[:2]

    if (bg_h, bg_w) != (h, w):
        background = cv2.resize(background, (w, h))

    mask_norm = mask.astype(np.float32) / 255.0

    if blur_kernel > 0:
        mask_norm = cv2.GaussianBlur(
            mask_norm, (blur_kernel, blur_kernel), 0
        )

    mask_3ch = np.dstack([mask_norm, mask_norm, mask_norm])

    frame_f = frame.astype(np.float32)
    bg_f = background.astype(np.float32)

    result = (frame_f * mask_3ch) + (bg_f * (1.0 - mask_3ch))
    return np.clip(result, 0, 255).astype(np.uint8)
