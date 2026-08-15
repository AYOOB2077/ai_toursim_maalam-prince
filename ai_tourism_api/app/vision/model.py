"""
LAYER 1 — VISION MODEL
======================
Wraps the trained landmark classifier (best_tourism_model.keras) produced by
final_model.ipynb. Loads the model once at process start and exposes a single
`predict(image_bytes)` method that returns ranked landmark candidates.

Architecture (must match training):
  Input (160, 160, 3) -> MobileNetV3Large (frozen/fine-tuned backbone,
  include_preprocessing=True) -> GlobalAveragePooling2D -> Dropout ->
  Dense(256, relu) -> BatchNormalization -> Dropout -> Dense(num_classes, softmax)

Note: MobileNetV3Large was built with include_preprocessing=True, so raw
0-255 RGB pixel values should be fed in directly — do NOT divide by 255
again here, that would double-normalize and hurt accuracy.
"""
import io
import json
import logging
from typing import Dict, List

import numpy as np
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)


class VisionService:
    def __init__(self, model_path: str, labels_path: str, img_size=(160, 160)):
        self.img_size = img_size
        self.class_names = self._load_labels(labels_path)
        self.model = self._load_model(model_path)

    @staticmethod
    def _load_labels(labels_path: str) -> List[str]:
        with open(labels_path, "r") as f:
            labels_dict = json.load(f)
        return [labels_dict[str(i)] for i in range(len(labels_dict))]

    def _load_model(self, model_path: str):
        # Imported lazily so the rest of the API can start even if TensorFlow
        # is not yet installed in a given environment (e.g. quick local checks).
        from tensorflow import keras  # pyright: ignore [reportMissingTypeStubs]

        # Compatibility patch for Keras 3 deserialization when models contain quantization_config=None
        orig_dense_init = keras.layers.Dense.__init__
        def patched_dense_init(self, *args, **kwargs):
            kwargs.pop("quantization_config", None)
            orig_dense_init(self, *args, **kwargs)
        keras.layers.Dense.__init__ = patched_dense_init

        resolved_path = self._resolve_model_path(model_path)
        logger.info("Loading vision model from %s", resolved_path)
        model = keras.models.load_model(resolved_path)
        expected_classes = model.output_shape[-1]
        if expected_classes != len(self.class_names):
            logger.warning(
                "labels.json has %d classes but the model outputs %d. "
                "Update app/vision/labels.json to match your training classes.",
                len(self.class_names),
                expected_classes,
            )
        return model

    @staticmethod
    def _resolve_model_path(local_fallback_path: str) -> str:
        if settings.VISION_HF_REPO_ID:
            from huggingface_hub import hf_hub_download

            logger.info(
                "Downloading vision model from Hugging Face Hub: %s/%s",
                settings.VISION_HF_REPO_ID,
                settings.VISION_HF_FILENAME,
            )
            return hf_hub_download(
                repo_id=settings.VISION_HF_REPO_ID,
                filename=settings.VISION_HF_FILENAME,
                token=settings.HF_TOKEN or None,
            )
        return local_fallback_path

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(self.img_size)
        arr = np.asarray(img, dtype=np.float32)
        return np.expand_dims(arr, axis=0)

    def predict(self, image_bytes: bytes, top_k: int = 5) -> List[Dict]:
        x = self._preprocess(image_bytes)
        probs = self.model.predict(x, verbose=0)[0]
        top_k = min(top_k, len(probs))
        top_indices = np.argsort(probs)[::-1][:top_k]
        return [
            {"label": self.class_names[i], "confidence": float(probs[i])}
            for i in top_indices
        ]


_vision_service: "VisionService | None" = None


def get_vision_service() -> VisionService:
    """Lazy singleton so the model is loaded once per process (not per request)."""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService(
            model_path=settings.VISION_MODEL_PATH,
            labels_path=settings.VISION_LABELS_PATH,
            img_size=settings.VISION_IMG_SIZE,
        )
    return _vision_service
