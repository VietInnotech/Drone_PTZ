import cv2
import time
import threading
import queue
import requests
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


# --- Hybrid Status Worker (Uses Native API) ---
class HybridStatusWorker:
    def __init__(self, ip, user, password):
        self.url_pt = f"http://{ip}/devices/pantilt/position"
        self.url_zoom = f"http://{ip}/devices/visible/position"
        self.auth = (user, password)
        self.running = True
        self.latest_status = "Initializing..."
        self.thread = threading.Thread(target=self._worker)
        self.thread.daemon = True
        self.thread.start()

    def _worker(self):
        while self.running:
            try:
                # 1. Get Pan/Tilt (Native API)
                r_pt = requests.get(self.url_pt, auth=self.auth, timeout=1)
                pt_data = r_pt.json()

                # 2. Get Zoom (Native API)
                r_z = requests.get(self.url_zoom, auth=self.auth, timeout=1)
                z_data = r_z.json()

                # Format: P: 120.50 | T: -10.20 | Z: 50%
                p_val = f"{pt_data.get('pan', 0):.2f}"
                t_val = f"{pt_data.get('tilt', 0):.2f}"
                z_val = f"{z_data.get('zoom', 0):.1f}%"

                self.latest_status = f"P: {p_val} | T: {t_val} | Z: {z_val}"

            except Exception as e:
                # Fallback message if API fails
                self.latest_status = "Stats: API Error"

            # Fast update rate (10Hz)
            time.sleep(0.1)

    def get(self):
        return self.latest_status

    def stop(self):
        self.running = False


def ptz_test():
    print(f"Connecting to Camera {IP}...")

    try:
        # 1. Setup ONVIF (For Control)
        mycam = ONVIFCamera(IP, PORT, USER, PASS, no_cache=True)
        media = mycam.create_media_service()
        ptz = mycam.create_ptz_service()
        token = media.GetProfiles()[0].token

        # 2. Setup Threads
        print("Starting Video & Hybrid Status Threads...")
        video = VideoStream(RTSP_URL)
        # Use the Hybrid worker instead of the ONVIF one
        stats = HybridStatusWorker(IP, USER, PASS)

        # Helper: Move (ONVIF)
        def move(pan, tilt, zoom):
            ptz.ContinuousMove(
                {
                    "ProfileToken": token,
                    "Velocity": {"PanTilt": {"x": pan, "y": tilt}, "Zoom": {"x": zoom}},
                }
            )

        # Helper: Stop (ONVIF)
        def stop():
            ptz.Stop({"ProfileToken": token, "PanTilt": True, "Zoom": True})

        # Helper: Home (ONVIF)
        def go_home():
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
        print("Testing concurrent pan/tilt and zoom operations...")

        while True:
            frame = video.read()
            if frame is None:
                time.sleep(0.01)
                continue

            elapsed = time.time() - start_time

            # --- Logic Sequence (Including Concurrent Tests) ---
            if stage == 0 and elapsed > 2:
                action_text = "Moving Right >>"
                move(0.5, 0.0, 0.0)
                stage = 1
            elif stage == 1 and elapsed > 5:
                action_text = "Stopping"
                stop()
                stage = 2
            elif stage == 2 and elapsed > 6:
                action_text = "Zooming In [+] (SOLO)"
                move(0.0, 0.0, 0.5)
                stage = 3
            elif stage == 3 and elapsed > 9:
                action_text = "Zooming Out [-] (SOLO)"
                move(0.0, 0.0, -0.5)
                stage = 4
            elif stage == 4 and elapsed > 12:
                action_text = "Stopping"
                stop()
                stage = 5
            elif stage == 5 and elapsed > 13:
                action_text = "Moving Left + Zoom In (CONCURRENT)"
                move(-0.5, 0.0, 0.5)
                stage = 6
            elif stage == 6 and elapsed > 17:
                action_text = "Stopping"
                stop()
                stage = 7
            elif stage == 7 and elapsed > 18:
                action_text = "Tilt Up + Zoom Out (CONCURRENT)"
                move(0.0, 0.5, -0.5)
                stage = 8
            elif stage == 8 and elapsed > 22:
                action_text = "Stopping"
                stop()
                stage = 9
            elif stage == 9 and elapsed > 23:
                action_text = "Pan Right + Tilt Down + Zoom (CONCURRENT 3-WAY)"
                move(0.5, -0.5, 0.5)
                stage = 10
            elif stage == 10 and elapsed > 27:
                action_text = "Stopping"
                stop()
                stage = 11
            elif stage == 11 and elapsed > 28:
                action_text = "RETURNING HOME [H]"
                go_home()
                stage = 12
            elif stage == 12 and elapsed > 34:
                print("Sequence Complete.")
                break

            # --- Draw Overlay ---
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (500, 110), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

            # Display Stats (Fetched from Native API)
            cv2.putText(
                frame,
                f"STATS: {stats.get()}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                f"ACTION: {action_text}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Time: {elapsed:.1f}s",
                (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
            )

            view_frame = cv2.resize(frame, (1280, 720))
            cv2.imshow("Infiniti ARC Control (Hybrid Mode)", view_frame)

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
