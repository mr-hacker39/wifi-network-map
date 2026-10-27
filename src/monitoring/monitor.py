
import json
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SCAN_FILE = DATA_DIR / "network_scan.json"
HISTORY_FILE = DATA_DIR / "scan_history.json"
EVENTS_FILE = DATA_DIR / "device_events.json"

MIN_INTERVAL = 30
MAX_INTERVAL = 3600
SCRIPT_TIMEOUT = 120

_monitor_lock = threading.Lock()
_stop_event = threading.Event()
_monitor_thread = None

_monitor_status = {
    "running": False,
    "message": "Monitoring is stopped.",
    "last_scan": None,
    "last_error": None,
}


def current_time():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default):
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    temporary_path.replace(path)


def device_key(device):
    return device.get("ip", "Unknown")


def record_latest_scan():
    scan = read_json(SCAN_FILE, {})

    if not scan.get("scan_time") or not isinstance(scan.get("devices"), list):
        raise RuntimeError("No valid scan found. Run a network scan first.")

    history = read_json(HISTORY_FILE, [])
    events = read_json(EVENTS_FILE, [])

    if not isinstance(history, list):
        history = []
    if not isinstance(events, list):
        events = []

    network = scan.get("network", "Unknown")
    current_devices = {
        device_key(device): device
        for device in scan["devices"]
        if device.get("ip")
    }

    previous_devices = {}
    previous_network = None

    if history:
        previous_network = history[-1].get("network")
        if previous_network == network:
            previous_devices = {
                device_key(device): device
                for device in history[-1].get("devices", [])
                if device.get("ip")
            }

    timestamp = current_time()

    for ip, device in current_devices.items():
        if ip not in previous_devices:
            event_type = "first_seen" if not history else "appeared"
            events.append({
                "time": timestamp,
                "type": event_type,
                "ip": ip,
                "hostname": device.get("hostname", "Unknown"),
                "mac": device.get("mac", "Unknown"),
                "network": network,
            })

    for ip, device in previous_devices.items():
        if ip not in current_devices:
            events.append({
                "time": timestamp,
                "type": "not_seen",
                "ip": ip,
                "hostname": device.get("hostname", "Unknown"),
                "mac": device.get("mac", "Unknown"),
                "network": network,
            })

    history.append({
        "time": timestamp,
        "scan_time": scan.get("scan_time"),
        "network": network,
        "device_count": len(current_devices),
        "devices": list(current_devices.values()),
    })

    write_json(HISTORY_FILE, history[-500:])
    write_json(EVENTS_FILE, events[-1000:])

    return scan


def run_script(relative_path):
    script_path = PROJECT_ROOT / relative_path

    if not script_path.is_file():
        raise FileNotFoundError(f"Project script not found: {script_path}")

    env = __import__("os").environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT / "src")
        + (":" + existing_pythonpath if existing_pythonpath else "")
    )

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT,
        check=False,
    )

    if result.returncode != 0:
        details = (result.stderr or result.stdout or "Unknown error").strip()
        raise RuntimeError(f"{relative_path} failed: {details}")

    return result.stdout.strip()


def scan_once():
    with _monitor_lock:
        _monitor_status["message"] = "Scanning network..."
        _monitor_status["last_error"] = None

        try:
            run_script("src/scanner/device_scanner.py")
            scan = record_latest_scan()
            run_script("src/topology/topology_visualizer.py")

            _monitor_status["last_scan"] = current_time()
            _monitor_status["message"] = "Scan and network map updated."
            return scan
        except Exception as error:
            _monitor_status["last_error"] = str(error)
            _monitor_status["message"] = "The latest scan failed."
            raise


def _monitor_loop(interval):
    try:
        while not _stop_event.is_set():
            try:
                scan_once()
            except Exception:
                # Keep monitoring; the dashboard exposes the latest error.
                pass

            if _stop_event.wait(interval):
                break
    finally:
        _monitor_status["running"] = False
        _monitor_status["message"] = "Monitoring is stopped."


def start_monitoring(interval=60):
    global _monitor_thread

    interval = int(interval)
    if not MIN_INTERVAL <= interval <= MAX_INTERVAL:
        raise ValueError(
            f"Interval must be between {MIN_INTERVAL} and {MAX_INTERVAL} seconds."
        )

    if _monitor_thread and _monitor_thread.is_alive():
        return get_monitor_status()

    _stop_event.clear()
    _monitor_status["running"] = True
    _monitor_status["message"] = "Monitoring started."
    _monitor_status["last_error"] = None

    _monitor_thread = threading.Thread(
        target=_monitor_loop,
        args=(interval,),
        daemon=True,
        name="wifi-network-monitor",
    )
    _monitor_thread.start()

    return get_monitor_status()


def stop_monitoring():
    _stop_event.set()
    _monitor_status["message"] = "Monitoring stop requested."
    return get_monitor_status()


def get_monitor_status():
    return dict(_monitor_status)


def get_history(limit=10):
    history = read_json(HISTORY_FILE, [])
    if not isinstance(history, list):
        return []
    return list(reversed(history[-limit:]))


def get_events(limit=10):
    events = read_json(EVENTS_FILE, [])
    if not isinstance(events, list):
        return []
    return list(reversed(events[-limit:]))

def get_device_presence():
    """Summarize device presence from retained scan history."""
    from datetime import datetime

    history = read_json(HISTORY_FILE, [])
    if not isinstance(history, list):
        return []

    devices = {}
    latest_scan_by_network = {}

    for scan in history:
        if isinstance(scan, dict) and scan.get("time"):
            network = scan.get("network", "Unknown")
            latest_scan_by_network[network] = scan

    for scan in history:
        if not isinstance(scan, dict):
            continue

        scan_time = scan.get("time")
        network = scan.get("network", "Unknown")

        if not scan_time:
            continue

        try:
            observed_at = datetime.fromisoformat(
                scan_time.replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            continue

        for device in scan.get("devices", []):
            if not isinstance(device, dict) or not device.get("ip"):
                continue

            key = (network, device["ip"])

            if key not in devices:
                devices[key] = {
                    "ip": device["ip"],
                    "network": network,
                    "hostname": device.get("hostname", "Unknown"),
                    "mac": device.get("mac", "Unknown"),
                    "first_seen": scan_time,
                    "last_seen": scan_time,
                    "first_time": observed_at,
                    "last_time": observed_at,
                    "scans_observed": 0,
                }

            record = devices[key]
            record["scans_observed"] += 1

            if observed_at < record["first_time"]:
                record["first_time"] = observed_at
                record["first_seen"] = scan_time

            if observed_at >= record["last_time"]:
                record["last_time"] = observed_at
                record["last_seen"] = scan_time
                record["hostname"] = device.get("hostname", "Unknown")
                record["mac"] = device.get("mac", "Unknown")

    results = []

    for record in devices.values():
        duration = (
            record["last_time"] - record["first_time"]
        ).total_seconds()

        record["observed_duration_seconds"] = max(0, int(duration))
        latest_scan = latest_scan_by_network.get(record["network"])

        if latest_scan is None:
            record["latest_scan_status"] = "Unknown"
        else:
            latest_ips = {
                device.get("ip")
                for device in latest_scan.get("devices", [])
                if isinstance(device, dict) and device.get("ip")
            }

            record["latest_scan_status"] = (
                "Seen in latest scan"
                if record["ip"] in latest_ips
                else "Not seen in latest scan"
            )

        # Remove internal datetime values before returning JSON/template data.
        del record["first_time"]
        del record["last_time"]

        results.append(record)

    return sorted(
        results,
        key=lambda item: item["last_seen"],
        reverse=True,
    )
