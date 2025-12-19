import queue

from src import webrtc_receiver


def test_make_app_routes_exist() -> None:
    q = queue.Queue()
    app = webrtc_receiver._make_app(q, path="/camera_1/", width=640, height=360, fps=15)
    # verify that the two handlers exist
    routes = {route.resource.canonical for route in app.router.routes()}
    assert "/camera_1/" in routes
    assert "/camera_1/offer" in routes