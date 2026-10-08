import json
import re
from pathlib import Path

import networkx as nx
from pyvis.network import Network


SCAN_FILE = Path("data/network_scan.json")
OUTPUT_FILE = Path("docs/network_map.html")


def load_scan_data():
    """Load the latest network scan data."""

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
        label=network
    )

    # Add device nodes
    for device in devices:

        ip = device.get("ip", "Unknown")

        if ip == "Unknown":
            continue

        hostname = device.get("hostname", "Unknown")
        status = device.get("status", "unknown")
        mac = device.get("mac", "Unknown")
        vendor = device.get("vendor", "Unknown")

        # Identify the gateway
        is_gateway = ip.endswith(".192")

        graph.add_node(
            ip,
            node_type="gateway" if is_gateway else "device",
            hostname=hostname,
            status=status,
            mac=mac,
            vendor=vendor,
            label=ip
        )

        graph.add_edge(
            network,
            ip,
            relationship="connected"
        )

    return graph


def create_visualization(graph):
    """Create an interactive HTML network map."""

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    network = Network(
        height="750px",
        width="100%",
        bgcolor="#111111",
        font_color="white",
        cdn_resources="in_line"
    )

    network.set_options("""
    {
      "nodes": {
        "shape": "dot",
        "size": 25,
        "font": {
          "size": 18
        }
      },
      "edges": {
        "width": 2,
        "smooth": {
          "type": "dynamic"
        }
      },
      "physics": {
        "enabled": true,
        "stabilization": {
          "iterations": 200
        }
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)

    # Add nodes
    for node, attributes in graph.nodes(data=True):

        node_type = attributes.get(
            "node_type",
            "device"
        )

        if node_type == "network":
            title = f"""
            <b>Network</b><br>
            Network: {node}
            """

            network.add_node(
                node,
                label=node,
                title=title,
                size=35
            )

        elif node_type == "gateway":
            title = f"""
            <b>Gateway</b><br>
            IP: {node}<br>
            Hostname: {attributes.get('hostname')}<br>
            MAC: {attributes.get('mac')}<br>
            Vendor: {attributes.get('vendor')}<br>
            Status: {attributes.get('status')}
            """

            network.add_node(
                node,
                label=f"Gateway\n{node}",
                title=title,
                size=30
            )

        else:
            title = f"""
            <b>Device</b><br>
            IP: {node}<br>
            Hostname: {attributes.get('hostname')}<br>
            MAC: {attributes.get('mac')}<br>
            Vendor: {attributes.get('vendor')}<br>
            Status: {attributes.get('status')}
            """

            network.add_node(
                node,
                label=node,
                title=title,
                size=25
            )

    # Add edges
    for source, destination, attributes in graph.edges(data=True):

        network.add_edge(
            source,
            destination,
            title=attributes.get(
                "relationship",
                "connected"
            )
        )

    network.write_html(
        str(OUTPUT_FILE),
        open_browser=False
    )

    remove_external_resources()

    return OUTPUT_FILE

def remove_external_resources():
    """Remove external Bootstrap CDN references from the generated HTML."""

    if not OUTPUT_FILE.exists():
        return

    html = OUTPUT_FILE.read_text(encoding="utf-8")

    html = re.sub(
        r'<link[^>]+bootstrap[^>]+>\s*',
        '',
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r'<script[^>]+bootstrap[^>]+></script>\s*',
        '',
        html,
        flags=re.IGNORECASE
    )

    OUTPUT_FILE.write_text(
        html,
        encoding="utf-8"
    )
def main():

    print("=" * 70)
    print("                 WIFI NETWORK MAP")
    print("                 INTERACTIVE VISUALIZER")
    print("=" * 70)

    scan_data = load_scan_data()

    graph = build_topology(scan_data)

    output_file = create_visualization(graph)

    print("\nVisualization created successfully.")
    print(f"Nodes : {graph.number_of_nodes()}")
    print(f"Edges : {graph.number_of_edges()}")
    print(f"Output: {output_file}")

    print("=" * 70)


if __name__ == "__main__":
    main()