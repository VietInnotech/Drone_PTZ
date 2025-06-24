import time
from ptz_controller import PTZService
from config import logger, Config

def test_continuous_move():
    """
    Tests the continuous_move functionality with simultaneous pan, tilt, and zoom.
    """
    logger.info("--- Starting Continuous Move Test ---")
    
    ptz_service = None
    try:
        # 1. Setup camera connection
        logger.info("Initializing PTZService...")
        # Use credentials from config.py
        ptz_service = PTZService(
            ip=Config.CAMERA_CREDENTIALS["ip"],
            user=Config.CAMERA_CREDENTIALS["user"],
            password=Config.CAMERA_CREDENTIALS["pass"]
        )

        if not ptz_service.connected:
            logger.error("Failed to connect to the camera. Aborting test.")
            return

        logger.info("Camera connected successfully.")

        # 2. Start continuous move
        pan_speed = 0.2
        tilt_speed = 0.2
        zoom_speed = 0.5
        duration = 5  # seconds

        logger.info(f"Executing continuous_move(pan={pan_speed}, tilt={tilt_speed}, zoom={zoom_speed}) for {duration} seconds...")
        ptz_service.continuous_move(pan=pan_speed, tilt=tilt_speed, zoom=zoom_speed)

        # 3. Wait for the specified duration
        time.sleep(duration)

        logger.info("5-second operation duration complete.")

    except Exception as e:
        logger.error(f"An error occurred during the test: {e}")

    finally:
        # 4. Proper teardown
        if ptz_service and ptz_service.connected:
            logger.info("Stopping all PTZ movement.")
            ptz_service.stop()
            logger.info("PTZ movement stopped.")
    
    logger.info("--- Continuous Move Test Finished ---")

if __name__ == "__main__":
    test_continuous_move()