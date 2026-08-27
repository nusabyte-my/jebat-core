#!/usr/bin/env python3
"""JEBAT auto-deploy webhook listener.

Listens for GitHub push webhooks and triggers the deploy script.

Usage:
  ./deploy-webhook.py                    # port 8081, no secret check
  ./deploy-webhook.py --port 8082        # custom port
  ./deploy-webhook.py --secret mysecret  # validate X-Hub-Signature-256

Systemd service (create /etc/systemd/system/jebat-deploy-webhook.service):
  [Unit]
  Description=JEBAT Auto-Deploy Webhook
  After=network.target

  [Service]
  ExecStart=/path/to/infra/deploy/deploy-webhook.py --secret mys3cr3t
  WorkingDirectory=/var/www/jebat-core
  Restart=always
  User=root

  [Install]
  WantedBy=multi-user.target
"""

import argparse
import hashlib
import hmac
import json
import logging
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

DEPLOY_SCRIPT = os.path.join(os.path.dirname(__file__), "auto-deploy.sh")
if not os.path.exists(DEPLOY_SCRIPT):
    DEPLOY_SCRIPT = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts", "auto-deploy.sh",
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("deploy-webhook")


class DeployHandler(BaseHTTPRequestHandler):
    secret = None

    def log_message(self, fmt, *args):
        log.info("%s - %s", self.client_address[0], fmt % args)

    def _verify_signature(self, body):
        if not self.secret:
            return True
        sig_header = self.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            self.secret.encode(), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(sig_header, expected)

    def _respond(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": msg}).encode())

    def do_POST(self):
        if self.path != "/deploy-webhook":
            self._respond(404, "not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        event = self.headers.get("X-GitHub-Event", "")
        delivery = self.headers.get("X-GitHub-Delivery", "")

        if not self._verify_signature(body):
            log.warning("invalid signature (delivery=%s)", delivery)
            self._respond(403, "invalid signature")
            return

        if event != "push":
            log.info("ignoring event=%s (delivery=%s)", event, delivery)
            self._respond(200, f"ignored event={event}")
            return

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, "invalid json")
            return

        branch = payload.get("ref", "")
        commit = (payload.get("head_commit") or {}).get("id", "")[:8]
        repo = (payload.get("repository") or {}).get("full_name", "?")

        log.info(
            "push event: repo=%s branch=%s commit=%s delivery=%s",
            repo, branch, commit, delivery,
        )

        if not branch.endswith("/main"):
            log.info("not main branch, skipping deploy")
            self._respond(200, f"not main branch ({branch})")
            return

        self._respond(202, "deploy triggered")

        log.info("running auto-deploy.sh ...")
        env = os.environ.copy()
        env["JEBAT_DEPLOY_COMMIT"] = commit
        env["JEBAT_DEPLOY_DELIVERY"] = delivery
        result = subprocess.run(
            ["bash", DEPLOY_SCRIPT],
            cwd=os.path.dirname(DEPLOY_SCRIPT) or "/",
            capture_output=True, text=True, env=env,
        )

        for line in result.stdout.splitlines():
            log.info("[deploy] %s", line)
        for line in result.stderr.splitlines():
            log.warning("[deploy] %s", line)

        if result.returncode == 0:
            log.info("deploy SUCCESS (commit=%s)", commit)
        else:
            log.error("deploy FAILED (commit=%s exit=%d)", commit, result.returncode)

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, "ok")
        else:
            self._respond(404, "not found")


def main():
    parser = argparse.ArgumentParser(description="JEBAT auto-deploy webhook")
    parser.add_argument("--port", type=int, default=8081, help="listen port")
    parser.add_argument("--secret", default="", help="GitHub webhook secret")
    parser.add_argument("--host", default="127.0.0.1", help="bind address")
    args = parser.parse_args()

    DeployHandler.secret = args.secret

    if not os.path.exists(DEPLOY_SCRIPT):
        log.error("deploy script not found: %s", DEPLOY_SCRIPT)
        sys.exit(1)

    server = HTTPServer((args.host, args.port), DeployHandler)
    log.info(
        "listening on %s:%s  secret=%s  script=%s",
        args.host, args.port,
        "yes" if args.secret else "no",
        DEPLOY_SCRIPT,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        log.info("shutdown")


if __name__ == "__main__":
    main()
