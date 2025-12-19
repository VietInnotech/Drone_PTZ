import queue

from src import webrtc_client


def test_start_webrtc_client_callable() -> None:
    q = queue.Queue()
    # We cannot actually connect in unit tests, but the function should be callable
    t = webrtc_client.start_webrtc_client(q, __import__("threading").Event(), url="http://localhost:8889/camera_1/")
    assert t is not None
    # thread should be alive (daemon) for a brief period
    assert t.is_alive()
    # don't hang tests: no join here
