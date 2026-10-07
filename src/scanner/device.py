from dataclasses import dataclass


@dataclass
class Device:
    """Represents a device discovered on the network."""

    ip: str
    mac: str = "Unknown"
    hostname: str = "Unknown"
    vendor: str = "Unknown"
    status: str = "unknown"

    def to_dict(self):
        """Convert device information to a dictionary."""

        return {
            "ip": self.ip,
            "mac": self.mac,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "status": self.status
        }