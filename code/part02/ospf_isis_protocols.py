"""Chapter 2.14 model: IS-IS Network Entity Title (NET = Area + 6-byte System ID
+ N-selector 00) parser and loopback IPv4-to-System-ID converter, OSPF auto-cost
reference-bandwidth link metric calculator, OSPF neighbor state-machine
transition checker, and EIGRP classic composite metric calculator.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 15 ("Distance Vector Control Planes": STP root/port election and
  reactive MAC learning, RIP RFC 1058/2453, EIGRP RFC 7868 DUAL and classic
  composite metric) and Chapter 16 ("Link State and Path Vector Control Planes":
  OSPF 1989 / OSPFv2 RFC 2328 / OSPFv3 RFC 5340 and IS-IS ISO 10589 / RFC 1195
  comparative anatomy, NET addressing, IIH/CSNP/PSNP/LSP, SRM flags, OSPF LSA
  types 1..7 and packet types 1..5, neighbor state machine).
"""
from typing import Dict


def ipv4_to_isis_system_id(ipv4_str: str) -> str:
    """Convert an IPv4 loopback ('192.168.1.1') to a 6-byte dotted-hex/BCD IS-IS System ID ('1921.6800.1001')."""
    octets = [int(x) for x in ipv4_str.strip().split(".")]
    if len(octets) != 4 or any(not (0 <= b <= 255) for b in octets):
        raise ValueError(f"Invalid IPv4 address: {ipv4_str}")
    digits = "".join(f"{b:03d}" for b in octets)  # 12 decimal digits
    return f"{digits[0:4]}.{digits[4:8]}.{digits[8:12]}"


def parse_isis_net(net_str: str) -> Dict[str, str]:
    """Parse an IS-IS NET ('49.0001.1921.6800.1001.00') into area_address, system_id, and nsel."""
    parts = net_str.strip().split(".")
    if len(parts) < 5 or len(parts[-1]) != 2:
        raise ValueError(f"Invalid IS-IS NET: {net_str}")
    nsel = parts[-1]
    sys_id = ".".join(parts[-4:-1])
    area = ".".join(parts[:-4])
    if len(sys_id.replace(".", "")) != 12 or not area:
        raise ValueError(f"Malformed System ID or Area in NET: {net_str}")
    return {"area": area, "system_id": sys_id, "nsel": nsel}


def compute_ospf_interface_cost(
    link_speed_mbps: int,
    reference_bandwidth_mbps: int = 100,
) -> int:
    """Compute OSPF interface cost = max(1, int(reference_bandwidth_mbps // link_speed_mbps))."""
    if link_speed_mbps <= 0 or reference_bandwidth_mbps <= 0:
        raise ValueError("Bandwidths must be positive")
    return max(1, reference_bandwidth_mbps // link_speed_mbps)


def diagnose_ospf_neighbor_state(
    hello_params_match: bool,
    two_way_seen: bool,
    is_broadcast_drother_pair: bool,
    mtu_and_router_id_valid: bool,
) -> str:
    """Determine the steady OSPF neighbor state given adjacency checks."""
    if not hello_params_match:
        return "Down"
    if not two_way_seen:
        return "Init"
    if is_broadcast_drother_pair:
        return "2-Way"
    if not mtu_and_router_id_valid:
        return "ExStart_or_Exchange"
    return "Full"


def compute_eigrp_classic_metric(min_bw_kbps: int, total_delay_tens_of_us: int) -> int:
    """Compute EIGRP classic composite metric (K1=K3=1, K2=K4=K5=0): 256 * (10^7 // min_bw_kbps + total_delay_tens_of_us)."""
    if min_bw_kbps <= 0 or total_delay_tens_of_us < 0:
        raise ValueError("Invalid EIGRP bandwidth or delay")
    return 256 * ((10_000_000 // min_bw_kbps) + total_delay_tens_of_us)
