"""NanoTrack single-object tracking (SOT) wrapper.

This module provides a thin wrapper around OpenCV's TrackerNano for efficient
single-object tracking without requiring full detection on every frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2
import numpy as np
from loguru import logger

if TYPE_CHECKING:
    from numpy.typing import NDArray


@dataclass
class NanoParams:
    """Parameters for NanoTrack initialization."""

    backbone: str
    head: str
    backend: int | None = None
    target: int | None = None


class NanoSOT:
    """Single-object tracker using OpenCV's TrackerNano (NanoTrack ONNX).

    This class provides a simple interface to initialize, update, and release
    a NanoTrack tracker instance. It is designed to be used in conjunction with
    YOLO+ByteTrack for improved target continuity and reduced compute.

    Lifecycle:
    1. Create instance with NanoParams
    2. Call init() with frame and bbox when target is locked
    3. Call update() on each frame to get new bbox
    4. Call release() when target is lost or tracking ends
    """

    def __init__(self, params: NanoParams) -> None:
        """Initialize NanoSOT with model parameters.

        Args:
            params: NanoParams with model paths and optional backend/target.
        """
        self._params = params
        self._tracker: cv2.Tracker | None = None
        self._active = False

    def init(
        self, frame: NDArray[np.uint8], bbox_xyxy: tuple[int, int, int, int]
    ) -> bool:
        """Initialize tracker with a frame and bounding box.

        Args:
            frame: Initial frame to seed the tracker.
            bbox_xyxy: Bounding box in (x1, y1, x2, y2) format.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        import os
        import traceback

        x1, y1, x2, y2 = bbox_xyxy
        w, h = max(1, x2 - x1), max(1, y2 - y1)

        try:
            # Diagnostic logging
            logger.debug(
                f"Initializing NanoSOT with bbox=({x1}, {y1}, {x2}, {y2}), size=({w}x{h})"
            )
            logger.debug(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")
            logger.debug(f"Backbone path: {self._params.backbone}")
            logger.debug(f"Head path: {self._params.head}")

            # Check if model files exist
            if not os.path.exists(self._params.backbone):
                logger.error(f"Backbone model not found: {self._params.backbone}")
                return False
            if not os.path.exists(self._params.head):
                logger.error(f"Head model not found: {self._params.head}")
                return False

            logger.debug("Model files found, creating tracker params")
            params = cv2.TrackerNano_Params()
            params.backbone = self._params.backbone
            params.neckhead = self._params.head

            if self._params.backend is not None:
                params.backend = self._params.backend
                logger.debug(f"Using backend: {self._params.backend}")
            if self._params.target is not None:
                params.target = self._params.target
                logger.debug(f"Using target: {self._params.target}")

            logger.debug("Creating TrackerNano instance")
            self._tracker = cv2.TrackerNano_create(params)

            if self._tracker is None:
                logger.error("cv2.TrackerNano_create() returned None")
                return False

            logger.debug(f"Calling tracker.init with bbox=({x1}, {y1}, {w}, {h})")
            # OpenCV TrackerNano.init expects (x, y, w, h)
            # NOTE: TrackerNano.init() returns None (void in C++), not a boolean
            # The method will throw an exception if initialization fails
            self._tracker.init(frame, (x1, y1, w, h))
            self._active = True

            logger.info(
                f"NanoSOT initialized: bbox=({x1}, {y1}, {x2}, {y2}), size=({w}x{h})"
            )

            return True
        except Exception as e:
            logger.error(f"Failed to initialize NanoSOT: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            self._tracker = None
            self._active = False
            return False

    def update(
        self, frame: NDArray[np.uint8]
    ) -> tuple[bool, tuple[int, int, int, int]]:
        """Update tracker with a new frame.

        Args:
            frame: New frame to track on.

        Returns:
            Tuple of (success, bbox_xyxy) where bbox_xyxy is (x1, y1, x2, y2).
            If tracking fails, returns (False, (0, 0, 0, 0)).
        """
        if not self._active or self._tracker is None:
            return False, (0, 0, 0, 0)

        try:
            ok, (x, y, w, h) = self._tracker.update(frame)
            if ok:
                # Convert (x, y, w, h) to (x1, y1, x2, y2)
                return bool(ok), (int(x), int(y), int(x + w), int(y + h))
            return False, (0, 0, 0, 0)
        except Exception as e:
            logger.warning(f"NanoSOT update failed: {e}")
            return False, (0, 0, 0, 0)

    def release(self) -> None:
        """Release tracker resources."""
        if self._tracker is not None:
            logger.debug("NanoSOT released")
        self._tracker = None
        self._active = False

    @property
    def active(self) -> bool:
        """Check if tracker is currently active."""
        return self._active


def _map_backend_str_to_cv2(backend_str: str) -> int | None:
    """Map backend string from config to OpenCV DNN backend constant.

    Args:
        backend_str: Backend name from config (e.g., "default", "cuda", "opencv").

    Returns:
        OpenCV backend constant or None for default.
    """
    backend_map = {
        "default": None,
        "opencv": cv2.dnn.DNN_BACKEND_OPENCV,
        "cuda": cv2.dnn.DNN_BACKEND_CUDA,
        "vulkan": cv2.dnn.DNN_BACKEND_VKCOM,
        "openvino": cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE,
        "halide": cv2.dnn.DNN_BACKEND_HALIDE,
    }
    return backend_map.get(backend_str.lower(), None)


def _map_target_str_to_cv2(target_str: str) -> int | None:
    """Map target string from config to OpenCV DNN target constant.

    Args:
        target_str: Target name from config (e.g., "cpu", "cuda", "opencl").

    Returns:
        OpenCV target constant or None for default.
    """
    target_map = {
        "cpu": cv2.dnn.DNN_TARGET_CPU,
        "cuda": cv2.dnn.DNN_TARGET_CUDA,
        "cuda_fp16": cv2.dnn.DNN_TARGET_CUDA_FP16,
        "opencl": cv2.dnn.DNN_TARGET_OPENCL,
        "opencl_fp16": cv2.dnn.DNN_TARGET_OPENCL_FP16,
        "vulkan": cv2.dnn.DNN_TARGET_VULKAN,
    }
    return target_map.get(target_str.lower(), None)


def create_nano_sot_from_settings(settings: object) -> NanoSOT:
    """Create a NanoSOT instance from Settings object.

    Args:
        settings: Settings object with tracking configuration.

    Returns:
        Configured NanoSOT instance.
    """
    tracking = settings.tracking  # type: ignore[attr-defined]

    backend = _map_backend_str_to_cv2(tracking.dnn_backend)
    target = _map_target_str_to_cv2(tracking.dnn_target)

    params = NanoParams(
        backbone=tracking.nanotrack_backbone_path,
        head=tracking.nanotrack_head_path,
        backend=backend,
        target=target,
    )

    return NanoSOT(params)
