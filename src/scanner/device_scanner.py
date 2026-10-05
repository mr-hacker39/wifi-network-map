import subprocess
import re


NETWORK = "10.56.14.0/24"


def scan_network(network):
    """Discover active devices using Nmap."""
    print(f"Scanning network: {network}")
    print("-" * 60)

    try:
        result = subprocess.run(
            ["sudo", "nmap", "-sn", network],
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout

    except subprocess.CalledProcessError as error:
        print("Nmap scan failed.")
        print(error)
        return ""


def parse_devices(scan_output):
    """Extract IP addresses from Nmap output."""
    devices = []

    for line in scan_output.splitlines():

        match = re.search(
            r"Nmap scan report for (?:[^(]+\()?(\d+\.\d+\.\d+\.\d+)\)?",
            line
        )

        if match:
            ip = match.group(1)

            devices.append({
                "ip": ip
            })

    return devices


def display_devices(devices):
    """Display discovered devices."""
    print("\nDiscovered Devices")
    print("=" * 60)

    if not devices:
        print("No devices discovered.")
        return

    for number, device in enumerate(devices, start=1):
        print(f"{number}. IP Address: {device['ip']}")

    print("=" * 60)
    print(f"Total devices: {len(devices)}")


def main():
    scan_output = scan_network(NETWORK)

    devices = parse_devices(scan_output)

    display_devices(devices)


if __name__ == "__main__":
    main()