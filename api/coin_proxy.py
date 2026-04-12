#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

BASE_DIR = Path("/var/www/html")
API_DIR = BASE_DIR / "api"
PRIVATE_DIR = BASE_DIR / "private"

JOB_FILE = PRIVATE_DIR / "photobooth_current_print.json"
PRINT_WRAPPER = API_DIR / "sumup_print_wrapper.php"

COIN_SECRET = os.getenv("COIN_SECRET", "shared-secret")
HOST = os.getenv("COIN_PROXY_HOST", "0.0.0.0")
PORT = int(os.getenv("COIN_PROXY_PORT", "8081"))


def load_job():
    if not JOB_FILE.exists():
        return None

    try:
        with JOB_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        app.logger.error("Job-Datei konnte nicht gelesen werden: %s", exc)
        return None


def save_job(job):
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w",
        delete=False,
        dir=str(PRIVATE_DIR),
        encoding="utf-8",
    ) as tmp:
        json.dump(job, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = tmp.name

    # Wichtig:
    # Die Datei darf anschließend von PHP/www-data wieder überschrieben werden.
    # Deshalb bewusst group-writable setzen.
    os.chmod(tmp_path, 0o664)
    os.replace(tmp_path, JOB_FILE)

    try:
        os.chmod(JOB_FILE, 0o664)
    except Exception as exc:
        app.logger.warning("Konnte Rechte auf Job-Datei nicht setzen: %s", exc)


def payment_mode_allows_coin(job):
    provider = str(job.get("provider", "")).strip().lower()
    payment_mode = str(job.get("payment_mode", "")).strip().lower()

    if provider in ("coin", "sumup_coin"):
        return True

    return payment_mode in {
        "coin",
        "terminal_coin",
        "qr_coin",
        "terminal_qr_coin",
    }


def run_print_wrapper():
    if not PRINT_WRAPPER.exists():
        raise FileNotFoundError(f"Wrapper nicht gefunden: {PRINT_WRAPPER}")

    result = subprocess.run(
        ["php", str(PRINT_WRAPPER)],
        capture_output=True,
        text=True,
        check=False,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


@app.route("/health", methods=["GET"])
def health():
    job = load_job()
    return jsonify(
        {
            "status": "ok",
            "job_file_exists": JOB_FILE.exists(),
            "wrapper_exists": PRINT_WRAPPER.exists(),
            "job_present": job is not None,
        }
    ), 200


@app.route("/coin-paid", methods=["POST"])
def coin_paid():
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify({"status": "invalid_json"}), 400

    if not isinstance(data, dict):
        return jsonify({"status": "invalid_json"}), 400

    secret = str(data.get("secret", ""))
    amount_cents_received = int(data.get("amount_cents_received", 0))

    if secret != COIN_SECRET:
        return jsonify({"status": "invalid_secret"}), 403

    job = load_job()
    if job is None:
        return jsonify({"status": "no_active_job"}), 404

    if not payment_mode_allows_coin(job):
        return jsonify(
            {
                "status": "coin_not_allowed_for_job",
                "provider": job.get("provider"),
                "payment_mode": job.get("payment_mode"),
            }
        ), 409

    if job.get("printed") is True:
        return jsonify({"status": "already_printed"}), 200

    job["paid"] = True
    job["amount_cents_received"] = amount_cents_received
    job["payment_channel"] = "coin"
    save_job(job)

    wrapper_result = run_print_wrapper()

    if wrapper_result["returncode"] != 0:
        app.logger.error("Wrapper-Fehler stdout=%s", wrapper_result["stdout"])
        app.logger.error("Wrapper-Fehler stderr=%s", wrapper_result["stderr"])
        return jsonify(
            {
                "status": "print_failed",
                "returncode": wrapper_result["returncode"],
            }
        ), 500

    job_after = load_job() or {}
    job_after["paid"] = True
    job_after["printed"] = True
    job_after["amount_cents_received"] = amount_cents_received
    job_after["payment_channel"] = "coin"
    save_job(job_after)

    return jsonify(
        {
            "status": "printed",
            "amount_cents_received": amount_cents_received,
        }
    ), 200


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
