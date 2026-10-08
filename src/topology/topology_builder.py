import json
from pathlib import Path

import networkx as nx


SCAN_FILE = Path("data/network_scan.json")


def load_scan_data():
    """Load the latest network scan."""

    if not SCAN_FILE.exists():
        raise FileNotFoundError(
            f"Scan file not found: {SCAN_FILE}"
        )

    with open(SCAN_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def build_topology(scan_data):
    """Build a logical network topology graph."""

    graph = nx.Graph()

    network = scan_data.get("network", "Unknown")
    devices = scan_data.get("devices", [])

    # Add network node
    graph.add_node(
        network,
        node_type="network",
        label=f"Network\n{network}"
    )

    # Add device nodes
    for device in devices:

        ip = device.get("ip", "Unknown")

        if ip == "Unknown":
            continue

        hostname = device.get("hostname", "Unknown")
        status = device.get("status", "unknown")

        graph.add_node(
            ip,
            node_type="device",
            hostname=hostname,
            status=status,
            mac=device.get("mac", "Unknown"),
            vendor=device.get("vendor", "Unknown")
        )

        # Connect device to the network
        graph.add_edge(
            network,
            ip,
            relationship="connected"
        )

    return graph


def display_topology(graph):
    """Display the topology in the terminal."""

    print("\nNetwork Topology")
    print("=" * 60)

    print(f"Nodes : {graph.number_of_nodes()}")
    print(f"Edges : {graph.number_of_edges()}")

    print("\nNodes")
    print("-" * 60)

    for node, attributes in graph.nodes(data=True):
        print(
            f"{node} | "
            f"type={attributes.get('node_type', 'unknown')} | "
            f"status={attributes.get('status', 'unknown')}"
        )

    print("\nConnections")
    print("-" * 60)

    for source, destination, attributes in graph.edges(data=True):
        print(
            f"{source} --> {destination} | "
            f"{attributes.get('relationship', 'unknown')}"
        )

    print("=" * 60)


def main():

    print("=" * 60)
    print("              NETWORK TOPOLOGY ENGINE")
    print("=" * 60)

    scan_data = load_scan_data()

    graph = build_topology(scan_data)

    display_topology(graph)


if __name__ == "__main__":
    main()