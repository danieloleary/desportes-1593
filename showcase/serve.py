"""Loopback-only preview. No upstream application scripts are executed."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse

ROOT = Path(__file__).resolve().parents[1]

class Handler(SimpleHTTPRequestHandler):
    def allowed(self):
        path = unquote(urlsplit(self.path).path)
        target = (ROOT / path.lstrip('/')).resolve()
        return not any(p.startswith('.') for p in path.split('/') if p) and target.is_relative_to(ROOT)

    def do_GET(self):
        if not self.allowed():
            self.send_error(403)
            return
        if urlsplit(self.path).path == '/':
            self.send_response(302)
            self.send_header('Location', '/showcase/')
            self.end_headers()
            return
        super().do_GET()

    def do_HEAD(self):
        if not self.allowed():
            self.send_error(403)
            return
        super().do_HEAD()

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

class Server(ThreadingHTTPServer):
    request_queue_size = 128

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4193)
    args = parser.parse_args()
    server = Server(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT)))
    print(f'Local showcase: http://127.0.0.1:{args.port}/showcase/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
