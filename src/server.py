import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from .config import STATIC_DIR
from .rag import RAGEngine


ENGINE = None


def get_engine() -> RAGEngine:
    global ENGINE
    if ENGINE is None:
        ENGINE = RAGEngine()
    return ENGINE


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            self.send_json({"status": "ok"})
            return
        if path == "/":
            path = "/index.html"
        target = (STATIC_DIR / unquote(path.lstrip("/"))).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/api/ask":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
            question = payload.get("question", "").strip()
            k = min(max(int(payload.get("k", 4)), 1), 6)
        except (ValueError, json.JSONDecodeError):
            self.send_json({"error": "Invalid JSON payload"}, status=400)
            return
        if not question:
            self.send_json({"error": "Question is required"}, status=400)
            return
        self.send_json(get_engine().answer(question, k=k))

    def send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), AppHandler)
    print("App running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()

