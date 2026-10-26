import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BODY = json.dumps(
    {"error": {"message": "chaos: rate limit exceeded", "type": "rate_limit_error", "code": 429}}
).encode()


class TooManyRequests(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers.get("content-length", 0)))
        self.send_response(429)
        self.send_header("content-type", "application/json")
        self.send_header("retry-after", "1")
        self.send_header("content-length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, *args):
        pass


ThreadingHTTPServer(("0.0.0.0", 8000), TooManyRequests).serve_forever()
