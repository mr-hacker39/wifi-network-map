
import json
import os
import subprocess
import sys
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

# Allow imports from the src directory when this file is run directly.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from monitoring.monitor import (
    get_events,
    get_history,
    get_monitor_status,
    scan_once,
    start_monitoring,
    stop_monitoring,
)

SCAN_FILE = PROJECT_ROOT / "data" / "network_scan.json"
MAP_FILE = PROJECT_ROOT / "docs" / "network_map.html"

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "local-development-key-change-me",
)


def load_scan_data():
    """Load the most recent saved network scan."""
    if not SCAN_FILE.exists():
        return {
            "network": "Not scanned yet",
            "device_count": 0,
            "scan_time": "No scan available",
            "devices": [],
        }

    try:
        with SCAN_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("Scan data must be a JSON object.")
            return data
    except (json.JSONDecodeError, OSError, ValueError):
        return {
            "network": "Data unavailable",
            "device_count": 0,
            "scan_time": "Could not read scan data",
            "devices": [],
        }


@app.route("/")
def dashboard():
    return render_template(
        "index.html",
        scan=load_scan_data(),
        map_available=MAP_FILE.is_file(),
        monitor=get_monitor_status(),
        history=get_history(10),
        events=get_events(10),
    )


@app.route("/network-map")
def network_map():
    if not MAP_FILE.is_file():
        return "Network map not generated yet.", 404

    return send_file(MAP_FILE, mimetype="text/html")


@app.route("/rescan", methods=["POST"])
def rescan():
    try:
        scan_once()
        flash(
            "Network scan, device history, and topology map updated.",
            "success",
        )
    except subprocess.TimeoutExpired:
        flash("The scan timed out. Please try again.", "error")
    except (FileNotFoundError, RuntimeError, OSError, ValueError) as error:
        app.logger.exception("Network rescan failed")
        flash(f"Rescan failed: {error}", "error")

    return redirect(url_for("dashboard"))


@app.route("/monitor/start", methods=["POST"])
def monitor_start():
    try:
        interval = int(request.form.get("interval", "60"))
        start_monitoring(interval)
        flash(
            f"Monitoring started with a {interval}-second scan interval.",
            "success",
        )
    except (TypeError, ValueError) as error:
        flash(f"Could not start monitoring: {error}", "error")

    return redirect(url_for("dashboard"))


@app.route("/monitor/stop", methods=["POST"])
def monitor_stop():
    stop_monitoring()
    flash("Monitoring stop requested.", "success")
    return redirect(url_for("dashboard"))


@app.route("/history")
def history_page():
    return render_template(
        "history.html",
        history=get_history(100),
        events=get_events(100),
    )


if __name__ == "__main__":
    # Keep one Flask process so the background monitor isn't duplicated.
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False,
    )
