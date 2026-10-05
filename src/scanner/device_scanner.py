import subprocess
import xml.etree.ElementTree as ET
import ipaddress
import re


def get_network():
    """Automatically detect the IPv4 network used by the default route."""

    try:
        route = subprocess.run(
            ["ip", "-4", "route", "show", "default"],
            capture_output=True,
            text=True,
            check=True
        )

        parts = route.stdout.split()

        if "dev" not in parts:
            return None

        interface = parts[parts.index("dev") + 1]

        address = subprocess.run(
            ["ip", "-4", "addr", "show", "dev", interface],
            capture_output=True,
            text=True,
            check=True
        )

        match = re.search(
            r"inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)",
            address.stdout
        )

        if not match:
            return None

        ip = match.group(1)
        prefix = int(match.group(2))

        network = ipaddress.ip_network(
            f"{ip}/{prefix}",
            strict=False
        )

        return str(network)

    except (subprocess.CalledProcessError, ValueError):
        return None


def scan_network(network):
    """Discover active devices using Nmap XML output."""

    print(f"Scanning network: {network}")
    print("-" * 60)

    try:
        result = subprocess.run(
            [
                "nmap",
                "-sn",
                "-oX",
                "-",
                network
            ],
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout

    except subprocess.CalledProcessError as error:
        print("Nmap scan failed.")
        print(error.stderr)
        return ""


def parse_devices(xml_output):
    """Parse Nmap XML output and extract device information."""

    devices = []

    if not xml_output:
        return devices

    try:
        root = ET.fromstring(xml_output)

        for host in root.findall("host"):

            status = host.find("status")

            if status is None:
                continue

            if status.get("state") != "up":
                continue

            ip_address = "Unknown"
            mac_address = "Unknown"
            vendor = "Unknown"
            hostname = "Unknown"

            # IP address
            for address in host.findall("address"):
                if address.get("addrtype") == "ipv4":
                    ip_address = address.get("addr", "Unknown")

                elif address.get("addrtype") == "mac":
                    mac_address = address.get("addr", "Unknown")
                    vendor = address.get("vendor", "Unknown")

            # Hostname
            hostnames = host.find("hostnames")

            if hostnames is not None:
                hostname_entry = hostnames.find("hostname")

                if hostname_entry is not None:
                    hostname = hostname_entry.get(
                        "name",
                        "Unknown"
                    )

            devices.append(
                {
                    "ip": ip_address,
                    "mac": mac_address,
                    "hostname": hostname,
                    "vendor": vendor,
                    "status": "up"
                }
            )

    except ET.ParseError as error:
        print("Failed to parse Nmap XML output.")
        print(error)

    return devices


def display_devices(devices):
    """Display discovered devices."""

    print("\nDiscovered Devices")
    print("=" * 80)

    if not devices:
        print("No devices discovered.")
        return

    for number, device in enumerate(devices, start=1):

        print(
            f"{number}. "
            f"IP: {device['ip']} | "
            f"MAC: {device['mac']} | "
            f"Hostname: {device['hostname']} | "
            f"Vendor: {device['vendor']}"
        )

    print("=" * 80)
    print(f"Total devices: {len(devices)}")


def main():

    print("=" * 80)
    print("                    WIFI NETWORK MAP")
    print("                    DEVICE SCANNER")
    print("=" * 80)

    network = get_network()

    if not network:
        print("Could not determine the local network.")
        return

    print(f"Detected network: {network}")

    scan_output = scan_network(network)

    devices = parse_devices(scan_output)

    display_devices(devices)


if __name__ == "__main__":
    main()