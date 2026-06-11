#!/usr/bin/env python3
"""
GitHub Webhook 服务器
保存到服务器: /www/ai-second-brain/webhook_server.py
运行: python3 webhook_server.py &
"""

import os
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "your-secret-here")
DEPLOY_SCRIPT = "/www/ai-second-brain/deploy.sh"

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 验证 secret（如果配置了）
        if WEBHOOK_SECRET != "your-secret-here":
            signature = self.headers.get("X-Hub-Signature-256", "")
            # 这里应该验证签名，暂时跳过简化处理

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            if data.get("ref") in ["refs/heads/main", "refs/heads/master"]:
                print(f"[Webhook] Received push, deploying...")
                result = subprocess.run(["bash", DEPLOY_SCRIPT], capture_output=True, text=True)
                print(f"[Webhook] Deploy result: {result.returncode}")
                if result.returncode == 0:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok"}).encode())
                else:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": result.stderr}).encode())
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ignored"}).encode())
        except Exception as e:
            print(f"[Webhook] Error: {e}")
            self.send_response(500)
            self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", 9000))
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"[Webhook] Listening on port {port}")
    server.serve_forever()