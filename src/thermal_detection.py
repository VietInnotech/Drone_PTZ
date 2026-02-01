"""
Thermal detection service using IR-style contrast-based detection methods.

This module implements thermal/IR detection techniques similar to IR missile seekers:
- Hot spot detection (brightest pixel tracking)
- Blob detection (SimpleBlobDetector with filtering)
- Contour-based detection (most flexible, accurate centroids)

All methods use CLAHE preprocessing for enhanced contrast and support optional
Kalman filtering for smooth centroid tracking.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import cv2
import numpy as np
from loguru import logger


class ThermalDetectionMethod(str, Enum):
    """Available thermal detection methods."""

    HOTSPOT = "hotspot"  # Classic IR seeker - track brightest pixel
    BLOB = "blob"  # SimpleBlobDetector with size/shape filtering
    CONTOUR = "contour"  # Contour-based with precise centroid calculation


@dataclass
class ThermalTarget:
    """Represents a detected thermal target.

    Attributes:
        centroid: (x, y) center position in pixels
        area: Area of the detected region in pixels
        bbox: (x, y, w, h) bounding box
        intensity: Average intensity of the region (0-255)
        track_id: Assigned track ID (for compatibility with existing tracking)
    """

    centroid: tuple[float, float]
    area: float
    bbox: tuple[int, int, int, int]
    intensity: float
    track_id: int | None = None

    @property
    def id(self) -> int | None:
        """Alias for track_id to match YOLO detection interface."""
        return self.track_id

    @property
    def cls(self) -> int:
        """Class ID for compatibility (always 0 for thermal target)."""
        return 0

    @property
    def conf(self) -> float:
        """Confidence score (normalized intensity)."""
        # Normalize intensity (0-255) to 0-1 confidence
        return min(max(self.intensity / 255.0, 0.0), 1.0)

    @property
    def xyxy(self) -> list[list[float]]:
        """Bounding box in YOLO format [[x1, y1, x2, y2]].
        
        Note: The coordinates are NOT normalized here, matching YOLO's .boxes.xyxy behavior
        which returns pixel coordinates in the tensor. Main.py handles normalization
        if values are > 1.0.
        """
        x, y, w, h = self.bbox
        return [[float(x), float(y), float(x + w), float(y + h)]]


class KalmanCentroidTracker:
    """Kalman filter for smooth centroid tracking.

    Uses a constant velocity model to predict and smooth target centroids,
    handling brief occlusions and reducing measurement noise.
    """

    def __init__(self, process_noise: float = 1e-2, measurement_noise: float = 1e-1):
        """Initialize Kalman filter.

        Args:
            process_noise: Process noise covariance (higher = trust measurements more)
            measurement_noise: Measurement noise covariance (higher = smoother output)
        """
        # State: [x, y, vx, vy]
        # Measurement: [x, y]
        self.kf = cv2.KalmanFilter(4, 2)

        # State transition matrix (constant velocity model)
        self.kf.transitionMatrix = np.array(
            [
                [1, 0, 1, 0],
                [0, 1, 0, 1],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ],
            dtype=np.float32,
        )

        # Measurement matrix (we observe x, y only)
        self.kf.measurementMatrix = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float32
        )

        # Process noise covariance
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * process_noise

        # Measurement noise covariance
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * measurement_noise

        # Error covariance (initial uncertainty)
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)

        self._initialized = False

    def predict(self) -> tuple[float, float]:
        """Predict next centroid position.

        Returns:
            Predicted (x, y) centroid position.
        """
        if not self._initialized:
            return (0.0, 0.0)

        prediction = self.kf.predict()
        return (float(prediction[0, 0]), float(prediction[1, 0]))

    def correct(self, measurement: tuple[float, float]) -> tuple[float, float]:
        """Update filter with measurement and return corrected position.

        Args:
            measurement: Observed (x, y) centroid position.

        Returns:
            Corrected (x, y) centroid position.
        """
        if not self._initialized:
            # Initialize state with first measurement
            self.kf.statePost = np.array(
                [[measurement[0]], [measurement[1]], [0], [0]], dtype=np.float32
            )
            self._initialized = True
            return measurement

        # Predict first
        self.kf.predict()

        # Correct with measurement
        measurement_arr = np.array([[measurement[0]], [measurement[1]]], dtype=np.float32)
        corrected = self.kf.correct(measurement_arr)

        return (float(corrected[0, 0]), float(corrected[1, 0]))

    def reset(self) -> None:
        """Reset the filter state."""
        self._initialized = False
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)


class ThermalDetectionService:
    """IR-style thermal detection using contrast-based methods.

    This service provides thermal target detection optimized for grayscale
    thermal camera input. It supports multiple detection methods and optional
    Kalman filtering for smooth tracking.
    """

    def __init__(self, settings: Any | None = None):
        """Initialize the thermal detection service.

        Args:
            settings: Settings object containing thermal configuration.
                     If None, uses default values.
        """
        # Import here to avoid circular imports
        if settings is None:
            from src.settings import load_settings  # noqa: PLC0415

            settings = load_settings()

        self.settings = settings

        # Get thermal settings (with fallback defaults)
        thermal = getattr(settings, "thermal_detection", None)
        if thermal is None:
            thermal = getattr(settings, "thermal", None)
        if thermal is None:
            # Use defaults if thermal settings not configured
            self._method = ThermalDetectionMethod.CONTOUR
            self._threshold = 200
            self._use_otsu = True
            self._clahe_clip = 2.0
            self._clahe_tiles = 8
            self._min_area = 100
            self._max_area = 50000
            self._use_kalman = True
            self._blur_size = 5
        else:
            self._method = ThermalDetectionMethod(thermal.detection_method)
            logger.info(f"ThermalDetectionService initialized with settings method: {self._method}")
            self._threshold = thermal.threshold_value
            self._use_otsu = thermal.use_otsu
            self._clahe_clip = thermal.clahe_clip_limit
            self._clahe_tiles = thermal.clahe_tile_size
            self._min_area = thermal.min_area
            self._max_area = thermal.max_area
            self._use_kalman = thermal.use_kalman
            self._blur_size = getattr(thermal, "blur_size", 5)

        # Initialize CLAHE (Contrast Limited Adaptive Histogram Equalization)
        self._clahe = cv2.createCLAHE(
            clipLimit=self._clahe_clip,
            tileGridSize=(self._clahe_tiles, self._clahe_tiles),
        )

        # Initialize blob detector
        self._blob_detector = self._create_blob_detector()

        # Initialize Kalman trackers (one per tracked target, keyed by ID)
        self._kalman_trackers: dict[int, KalmanCentroidTracker] = {}
        self._next_track_id = 1

        logger.info(
            "ThermalDetectionService initialized: method={}, use_otsu={}, min_area={}, use_kalman={}",
            self._method.value,
            self._use_otsu,
            self._min_area,
            self._use_kalman,
        )

    def _create_blob_detector(self) -> cv2.SimpleBlobDetector:
        """Create and configure SimpleBlobDetector for thermal blobs."""
        params = cv2.SimpleBlobDetector_Params()

        # Filter by color (bright blobs in thermal = hot spots)
        params.filterByColor = True
        params.blobColor = 255  # Detect light (hot) blobs

        # Filter by area
        params.filterByArea = True
        params.minArea = float(self._min_area)
        params.maxArea = float(self._max_area)

        # Filter by circularity (0 = line, 1 = perfect circle)
        params.filterByCircularity = False  # Thermal signatures can be irregular

        # Filter by convexity
        params.filterByConvexity = False

        # Filter by inertia (elongation)
        params.filterByInertia = False

        return cv2.SimpleBlobDetector_create(params)

    def _preprocess(self, frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Preprocess frame with CLAHE enhancement.

        Args:
            frame: Input frame (grayscale or BGR).

        Returns:
            Tuple of (grayscale frame, enhanced frame).
        """
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()

        # Apply Gaussian blur to reduce noise
        if self._blur_size > 0:
            gray = cv2.GaussianBlur(gray, (self._blur_size, self._blur_size), 0)

        # Apply CLAHE for contrast enhancement
        enhanced = self._clahe.apply(gray)

        return gray, enhanced

    def _threshold_image(self, enhanced: np.ndarray) -> np.ndarray:
        """Apply thresholding to create binary mask.

        Args:
            enhanced: CLAHE-enhanced grayscale image.

        Returns:
            Binary mask of hot regions.
        """
        if self._use_otsu:
            # Otsu's automatic thresholding
            _, binary = cv2.threshold(
                enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        else:
            # Fixed threshold
            _, binary = cv2.threshold(
                enhanced, self._threshold, 255, cv2.THRESH_BINARY
            )

        # Morphological operations to clean up noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)  # Remove noise
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)  # Fill gaps

        return binary

    def _detect_hotspot(
        self, gray: np.ndarray, enhanced: np.ndarray
    ) -> list[ThermalTarget]:
        """Detect using hottest pixel (classic IR seeker approach).

        Args:
            gray: Original grayscale image.
            enhanced: CLAHE-enhanced image.

        Returns:
            List with single target at hottest pixel.
        """
        # Find maximum intensity location
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(enhanced)

        if max_val < self._threshold:
            return []

        # Create a small region around the hotspot
        x, y = max_loc
        half_size = 10  # Default region size

        # Estimate area from local hot region
        binary = self._threshold_image(enhanced)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        area = 100.0  # Default area
        bbox = (x - half_size, y - half_size, half_size * 2, half_size * 2)

        # Find contour containing the hotspot
        for contour in contours:
            if cv2.pointPolygonTest(contour, (float(x), float(y)), False) >= 0:
                area = cv2.contourArea(contour)
                bx, by, bw, bh = cv2.boundingRect(contour)
                bbox = (bx, by, bw, bh)
                break

        target = ThermalTarget(
            centroid=(float(x), float(y)),
            area=area,
            bbox=bbox,
            intensity=float(max_val),
            track_id=None,
        )

        return [target]

    def _detect_blob(
        self, gray: np.ndarray, enhanced: np.ndarray
    ) -> list[ThermalTarget]:
        """Detect using SimpleBlobDetector.

        Args:
            gray: Original grayscale image.
            enhanced: CLAHE-enhanced image.

        Returns:
            List of detected thermal targets.
        """
        # Invert for blob detection (expects dark blobs on light background)
        # We use blobColor=255 so we detect bright spots directly
        keypoints = self._blob_detector.detect(enhanced)

        targets = []
        for kp in keypoints:
            x, y = kp.pt
            size = kp.size
            half_size = int(size / 2)

            # Calculate intensity at blob center
            ix, iy = int(x), int(y)
            h, w = enhanced.shape[:2]
            if 0 <= ix < w and 0 <= iy < h:
                intensity = float(enhanced[iy, ix])
            else:
                intensity = 0.0

            target = ThermalTarget(
                centroid=(x, y),
                area=np.pi * (size / 2) ** 2,  # Approximate circular area
                bbox=(
                    max(0, int(x) - half_size),
                    max(0, int(y) - half_size),
                    int(size),
                    int(size),
                ),
                intensity=intensity,
                track_id=None,
            )
            targets.append(target)

        return targets

    def _detect_contour(
        self, gray: np.ndarray, enhanced: np.ndarray
    ) -> list[ThermalTarget]:
        """Detect using contour analysis with precise centroids.

        Args:
            gray: Original grayscale image.
            enhanced: CLAHE-enhanced image.

        Returns:
            List of detected thermal targets with accurate centroids.
        """
        binary = self._threshold_image(enhanced)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        targets = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by area
            if area < self._min_area or area > self._max_area:
                continue

            # Calculate centroid using image moments
            moments = cv2.moments(contour)
            if moments["m00"] == 0:
                continue

            cx = moments["m10"] / moments["m00"]
            cy = moments["m01"] / moments["m00"]

            # Get bounding box
            bx, by, bw, bh = cv2.boundingRect(contour)

            # Calculate average intensity within contour
            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            intensity = cv2.mean(gray, mask=mask)[0]

            target = ThermalTarget(
                centroid=(cx, cy),
                area=area,
                bbox=(bx, by, bw, bh),
                intensity=intensity,
                track_id=None,
            )
            targets.append(target)

        # Sort by area (largest first) - usually the primary target
        targets.sort(key=lambda t: t.area, reverse=True)

        return targets

    def detect(self, frame: np.ndarray) -> list[ThermalTarget]:
        """Detect thermal targets in a frame.

        Args:
            frame: Input frame (grayscale thermal image preferred).

        Returns:
            List of detected ThermalTarget objects with centroids.
        """
        if frame is None or frame.size == 0:
            logger.warning("Invalid frame provided to ThermalDetectionService.detect()")
            return []

        try:
            # Preprocess with CLAHE
            gray, enhanced = self._preprocess(frame)

            # Detect using configured method
            if self._method == ThermalDetectionMethod.HOTSPOT:
                targets = self._detect_hotspot(gray, enhanced)
            elif self._method == ThermalDetectionMethod.BLOB:
                targets = self._detect_blob(gray, enhanced)
            else:  # CONTOUR
                targets = self._detect_contour(gray, enhanced)

            # Assign track IDs and apply Kalman filtering
            targets = self._apply_tracking(targets)

            logger.debug(
                "Thermal detection: method={}, targets={}",
                self._method.value,
                len(targets),
            )

            return targets

        except Exception as e:
            logger.error(f"Thermal detection failed: {e}")
            return []

    def _apply_tracking(self, targets: list[ThermalTarget]) -> list[ThermalTarget]:
        """Apply simple nearest-neighbor tracking and optional Kalman filtering.

        Args:
            targets: Detected targets without track IDs.

        Returns:
            Targets with assigned track IDs and smoothed centroids.
        """
        if not targets:
            return []

        # Simple approach: assign sequential IDs for now
        # In production, use Hungarian algorithm for multi-target association
        for i, target in enumerate(targets):
            track_id = i + 1
            target.track_id = track_id

            if self._use_kalman:
                # Get or create Kalman tracker for this ID
                if track_id not in self._kalman_trackers:
                    self._kalman_trackers[track_id] = KalmanCentroidTracker()

                kalman = self._kalman_trackers[track_id]
                smoothed = kalman.correct(target.centroid)
                target.centroid = smoothed

        return targets

    def get_primary_target(self, targets: list[ThermalTarget]) -> ThermalTarget | None:
        """Get the primary (largest/hottest) target from detection results.

        Args:
            targets: List of detected targets.

        Returns:
            Primary target or None if no targets detected.
        """
        if not targets:
            return None

        # Return largest target (already sorted in contour method)
        return max(targets, key=lambda t: t.area)

    def set_method(self, method: str | ThermalDetectionMethod) -> None:
        """Change detection method at runtime.

        Args:
            method: Detection method name or enum value.
        """
        if isinstance(method, str):
            method = ThermalDetectionMethod(method)
        self._method = method
        logger.info(f"Thermal detection method changed to: {method.value}")

    def get_class_names(self) -> dict[int, str]:
        """Get class names (compatibility with DetectionService interface).

        Returns:
            Dict mapping track IDs to class name (always 'thermal_target').
        """
        return {0: "thermal_target"}

    def filter_by_target_labels(self, boxes: list[ThermalTarget] | Any) -> list[ThermalTarget] | Any:
        """Filter detection boxes (compatibility with DetectionService interface).
        
        For thermal detection, we don't filter by class label since we only 
        detect 'hot' objects. Returns the boxes as-is.

        Args:
            boxes: List of ThermalTarget objects.

        Returns:
            The input boxes unchanged.
        """
        return boxes
