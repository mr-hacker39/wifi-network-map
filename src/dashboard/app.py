
import json
from pathlib import Path

from flask import Flask, render_template, send_file

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCAN_FILE = PROJECT_ROOT / "data" / "network_scan.json"
MAP_FILE = PROJECT_ROOT / "docs" / "network_map.html"

app = Flask(__name__)


def load_scan_data():
    if not SCAN_FILE.exists():
        return {
            "network": "Not scanned yet",
            "device_count": 0,
            "scan_time": "No scan available",
            "devices": [],
        }

    try:
        with SCAN_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {
            "network": "Data unavailable",
            "device_count": 0,
            "scan_time": "Could not read scan data",
            "devices": [],
        }


@app.route("/")
def dashboard():
    scan_data = load_scan_data()

    return render_template(
        "index.html",
        scan=scan_data,
        map_available=MAP_FILE.exists(),
    )


@app.route("/network-map")
def network_map():
    if not MAP_FILE.exists():
        return "Network map not generated yet.", 404

    return send_file(MAP_FILE, mimetype="text/html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
