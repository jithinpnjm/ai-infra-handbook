"""Chapter 2.26 model: Classic BPF / pcap-filter byte-offset evaluator (TCP flags
ip/tcp[tcpflags], IPv4 More-Fragments bit ip[6:2] & 0x2000, TTL ip[8], and
DSCP/ECN ip[1] byte masks), tcpdump ring-buffer storage and high-rate packet
rate calculator, and two-endpoint packet-capture diff analyzer.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 10
  (tcpdump output, primitives and operators).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 10 (packet sniffing, tcpdump/Wireshark, TCP analysis) and Chapter 15
  ("BPF": BCC and bpftrace architecture, kprobes/tracepoints/uprobes/USDT, maps,
  networking tools and one-liners).
- James Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapter 1.
- nvidia-devops/volume-01/03-linux-networking-masterclass.md.
"""
from typing import Dict


TCP_FIN = 0x01
TCP_SYN = 0x02
TCP_RST = 0x04
TCP_PSH = 0x08
TCP_ACK = 0x10


def evaluate_pcap_byte_offset_filters(
    ip_tos_byte: int,
    ip_flags_frag_u16: int,
    ip_ttl_byte: int,
    tcp_flags_byte: int,
) -> Dict[str, bool]:
    """Evaluate the byte-offset pcap-filter expressions from Section 2."""
    return {
        "syn_only": (tcp_flags_byte & (TCP_SYN | TCP_ACK)) == TCP_SYN,
        "rst_or_fin": (tcp_flags_byte & (TCP_RST | TCP_FIN)) != 0,
        "more_fragments": (ip_flags_frag_u16 & 0x2000) != 0,
        "ttl_below_5": ip_ttl_byte < 5,
        "dscp_ef_46": (ip_tos_byte & 0xFC) == 0xB8,  # 46 << 2 = 184 = 0xB8
        "ecn_ce_3": (ip_tos_byte & 0x03) == 3,
    }


def compute_capture_rate_and_ring_storage(
    link_gbps: float,
    frame_bytes: int,
    snaplen_bytes: int,
    ring_file_mb: int,
    ring_file_count: int,
) -> Dict[str, float]:
    """Compute wire packet rate (Mpps), truncated capture write rate (MB/s), and max ring-buffer disk usage."""
    if link_gbps <= 0 or frame_bytes <= 0 or snaplen_bytes <= 0 or ring_file_mb <= 0 or ring_file_count <= 0:
        raise ValueError("Capture parameters must be positive")
    wire_frame_bytes = frame_bytes + 38  # Ethernet preamble/SFD/header/FCS/IFG
    pps = (link_gbps * 1e9 / 8.0) / float(wire_frame_bytes)
    mpps = round(pps / 1e6, 2)
    captured_bytes_per_pkt = min(frame_bytes, snaplen_bytes) + 16  # 16B pcap packet record header
    write_mb_per_sec = round((pps * captured_bytes_per_pkt) / 1e6, 1)
    max_disk_mb = float(ring_file_mb * ring_file_count)
    return {
        "wire_mpps": mpps,
        "capture_write_mb_s": write_mb_per_sec,
        "max_ring_disk_mb": max_disk_mb,
    }


def diagnose_two_side_tcp_capture(
    syn_sent_by_client: bool,
    syn_seen_at_server: bool,
    synack_sent_by_server: bool,
    synack_seen_at_client: bool,
    rst_ttl_differs_from_server: bool = False,
) -> str:
    """Compare client-side and server-side packet captures to pinpoint where a connection failed."""
    if rst_ttl_differs_from_server:
        return "middlebox_injected_rst"
    if syn_sent_by_client and not syn_seen_at_server:
        return "forward_path_dropped_syn"
    if syn_seen_at_server and not synack_sent_by_server:
        return "server_firewall_or_listen_backlog_dropped_syn"
    if synack_sent_by_server and not synack_seen_at_client:
        return "return_path_or_asymmetric_nat_dropped_synack"
    return "handshake_succeeded"
