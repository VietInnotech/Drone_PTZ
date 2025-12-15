import time
import sys
import traceback
from onvif import ONVIFCamera

# --- Configuration ---
IP = "192.168.1.123"
PORT = 80
USER = "admin"
PASS = "!Inf2019"


def ptz_test():
    print(f"Connecting to {IP}...")

    try:
        # Connect to camera
        # no_cache=True is safer during testing to avoid old file errors
        mycam = ONVIFCamera(IP, PORT, USER, PASS, no_cache=True)

        # Create media service to get profiles
        media = mycam.create_media_service()

        # Create PTZ service to control camera
        ptz = mycam.create_ptz_service()

        # Get the first media profile
        media_profiles = media.GetProfiles()
        if not media_profiles:
            print("Error: No media profiles found.")
            return

        # 1. Extract the Token ID string (Fixes "ReferenceToken" error)
        video_token = media_profiles[0].token
        print(f"Using Profile Token: {video_token}")

        # Helper: Stop Movement
        def stop_movement():
            print("Stopping...")
            stop_req = ptz.create_type("Stop")
            stop_req.ProfileToken = video_token
            stop_req.PanTilt = True
            stop_req.Zoom = True
            ptz.Stop(stop_req)

        # Helper: Move Continuous
        def move_continuous(pan_speed, tilt_speed, zoom_speed):
            # 2. Use a simple dictionary for the Velocity (Fixes "No element PTZSpeed" error)
            # The library will automatically map this dict to the PTZSpeed XML type.
            velocity_payload = {
                "PanTilt": {"x": pan_speed, "y": tilt_speed},
                "Zoom": {"x": zoom_speed},
            }

            ptz.ContinuousMove(
                {"ProfileToken": video_token, "Velocity": velocity_payload}
            )

        # --- TEST SEQUENCE ---

        # Test 1: Move Right
        print("Test 1: Panning RIGHT (Speed 0.5)")
        move_continuous(0.5, 0.0, 0.0)
        time.sleep(2)
        stop_movement()
        time.sleep(1)

        # Test 2: Move Left
        print("Test 2: Panning LEFT (Speed -0.5)")
        move_continuous(-0.5, 0.0, 0.0)
        time.sleep(2)
        stop_movement()
        time.sleep(1)

        # Test 3: Zoom In
        print("Test 3: Zooming IN (Speed 0.3)")
        move_continuous(0.0, 0.0, 0.3)
        time.sleep(1.5)
        stop_movement()

        print("\nTest Complete: Success!")

    except Exception as e:
        print("\nCRITICAL ERROR:")
        traceback.print_exc()


if __name__ == "__main__":
    ptz_test()
