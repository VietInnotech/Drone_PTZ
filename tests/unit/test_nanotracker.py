"""Unit tests for src/tracking/nanotracker.py"""

from unittest.mock import MagicMock, Mock, patch

import cv2
import numpy as np
import pytest

from src.tracking.nanotracker import (
    NanoParams,
    NanoSOT,
    _map_backend_str_to_cv2,
    _map_target_str_to_cv2,
    create_nano_sot_from_settings,
)


class TestNanoParams:
    """Test NanoParams dataclass."""

    def test_nano_params_creation(self) -> None:
        """Test creating NanoParams with required fields."""
        params = NanoParams(
            backbone="path/to/backbone.onnx",
            head="path/to/head.onnx",
        )
        assert params.backbone == "path/to/backbone.onnx"
        assert params.head == "path/to/head.onnx"
        assert params.backend is None
        assert params.target is None

    def test_nano_params_with_backend_target(self) -> None:
        """Test creating NanoParams with backend and target."""
        params = NanoParams(
            backbone="backbone.onnx",
            head="head.onnx",
            backend=cv2.dnn.DNN_BACKEND_OPENCV,
            target=cv2.dnn.DNN_TARGET_CPU,
        )
        assert params.backend == cv2.dnn.DNN_BACKEND_OPENCV
        assert params.target == cv2.dnn.DNN_TARGET_CPU


class TestNanoSOT:
    """Test NanoSOT class."""

    @pytest.fixture
    def params(self) -> NanoParams:
        """Create test parameters."""
        return NanoParams(
            backbone="assets/models/nanotrack/nanotrack_backbone_sim.onnx",
            head="assets/models/nanotrack/nanotrack_head_sim.onnx",
        )

    @pytest.fixture
    def frame(self) -> np.ndarray:
        """Create test frame."""
        return np.zeros((720, 1280, 3), dtype=np.uint8)

    def test_nanosot_initialization(self, params: NanoParams) -> None:
        """Test NanoSOT initialization."""
        sot = NanoSOT(params)
        assert sot._params == params
        assert sot._tracker is None
        assert not sot._active
        assert not sot.active

    @patch("cv2.TrackerNano_create")
    @patch("cv2.TrackerNano_Params")
    def test_init_success(
        self,
        mock_params_class: Mock,
        mock_create: Mock,
        params: NanoParams,
        frame: np.ndarray,
    ) -> None:
        """Test successful tracker initialization."""
        # Mock the TrackerNano_Params instance
        mock_params_instance = Mock()
        mock_params_class.return_value = mock_params_instance

        # Mock the tracker
        # NOTE: TrackerNano.init() returns None (void in C++), not a boolean
        mock_tracker = Mock()
        mock_tracker.init.return_value = None
        mock_create.return_value = mock_tracker

        sot = NanoSOT(params)
        bbox = (100, 100, 200, 200)
        result = sot.init(frame, bbox)

        assert result is True
        assert sot.active is True
        mock_params_instance.__setattr__("backbone", params.backbone)
        mock_params_instance.__setattr__("neckhead", params.head)
        mock_create.assert_called_once_with(mock_params_instance)
        mock_tracker.init.assert_called_once_with(frame, (100, 100, 100, 100))

    @patch("cv2.TrackerNano_create")
    @patch("cv2.TrackerNano_Params")
    def test_init_failure(
        self,
        mock_params_class: Mock,
        mock_create: Mock,
        params: NanoParams,
        frame: np.ndarray,
    ) -> None:
        """Test tracker initialization failure via exception."""
        mock_params_instance = Mock()
        mock_params_class.return_value = mock_params_instance

        mock_tracker = Mock()
        # Simulate initialization failure by raising an exception
        mock_tracker.init.side_effect = RuntimeError("Model loading failed")
        mock_create.return_value = mock_tracker

        sot = NanoSOT(params)
        bbox = (100, 100, 200, 200)
        result = sot.init(frame, bbox)

        assert result is False
        assert sot.active is False

    @patch("cv2.TrackerNano_create")
    @patch("cv2.TrackerNano_Params")
    def test_init_exception(
        self,
        mock_params_class: Mock,
        mock_create: Mock,
        params: NanoParams,
        frame: np.ndarray,
    ) -> None:
        """Test tracker initialization with exception."""
        mock_create.side_effect = RuntimeError("Failed to create tracker")

        sot = NanoSOT(params)
        bbox = (100, 100, 200, 200)
        result = sot.init(frame, bbox)

        assert result is False
        assert sot.active is False

    def test_update_not_initialized(
        self, params: NanoParams, frame: np.ndarray
    ) -> None:
        """Test update when tracker is not initialized."""
        sot = NanoSOT(params)
        ok, bbox = sot.update(frame)

        assert ok is False
        assert bbox == (0, 0, 0, 0)

    @patch("cv2.TrackerNano_create")
    @patch("cv2.TrackerNano_Params")
    def test_update_success(
        self,
        mock_params_class: Mock,
        mock_create: Mock,
        params: NanoParams,
        frame: np.ndarray,
    ) -> None:
        """Test successful tracker update."""
        mock_params_instance = Mock()
        mock_params_class.return_value = mock_params_instance

        mock_tracker = Mock()
        mock_tracker.init.return_value = True
        mock_tracker.update.return_value = (True, (110, 110, 90, 90))
        mock_create.return_value = mock_tracker

        sot = NanoSOT(params)
        sot.init(frame, (100, 100, 200, 200))

        ok, bbox = sot.update(frame)

        assert ok is True
        assert bbox == (110, 110, 200, 200)  # (x, y, x+w, y+h)

    @patch("cv2.TrackerNano_create")
    @patch("cv2.TrackerNano_Params")
    def test_update_failure(
        self,
        mock_params_class: Mock,
        mock_create: Mock,
        params: NanoParams,
        frame: np.ndarray,
    ) -> None:
        """Test tracker update failure."""
        mock_params_instance = Mock()
        mock_params_class.return_value = mock_params_instance

        mock_tracker = Mock()
        mock_tracker.init.return_value = True
        mock_tracker.update.return_value = (False, (0, 0, 0, 0))
        mock_create.return_value = mock_tracker

        sot = NanoSOT(params)
        sot.init(frame, (100, 100, 200, 200))

        ok, bbox = sot.update(frame)

        assert ok is False
        assert bbox == (0, 0, 0, 0)

    @patch("cv2.TrackerNano_create")
    @patch("cv2.TrackerNano_Params")
    def test_update_exception(
        self,
        mock_params_class: Mock,
        mock_create: Mock,
        params: NanoParams,
        frame: np.ndarray,
    ) -> None:
        """Test tracker update with exception."""
        mock_params_instance = Mock()
        mock_params_class.return_value = mock_params_instance

        mock_tracker = Mock()
        mock_tracker.init.return_value = True
        mock_tracker.update.side_effect = RuntimeError("Update failed")
        mock_create.return_value = mock_tracker

        sot = NanoSOT(params)
        sot.init(frame, (100, 100, 200, 200))

        ok, bbox = sot.update(frame)

        assert ok is False
        assert bbox == (0, 0, 0, 0)

    def test_release(self, params: NanoParams) -> None:
        """Test tracker release."""
        sot = NanoSOT(params)
        sot._tracker = MagicMock()
        sot._active = True

        sot.release()

        assert sot._tracker is None
        assert not sot._active
        assert not sot.active


class TestMappingFunctions:
    """Test backend and target mapping functions."""

    def test_map_backend_str_to_cv2(self) -> None:
        """Test backend string to OpenCV constant mapping."""
        assert _map_backend_str_to_cv2("default") is None
        assert _map_backend_str_to_cv2("opencv") == cv2.dnn.DNN_BACKEND_OPENCV
        assert _map_backend_str_to_cv2("cuda") == cv2.dnn.DNN_BACKEND_CUDA
        assert _map_backend_str_to_cv2("vulkan") == cv2.dnn.DNN_BACKEND_VKCOM
        assert _map_backend_str_to_cv2("openvino") == cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE
        assert _map_backend_str_to_cv2("halide") == cv2.dnn.DNN_BACKEND_HALIDE
        assert _map_backend_str_to_cv2("unknown") is None

    def test_map_target_str_to_cv2(self) -> None:
        """Test target string to OpenCV constant mapping."""
        assert _map_target_str_to_cv2("cpu") == cv2.dnn.DNN_TARGET_CPU
        assert _map_target_str_to_cv2("cuda") == cv2.dnn.DNN_TARGET_CUDA
        assert _map_target_str_to_cv2("cuda_fp16") == cv2.dnn.DNN_TARGET_CUDA_FP16
        assert _map_target_str_to_cv2("opencl") == cv2.dnn.DNN_TARGET_OPENCL
        assert _map_target_str_to_cv2("opencl_fp16") == cv2.dnn.DNN_TARGET_OPENCL_FP16
        assert _map_target_str_to_cv2("vulkan") == cv2.dnn.DNN_TARGET_VULKAN
        assert _map_target_str_to_cv2("unknown") is None


class TestCreateNanoSOTFromSettings:
    """Test create_nano_sot_from_settings function."""

    def test_create_from_settings_default(self) -> None:
        """Test creating NanoSOT from settings with defaults."""
        mock_settings = Mock()
        mock_settings.tracking.nanotrack_backbone_path = "backbone.onnx"
        mock_settings.tracking.nanotrack_head_path = "head.onnx"
        mock_settings.tracking.dnn_backend = "default"
        mock_settings.tracking.dnn_target = "cpu"

        sot = create_nano_sot_from_settings(mock_settings)

        assert isinstance(sot, NanoSOT)
        assert sot._params.backbone == "backbone.onnx"
        assert sot._params.head == "head.onnx"
        assert sot._params.backend is None
        assert sot._params.target == cv2.dnn.DNN_TARGET_CPU

    def test_create_from_settings_cuda(self) -> None:
        """Test creating NanoSOT from settings with CUDA."""
        mock_settings = Mock()
        mock_settings.tracking.nanotrack_backbone_path = "backbone.onnx"
        mock_settings.tracking.nanotrack_head_path = "head.onnx"
        mock_settings.tracking.dnn_backend = "cuda"
        mock_settings.tracking.dnn_target = "cuda"

        sot = create_nano_sot_from_settings(mock_settings)

        assert isinstance(sot, NanoSOT)
        assert sot._params.backend == cv2.dnn.DNN_BACKEND_CUDA
        assert sot._params.target == cv2.dnn.DNN_TARGET_CUDA
