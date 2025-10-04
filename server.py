import os, subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.get("/")
def health():
    return "OK", 200

@app.post("/run")
def run():
    token = request.args.get("token") or request.headers.get("X-CRON-TOKEN")
    if token != os.getenv("CRON_TOKEN"):
        return jsonify({"error": "forbidden"}), 403
    try:
        subprocess.run(["bash", "run_cron.sh"], check=True)
        return jsonify({"status": "ok"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "script failed", "code": e.returncode}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
