#!/usr/bin/env python3
"""Planning helpers for a BCM install, built from numbers and rules in the BCM 11 Installation Manual.

  sizing:   Appendix B heuristics for head node RAM and disk, and regular node RAM and disk
  naming:   node base name + digits (3.3.11)
  addresses: sequential interface addresses with an IP offset (3.3.15), with an overlap check
  disk:     default head node layout choice by drive size (1.1 step 19, 3.3.17)
These are the manual's rules, not measurements. Always check the manual and your own cluster.
"""
import ipaddress, re


# ---- Appendix B: sizing ---------------------------------------------------------------------------------
def head_node_ram_gb(nodes, os_ram_gb=0.0, metrics_per_device=100):
    """RAM = OS processes + 100 MB + nodes x 1.8 MB (valid for up to 100 metrics and health checks per device);
    each further 100 metrics and checks add about 1 MB per device (B.1.2)."""
    extra_blocks = max(0, (metrics_per_device - 100) / 100.0)
    mb = 100 + nodes * 1.8 + extra_blocks * 1.0 * nodes
    return os_ram_gb + mb / 1000.0


def head_node_disk_gb(devices, regular_node_images=1, os_disk_gb=0.0, metrics_per_device=100):
    """Disk = OS without BCM + 5 GB per regular node image + 100 kB x (metrics and health checks) x devices (B.1.2)."""
    return os_disk_gb + 5.0 * regular_node_images + 100e3 * metrics_per_device * devices / 1e9


def regular_node_ram_gb(nodes, non_bcm_ram_gb=0.0):
    """RAM = non-BCM processes + 50 MB + nodes x 10 kB (B.1.1)."""
    return non_bcm_ram_gb + (50e6 + nodes * 10e3) / 1e9


# the manual's observed table (B.2.1): nodes -> (CMDaemon+MySQL RAM GB, CMDaemon RAM GB, disk GB)
OBSERVED = {1000: (16, 2, 10), 2000: (32, 4, 20), 5000: (64, 10, 50)}


# ---- naming and addresses -----------------------------------------------------------------------------
def node_names(count, base="node", start=1, digits=3):
    names = [f"{base}{i:0{digits}d}" for i in range(start, start + count)]
    if any(len(re.sub(r"^\D+", "", n)) > digits for n in names):
        raise ValueError(f"{count} nodes starting at {start} do not fit in {digits} digits")
    return names


def interface_addresses(network, count, offset="0.0.0.0"):
    """Sequential addresses in steps of 1, starting after the network base address, plus an offset (3.3.15)."""
    net = ipaddress.ip_network(network)
    off = int(ipaddress.ip_address(offset))
    first = int(net.network_address) + 1 + off
    addrs = [ipaddress.ip_address(first + i) for i in range(count)]
    if any(a not in net for a in addrs):
        raise ValueError(f"{count} addresses with offset {offset} do not fit in {network}")
    return [str(a) for a in addrs]


def overlap(a_list, b_list):
    return sorted(set(a_list) & set(b_list))


# ---- disk layout default --------------------------------------------------------------------------------
def default_head_layout(drive_gb):
    """Below about 500 GB: master-one-big-partition.xml. Otherwise master-standard.xml (1.1 step 19)."""
    if drive_gb < 500:
        return "master-one-big-partition.xml", [("/boot", "1G"), ("/boot/efi", "100M"), ("swap", "16G"), ("/", "rest")]
    return "master-standard.xml", [("/boot", "1G"), ("/boot/efi", "100M"), ("swap", "16G"), ("/tmp", "20G"), ("/var", "180G"), ("/", "rest")]


# ---- network topology (3.3.9, 3.3.13) -------------------------------------------------------------------
TOPOLOGIES = {
    1: {"networks": ["externalnet", "internalnet"], "node_traffic_leaves_via": "head node (routed and forwarded there)", "head_dhcp_relay_needed": False},
    2: {"networks": ["internalnet"], "node_traffic_leaves_via": "a router, not the head node", "head_dhcp_relay_needed": "only if nodes span several subnets"},
    3: {"networks": ["internalnet", "managementnet"], "node_traffic_leaves_via": "a router; head node is on another network", "head_dhcp_relay_needed": True},
}
