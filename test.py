import cv2
import time
import threading
import queue
import traceback
from onvif import ONVIFCamera

# --- Configuration ---
IP = "192.168.1.123"
PORT = 80
USER = "admin"
PASS = "!Inf2019"
RTSP_URL = f"rtsp://{USER}:{PASS}@{IP}:554/profile1/media.smp"


# --- Threaded Video Class ---
class VideoStream:
    def __init__(self, src):
        self.capture = cv2.VideoCapture(src)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.q = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._reader)
        self.thread.daemon = True
        self.thread.start()

    def _reader(self):
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get() if not self.q.empty() else None

    def stop(self):
        self.running = False
        self.capture.release()
        self.thread.join()


# --- Threaded Status Class (New) ---
# Fetching status via ONVIF is slow (HTTP request), so we do it in a thread
# to avoid freezing the video stream.
class StatusWorker:
    def __init__(self, ptz, token):
        self.ptz = ptz
        self.token = token
        self.running = True
        self.latest_status = "Initializing..."
        self.thread = threading.Thread(target=self._worker)
        self.thread.daemon = True
        self.thread.start()

    def _worker(self):
        while self.running:
            try:
                # Request Status
                req = self.ptz.create_type("GetStatus")
                req.ProfileToken = self.token
                status = self.ptz.GetStatus(req)

                # Safe Extraction (Handling the 'None' bug)
                if status.Position is None:
                    self.latest_status = "Pos: Unavailable (Busy?)"
                else:
                    # Check partial data
                    p_val = (
                        f"{status.Position.PanTilt.x:.2f}"
                        if status.Position.PanTilt
                        else "?"
                    )
                    t_val = (
                        f"{status.Position.PanTilt.y:.2f}"
                        if status.Position.PanTilt
                        else "?"
                    )
                    z_val = (
                        f"{status.Position.Zoom.x:.2f}" if status.Position.Zoom else "?"
                    )

                    self.latest_status = f"P: {p_val} | T: {t_val} | Z: {z_val}"

            except Exception as e:
                self.latest_status = "Stats Error"

            # Don't hammer the camera; update 4 times a second
            time.sleep(0.25)

    def get(self):
        return self.latest_status

    def stop(self):
        self.running = False


def ptz_test():
    print(f"Connecting to Camera {IP}...")

    try:
        # 1. Setup ONVIF
        mycam = ONVIFCamera(IP, PORT, USER, PASS, no_cache=True)
        media = mycam.create_media_service()
        ptz = mycam.create_ptz_service()
        token = media.GetProfiles()[0].token

        # 2. Setup Threads
        print("Starting Video & Status Threads...")
        video = VideoStream(RTSP_URL)
        stats = StatusWorker(ptz, token)

        # Helper: Move
        def move(pan, tilt, zoom):
            ptz.ContinuousMove(
                {
                    "ProfileToken": token,
                    "Velocity": {"PanTilt": {"x": pan, "y": tilt}, "Zoom": {"x": zoom}},
                }
            )

        # Helper: Stop
        def stop():
            ptz.Stop({"ProfileToken": token, "PanTilt": True, "Zoom": True})

        # Helper: Home
        def go_home():
            print("   -> Commencing Return to Home...")
            # We use a speed of 1.0 (Max) for the return
            ptz.GotoHomePosition(
                {
                    "ProfileToken": token,
                    "Speed": {"PanTilt": {"x": 1.0, "y": 1.0}, "Zoom": {"x": 1.0}},
                }
            )

        # --- Main Loop ---
        start_time = time.time()
        stage = 0
        action_text = "Starting..."

        print("Test Started. Press 'q' to exit.")

        while True:
            frame = video.read()
            if frame is None:
                time.sleep(0.01)
                continue

            elapsed = time.time() - start_time

            # --- Logic Sequence ---
            if stage == 0 and elapsed > 2:
                action_text = "Moving Right >>"
                move(0.5, 0.0, 0.0)
                stage = 1
            elif stage == 1 and elapsed > 5:
                action_text = "Stopping"
                stop()
                stage = 2
            elif stage == 2 and elapsed > 6:
                action_text = "<< Moving Left"
                move(-0.5, 0.0, 0.0)
                stage = 3
            elif stage == 3 and elapsed > 9:
                action_text = "Stopping"
                stop()
                stage = 4
            elif stage == 4 and elapsed > 10:
                action_text = "Zooming In [+]"
                move(0.0, 0.0, 0.5)
                stage = 5
            elif stage == 5 and elapsed > 13:
                action_text = "Stopping"
                stop()
                stage = 6
            elif stage == 6 and elapsed > 14:
                action_text = "RETURNING HOME [H]"
                go_home()
                stage = 7
            elif stage == 7 and elapsed > 20:  # Give it time to get home
                print("Sequence Complete.")
                break

            # --- Draw Overlay ---
            # 1. Background Box for Text (Black semi-transparent)
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (450, 110), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

            # 2. Text Info
            # Stats (Pan/Tilt/Zoom)
            cv2.putText(
                frame,
                f"STATS: {stats.get()}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

            # Current Action
            cv2.putText(
                frame,
                f"ACTION: {action_text}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # Timer
            cv2.putText(
                frame,
                f"Time: {elapsed:.1f}s",
                (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
            )

            # Show Frame
            # Resize for viewing
            view_frame = cv2.resize(frame, (1280, 720))
            cv2.imshow("Infiniti ARC Control", view_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except Exception as e:
        print("\nCRITICAL ERROR:")
        traceback.print_exc()

    finally:
        print("Cleaning up...")
        if "video" in locals():
            video.stop()
        if "stats" in locals():
            stats.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    ptz_test()
