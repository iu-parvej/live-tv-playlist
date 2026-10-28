"""
web/server.py
Lightweight local HTTP server for the Live TV Dashboard & HLS Player.
Provides APIs for channel listings, stats, stream playback, and triggering refresh.
"""

import os
import sys
import json
import threading
import logging
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
from main import run_pipeline

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WebServer")

is_refreshing = False
refresh_log = []

class LiveTVHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__)), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            status_path = os.path.join("output", "status.json")
            if os.path.exists(status_path):
                with open(status_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"status": "No check performed yet"}
            data["is_refreshing"] = is_refreshing
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif path == "/api/channels":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            # Read playlist.m3u or parse output
            m3u_path = os.path.join("output", "playlist.m3u")
            channels = []
            if os.path.exists(m3u_path):
                with open(m3u_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                curr_ch = {}
                for l in lines:
                    l = l.strip()
                    if l.startswith("#EXTINF:"):
                        curr_ch = {}
                        # extract group-title
                        import re
                        m_grp = re.search(r'group-title="([^"]+)"', l)
                        m_logo = re.search(r'tvg-logo="([^"]+)"', l)
                        name = l.split(",")[-1].strip()
                        curr_ch["name"] = name
                        curr_ch["category"] = m_grp.group(1) if m_grp else "General"
                        curr_ch["logo"] = m_logo.group(1) if m_logo else ""
                    elif l.startswith("http://") or l.startswith("https://"):
                        if curr_ch:
                            curr_ch["url"] = l
                            channels.append(curr_ch)
                            curr_ch = {}
            self.wfile.write(json.dumps(channels).encode("utf-8"))

        elif path == "/api/refresh":
            global is_refreshing
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            if not is_refreshing:
                is_refreshing = True
                def run_bg():
                    global is_refreshing
                    try:
                        run_pipeline(auto_push=True)
                    except Exception as e:
                        logger.error(f"Error in background refresh: {e}")
                    finally:
                        is_refreshing = False

                t = threading.Thread(target=run_bg, daemon=True)
                t.start()
                self.wfile.write(json.dumps({"status": "started", "message": "Refresh started in background"}).encode("utf-8"))
            else:
                self.wfile.write(json.dumps({"status": "already_running", "message": "Refresh is already running"}).encode("utf-8"))

        else:
            super().do_GET()

def start_web_server(port: int = 8080):
    server = HTTPServer(("0.0.0.0", port), LiveTVHandler)
    print("=" * 65)
    print(f" 📺 LIVE TV DASHBOARD & HLS PLAYER RUNNING")
    print(f" 🌐 Open in your browser: http://localhost:{port}")
    print("=" * 65)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server.")
        server.server_close()

if __name__ == "__main__":
    start_web_server()
