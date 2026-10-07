import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path("data")
SCAN_FILE = DATA_DIR / "network_scan.json"


def save_scan(network, devices):
    """Save network scan results as JSON."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    scan_data = {
        "scan_time": datetime.now().astimezone().isoformat(),
        "network": network,
        "device_count": len(devices),
        "devices": devices
    }

    with open(SCAN_FILE, "w", encoding="utf-8") as file:
        json.dump(
            scan_data,
            file,
            indent=4
        )

    return SCAN_FILE


def load_scan():
    """Load the latest scan results."""

    if not SCAN_FILE.exists():
        return None

    with open(SCAN_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


if __name__ == "__main__":
    print(f"Scan file: {SCAN_FILE}")