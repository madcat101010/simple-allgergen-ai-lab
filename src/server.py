"""
Standalone Standard Library Web Server for McDonald's Allergen AI Agent
------------------------------------------------------------------------
Zero-dependency HTTP server built using Python's native http.server module.
Serves static UI files and provides REST API endpoints:
- POST /api/chat
- GET  /api/menu
- GET  /api/traces
- GET  /api/health
"""

import http.server
import json
import os
import socketserver
import sys
import time
import urllib.parse
from typing import List, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.agent import AllergenAgent
from src.tools import load_allergen_dataset
from src.telemetry import telemetry

PORT = 8000
agent = AllergenAgent()


class AllergenHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve relative to PROJECT_ROOT so /static/style.css and /static/app.js map directly
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def _send_json(self, data: Any, status_code: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        
        if url.path == "/api/health":
            self._send_json({"status": "ok", "app": "mcdonalds-allergen-ai-agent", "version": "1.0.0"})
            return
            
        elif url.path == "/api/menu":
            try:
                data = load_allergen_dataset()
                self._send_json({"count": len(data), "items": data})
            except Exception as e:
                self._send_json({"error": str(e)}, status_code=500)
            return

        elif url.path == "/api/traces":
            self._send_json({"count": len(telemetry.recent_traces), "traces": telemetry.get_recent_traces()})
            return

        elif url.path == "/" or url.path == "/index.html":
            self.path = "/static/index.html"
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/api/chat":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8")
            
            try:
                payload = json.loads(post_body)
                prompt = payload.get("prompt", "").strip()
                allergies = payload.get("allergies", [])

                if not prompt:
                    self._send_json({"error": "Prompt cannot be empty"}, status_code=400)
                    return

                start_time = time.time()
                result = agent.process_query(prompt, allergies)
                duration_ms = round((time.time() - start_time) * 1000, 2)

                tool_calls = [
                    {
                        "tool": "evaluate_allergen_safety",
                        "input": {"item": result.get("evaluated_item"), "allergies": allergies},
                        "matched_allergens": result.get("details", {}).get("matched_allergens", [])
                    }
                ]

                trace = telemetry.record_trace(
                    prompt=prompt,
                    user_allergies=allergies,
                    status=result["status"],
                    evaluated_item=result.get("evaluated_item"),
                    execution_time_ms=duration_ms,
                    tool_calls=tool_calls,
                    details=result.get("details")
                )

                response_data = {
                    "prompt": result["prompt"],
                    "user_allergies": result["user_allergies"],
                    "status": result["status"],
                    "safety_badge": result["safety_badge"],
                    "response": result["response"],
                    "details": result.get("details"),
                    "disclaimer": result.get("disclaimer", "Warning: Shared kitchen prep areas."),
                    "execution_time_ms": duration_ms,
                    "trace": trace
                }

                self._send_json(response_data)

            except Exception as e:
                self._send_json({"error": f"Agent error: {str(e)}"}, status_code=500)
            return

        self._send_json({"error": "Not Found"}, status_code=404)


def run_server(port: int = PORT):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", port), AllergenHTTPRequestHandler) as httpd:
        print(f"[+] McDonald's Allergen AI Agent Web Server running at http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
