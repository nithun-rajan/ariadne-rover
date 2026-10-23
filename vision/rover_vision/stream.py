"""Live MJPEG stream of the camera view, for debugging from a laptop browser."""

import errno
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

from . import config

_PAGE = (b'<html><head><title>Rover camera</title></head>'
         b'<body style="margin:0;background:#000">'
         b'<img src="/stream" style="width:100%;height:100vh;object-fit:contain">'
         b'</body></html>')


class FrameBuffer:
    """Thread-safe holder for the most recent frame."""

    def __init__(self):
        self._lock = threading.Lock()
        self._frame = None

    def set(self, frame):
        with self._lock:
            self._frame = frame

    def get(self):
        with self._lock:
            return self._frame


def _make_handler(frames, fps, jpeg_quality):
    class MJPEGHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(_PAGE)
            elif self.path == '/stream':
                self.send_response(200)
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
                self.end_headers()
                self._stream()
            else:
                self.send_error(404)

        def _stream(self):
            try:
                while True:
                    frame = frames.get()
                    if frame is None:
                        time.sleep(0.05)
                        continue
                    ok, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                    if ok:
                        self.wfile.write(b'--FRAME\r\nContent-Type: image/jpeg\r\n\r\n')
                        self.wfile.write(jpg.tobytes())
                        self.wfile.write(b'\r\n')
                    time.sleep(1.0 / fps)
            except (BrokenPipeError, ConnectionResetError):
                pass   # viewer closed the tab

        def log_message(self, *_args):
            pass

    return MJPEGHandler


class StreamServer:
    """Background MJPEG server.

    Uses a threading server so several viewers can watch at once; a plain
    HTTPServer would block every other request behind the first stream.
    If the preferred port is taken (e.g. a previous run is still exiting),
    the next free port is used.
    """

    def __init__(self, frames, port=config.STREAM_PORT, host='0.0.0.0', max_tries=10,
                 fps=config.FRAMERATE, jpeg_quality=config.STREAM_JPEG_QUALITY):
        handler = _make_handler(frames, fps, jpeg_quality)
        last_error = None
        for candidate in range(port, port + max_tries):
            try:
                self._server = ThreadingHTTPServer((host, candidate), handler)
                break
            except OSError as exc:
                if exc.errno != errno.EADDRINUSE:
                    raise
                last_error = exc
        else:
            raise RuntimeError(f'no free stream port in {port}-{port + max_tries - 1}') from last_error

        self._server.daemon_threads = True
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self):
        return f'http://{socket.gethostname().split(".")[0]}.local:{self.port}'

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()
        self._server.server_close()
