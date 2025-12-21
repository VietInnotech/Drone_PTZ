#!/usr/bin/env python3
"""
Test script to verify if the camera can process multiple requests simultaneously.
Tests pan, tilt, and zoom operations concurrently.

Octagon API v2.19 endpoints used:
- POST /api/devices/pantilt/position - Set pan/tilt position
- POST /api/devices/visible/position - Set visible lens zoom/focus
"""

import asyncio
import aiohttp
import time
import json
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

# Configuration
CAMERA_HOST = "192.168.1.122"  # Update with your actual camera IP
API_BASE_URL = f"http://{CAMERA_HOST}/api"
USERNAME = "admin"
PASSWORD = "!Inf2019"


@dataclass
class RequestTiming:
    """Track timing information for a request"""

    name: str
    send_time: float
    receive_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = False
    error: Optional[str] = None

    def complete(self, success: bool, error: Optional[str] = None):
        self.receive_time = time.time()
        self.duration = self.receive_time - self.send_time
        self.success = success
        self.error = error


class ConcurrentCameraTest:
    def __init__(self):
        self.timings: list[RequestTiming] = []
        self.auth = aiohttp.BasicAuth(USERNAME, PASSWORD)

    async def test_pantilt_position(
        self, session: aiohttp.ClientSession, pan: float, tilt: float
    ) -> RequestTiming:
        """Send a pan/tilt position request"""
        timing = RequestTiming(name="PanTilt", send_time=time.time())
        self.timings.append(timing)

        url = f"{API_BASE_URL}/devices/pantilt/position"
        data = {"pan": pan, "tilt": tilt}

        try:
            async with session.post(url, json=data, auth=self.auth) as resp:
                content = await resp.text()
                result = json.loads(content)
                timing.complete(resp.status == 200 and result.get("success", False))
                return timing
        except Exception as e:
            timing.complete(False, str(e))
            return timing

    async def stop_visible_zoom(self, session: aiohttp.ClientSession) -> RequestTiming:
        """Stop visible lens zoom/focus motors"""
        timing = RequestTiming(name="StopZoom", send_time=time.time())
        self.timings.append(timing)

        url = f"{API_BASE_URL}/devices/visible?command=stop"

        try:
            async with session.get(url, auth=self.auth) as resp:
                content = await resp.text()
                # Handle empty response (some commands don't return JSON)
                if content.strip():
                    result = json.loads(content)
                    timing.complete(resp.status == 200 and result.get("success", False))
                else:
                    timing.complete(resp.status == 200)
                return timing
        except Exception as e:
            timing.complete(False, str(e))
            return timing

    async def test_visible_zoom(
        self, session: aiohttp.ClientSession, direction: str = "tele"
    ) -> RequestTiming:
        """Send a visible lens zoom request using zoomTele or zoomWide command"""
        timing = RequestTiming(name=f"VisibleZoom-{direction}", send_time=time.time())
        self.timings.append(timing)

        zoom_cmd = "zoomTele" if direction.lower() == "tele" else "zoomWide"
        url = f"{API_BASE_URL}/devices/visible?command={zoom_cmd}"

        try:
            async with session.get(url, auth=self.auth) as resp:
                content = await resp.text()
                # Handle empty response (some commands don't return JSON)
                if content.strip():
                    result = json.loads(content)
                    timing.complete(resp.status == 200 and result.get("success", False))
                else:
                    timing.complete(resp.status == 200)
                return timing
        except Exception as e:
            timing.complete(False, str(e))
            return timing

    async def stop_pantilt_move(self, session: aiohttp.ClientSession) -> RequestTiming:
        """Stop pan-tilt movement"""
        timing = RequestTiming(name="StopPanTilt", send_time=time.time())
        self.timings.append(timing)

        url = f"{API_BASE_URL}/devices/pantilt?command=stop"

        try:
            async with session.get(url, auth=self.auth) as resp:
                content = await resp.text()
                # Handle empty response (some commands don't return JSON)
                if content.strip():
                    result = json.loads(content)
                    timing.complete(resp.status == 200 and result.get("success", False))
                else:
                    timing.complete(resp.status == 200)
                return timing
        except Exception as e:
            timing.complete(False, str(e))
            return timing

    async def test_pantilt_move(
        self, session: aiohttp.ClientSession, direction: str, speed: float
    ) -> RequestTiming:
        """Send a pan/tilt move request"""
        timing = RequestTiming(name=f"PanTilt-{direction}", send_time=time.time())
        self.timings.append(timing)

        url = f"{API_BASE_URL}/devices/pantilt?command=move&direction={direction}&speed={speed}"

        try:
            async with session.get(url, auth=self.auth) as resp:
                content = await resp.text()
                # Handle empty response (some commands don't return JSON)
                if content.strip():
                    result = json.loads(content)
                    timing.complete(resp.status == 200 and result.get("success", False))
                else:
                    timing.complete(resp.status == 200)
                return timing
        except Exception as e:
            timing.complete(False, str(e))
            return timing

    async def get_device_status(self, session: aiohttp.ClientSession) -> bool:
        """Check if critical devices are connected"""
        try:
            async with session.get(f"{API_BASE_URL}/devices", auth=self.auth) as resp:
                # Handle non-standard JSON content-type by parsing manually
                content = await resp.text()
                result = json.loads(content)
                if not result.get("success", False):
                    return False

                data = result.get("data", {})
                pantilt_status = data.get("pantilt", {}).get("status", "UNKNOWN")
                visible_status = data.get("visible", {}).get("status", "UNKNOWN")

                print(f"[Device Status]")
                print(f"  Pan-Tilt: {pantilt_status}")
                print(f"  Visible: {visible_status}")

                # Pan-Tilt is required, Visible is optional
                pantilt_ok = pantilt_status == "CONNECTED"
                visible_available = (
                    visible_status == "CONNECTED" or visible_status == "UNKNOWN"
                )

                return pantilt_ok
        except Exception as e:
            print(f"[Device Status] Error: {e}")
            return False

    async def run_concurrent_test(self, num_iterations: int = 3):
        """Run concurrent tests with pan, tilt, and zoom"""
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            print(f"\n{'=' * 80}")
            print(f"CONCURRENT CAMERA API TEST")
            print(f"{'=' * 80}")
            print(f"Target: {CAMERA_HOST}")
            print(f"Test Duration: {num_iterations} iteration(s)")
            print(f"{'=' * 80}\n")

            # Check device status
            if not await self.get_device_status(session):
                print("\n[ERROR] Not all devices are connected. Aborting test.")
                return

            print("\n[TEST] Starting concurrent requests...")
            print("-" * 80)

            # Run multiple iterations
            for iteration in range(num_iterations):
                print(f"\n[Iteration {iteration + 1}/{num_iterations}]")
                self.timings.clear()

                # Create concurrent tasks
                tasks = [
                    self.test_pantilt_position(session, pan=2.0, tilt=2.0),
                    self.test_visible_zoom(session, direction="tele"),
                    self.test_pantilt_move(session, direction="up", speed=10.0),
                ]

                # Execute all requests concurrently
                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time

                # Stop all motors after movement to prevent continuous motion
                await self.stop_visible_zoom(session)
                await self.stop_pantilt_move(session)

                # Report results
                print(f"  Total time: {total_time:.3f}s")
                for timing in sorted(self.timings, key=lambda x: x.send_time):
                    status = "✓ SUCCESS" if timing.success else "✗ FAILED"
                    error_msg = f" - {timing.error}" if timing.error else ""
                    print(
                        f"  {timing.name:20} {status:12} ({timing.duration:.3f}s){error_msg}"
                    )

                # Check if requests were truly concurrent
                send_times = [t.send_time for t in self.timings]
                receive_times = [t.receive_time for t in self.timings if t.receive_time]

                if send_times:
                    time_spread = max(send_times) - min(send_times)
                    print(
                        f"  Request spread: {time_spread:.6f}s (lower is more concurrent)"
                    )

                # Wait between iterations
                if iteration < num_iterations - 1:
                    await asyncio.sleep(1)

            # Final summary
            print("\n" + "=" * 80)
            print("[SUMMARY]")
            print("=" * 80)

            total_requests = len(self.timings)
            successful = sum(1 for t in self.timings if t.success)
            failed = total_requests - successful

            print(f"Total Requests: {total_requests}")
            print(f"Successful: {successful}")
            print(f"Failed: {failed}")

            if self.timings:
                avg_duration = sum(t.duration for t in self.timings) / len(self.timings)
                print(f"Average Request Time: {avg_duration:.3f}s")

            print("\n[ANALYSIS]")
            if failed > 0:
                print(
                    f"⚠️  {failed} request(s) failed. Check camera connection and API."
                )
            else:
                print("✓ All requests completed successfully!")
                print("✓ Camera can handle concurrent requests.")

            print("\n" + "=" * 80 + "\n")


async def main():
    """Main entry point"""
    test = ConcurrentCameraTest()

    try:
        # Run with 3 iterations
        await test.run_concurrent_test(num_iterations=3)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test cancelled by user.")
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("\n🎥 Camera Concurrent Request Test\n")
    print(f"⚠️  Before running, update CAMERA_HOST in the script if needed.")
    print(f"Current target: {CAMERA_HOST}\n")

    input("Press Enter to start the test...")

    asyncio.run(main())
