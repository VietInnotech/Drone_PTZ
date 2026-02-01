import pytest
import threading
import queue
import time
from src.settings import Settings
from src.detection_manager import DetectionManager, DetectionMode, DetectionResult

def test_detection_manager_initialization():
    settings = Settings()
    settings.visible_detection.enabled = True
    settings.thermal_detection.enabled = False
    
    manager = DetectionManager(settings)
    assert manager.settings == settings
    assert manager._visible_service is None
    assert manager._thermal_service is None

def test_detection_manager_priority_logic():
    settings = Settings()
    settings.thermal_detection.enabled = True
    settings.tracking.priority = "thermal"
    manager = DetectionManager(settings)
    assert manager.get_tracking_priority() == DetectionMode.THERMAL
    
    settings.tracking.priority = "visible"
    assert manager.get_tracking_priority() == DetectionMode.VISIBLE

def test_camera_conflict_validation():
    settings = Settings()
    settings.visible_detection.enabled = True
    settings.thermal_detection.enabled = True
    
    # Same camera index 0
    settings.visible_detection.camera.source = "camera"
    settings.visible_detection.camera.camera_index = 0
    settings.thermal_detection.camera.source = "camera"
    settings.thermal_detection.camera.camera_index = 0
    
    with pytest.raises(ValueError, match="Camera conflict"):
        settings.model_validate(settings.model_dump())

def test_detection_manager_start_stop():
    # Use a dummy settings object with both disabled to avoid starting actual CV2 captures
    settings = Settings()
    settings.visible_detection.enabled = False
    settings.thermal_detection.enabled = False
    
    manager = DetectionManager(settings)
    manager.start()
    manager.stop()
    assert manager._stop_event.is_set()
