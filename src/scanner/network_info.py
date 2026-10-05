import socket
import subprocess


def get_hostname():
    """Get the hostname of this Linux machine."""
    return socket.gethostname()


def get_default_gateway():
    """Get the default gateway."""
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            check=True
        )

        parts = result.stdout.split()

        if "via" in parts:
            return parts[parts.index("via") + 1]

    except (subprocess.CalledProcessError, ValueError):
        pass

    return "Unknown"


def get_network_interface():
    """Get the interface used by the default route."""
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            check=True
        )

        parts = result.stdout.split()

        if "dev" in parts:
            return parts[parts.index("dev") + 1]

    except (subprocess.CalledProcessError, ValueError):
        pass

    return "Unknown"


def get_local_ip():
    """Get the IPv4 address used by the default route."""
    try:
        result = subprocess.run(
            ["ip", "route", "get", "8.8.8.8"],
            capture_output=True,
            text=True,
            check=True
        )

        parts = result.stdout.split()

        if "src" in parts:
            return parts[parts.index("src") + 1]

    except (subprocess.CalledProcessError, ValueError):
        pass

    return "Unknown"


def main():
    print("=" * 55)
    print("              WIFI NETWORK MAP")
    print("=" * 55)

    print(f"Hostname          : {get_hostname()}")
    print(f"Network Interface : {get_network_interface()}")
    print(f"Local IP          : {get_local_ip()}")
    print(f"Default Gateway   : {get_default_gateway()}")

    print("=" * 55)


if __name__ == "__main__":
    main()