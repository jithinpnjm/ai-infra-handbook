"""Chapter 2.22 model: /proc/net/softnet_stat hex line parser (processed, dropped,
time_squeeze), ss -ti output parser and bottleneck classifier (rwnd_limited,
cwnd_limited, sndbuf_limited, app_limited), and USE method interface + PCIe bus
utilization evaluator.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapters 9
  and 10 (kernel network interfaces, ip command family, Netplan/NetworkManager/
  systemd-networkd, sockets, Unix domain sockets, lsof, nc, telnet, curl).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 10 ("Network": USE method, workload characterization, latency and TCP
  analysis, ss -ti, ip -s, nstat, sar, nicstat, ethtool, BCC/bpftrace tcplife,
  tcptop, tcpretrans, tcpdrop).
- James Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapter 2.
"""
from typing import Dict


def parse_softnet_stat_line(hex_line: str, cpu_id: int = 0) -> Dict[str, int]:
    """Parse one line of /proc/net/softnet_stat (hexadecimal columns) into integer counters.
    Column 1 (idx 0): total packets processed by softirq on this CPU.
    Column 2 (idx 1): packets dropped because netdev_max_backlog was full.
    Column 3 (idx 2): time_squeeze count (netdev_budget exhausted before queue drained).
    """
    cols = hex_line.strip().split()
    if len(cols) < 3:
        raise ValueError(f"Malformed softnet_stat line: {hex_line}")
    return {
        "cpu_id": cpu_id,
        "processed": int(cols[0], 16),
        "dropped": int(cols[1], 16),
        "time_squeeze": int(cols[2], 16),
    }


def classify_ss_ti_bottleneck(ss_ti_text: str) -> Dict[str, object]:
    """Parse ss -ti output and identify the primary TCP throughput limiter."""
    tokens = ss_ti_text.strip().split()
    kv: Dict[str, str] = {}
    flags = set()
    for tok in tokens:
        if ":" in tok:
            k, v = tok.split(":", 1)
            kv[k] = v
        else:
            flags.add(tok)

    retrans_total = 0
    if "retrans" in kv and "/" in kv["retrans"]:
        retrans_total = int(kv["retrans"].split("/")[1])

    if "sndbuf_limited" in kv:
        limiter = "send_buffer_limited"
    elif "rwnd_limited" in kv:
        limiter = "receiver_window_limited"
    elif "cwnd_limited" in kv or retrans_total > 0:
        limiter = "network_congestion_or_loss_limited"
    elif "app_limited" in flags:
        limiter = "application_limited"
    else:
        limiter = "unconstrained"

    return {
        "primary_limiter": limiter,
        "cwnd": int(kv.get("cwnd", "0")),
        "retrans_total": retrans_total,
        "app_limited": "app_limited" in flags,
    }


def evaluate_interface_and_pcie_use(
    throughput_gbps: float,
    negotiated_link_gbps: float,
    pcie_usable_gbps: float,
    rx_crc_errors_delta: int = 0,
    rx_missed_drops_delta: int = 0,
) -> Dict[str, object]:
    """Compute USE utilization for link and PCIe slot and classify bottleneck/error state."""
    if throughput_gbps < 0 or negotiated_link_gbps <= 0 or pcie_usable_gbps <= 0:
        raise ValueError("Invalid throughput or capacity parameters")
    link_util_pct = round(100.0 * throughput_gbps / negotiated_link_gbps, 1)
    pcie_util_pct = round(100.0 * throughput_gbps / pcie_usable_gbps, 1)
    pcie_bottlenecked = negotiated_link_gbps > pcie_usable_gbps
    return {
        "link_utilization_pct": link_util_pct,
        "pcie_utilization_pct": pcie_util_pct,
        "pcie_bus_bottleneck": pcie_bottlenecked,
        "has_physical_errors": rx_crc_errors_delta > 0,
        "has_host_saturation_drops": rx_missed_drops_delta > 0,
    }
