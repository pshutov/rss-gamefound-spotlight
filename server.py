import os, subprocess, logging
from flask import Flask, request, jsonify

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)

@app.get("/")
def health():
    return "OK", 200

@app.post("/run")
def run():
    token = request.args.get("token") or request.headers.get("X-CRON-TOKEN")
    if token != os.getenv("CRON_TOKEN"):
        log.warning("Forbidden /run request (invalid token)")
        return jsonify({"error": "forbidden"}), 403
    log.info("Starting cron job via /run")
    try:
        result = subprocess.run(
            ["bash", "run_cron.sh"],
            capture_output=True, text=True, check=True,
        )
        if result.stdout:
            log.info("cron stdout:\n%s", result.stdout)
        if result.stderr:
            log.warning("cron stderr:\n%s", result.stderr)
        log.info("Cron job finished successfully")
        return jsonify({"status": "ok"}), 200
    except subprocess.CalledProcessError as e:
        log.error("Cron job failed (code %d)", e.returncode)
        if e.stdout:
            log.error("stdout:\n%s", e.stdout)
        if e.stderr:
            log.error("stderr:\n%s", e.stderr)
        return jsonify({"error": "script failed", "code": e.returncode}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    log.info("Starting server on port %d", port)
    app.run(host="0.0.0.0", port=port)
