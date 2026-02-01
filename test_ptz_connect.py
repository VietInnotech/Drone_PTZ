
import sys
from pathlib import Path
from loguru import logger
from src.settings import load_settings
from src.ptz_controller import PTZService

def test_connection():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    settings = load_settings()
    print("Loading settings from config.yaml...")
    vis_cam = settings.visible_detection.camera
    print(f"IP: {vis_cam.credentials_ip}")
    print(f"User: {vis_cam.credentials_user}")
    print(f"Password: {'*' * len(vis_cam.credentials_password) if vis_cam.credentials_password else 'None'}")
    
    print("\nInitializing PTZService...")
    ptz = PTZService(settings=settings)
    
    if ptz.connected:
        print("\nSUCCESS: PTZService connected!")
        print(f"Profile: {ptz.profile.Name}")
        print(f"Pan/Tilt Range: ({ptz.xmin}, {ptz.xmax}), ({ptz.ymin}, {ptz.ymax})")
    else:
        print("\nFAILURE: PTZService failed to connect.")
        # The logs should show why

if __name__ == "__main__":
    test_connection()
