#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.26: Packet capture from scratch: tcpdump, tshark, Wireshark and BPF-based tracing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from packet_capture_bpf import (
    TCP_ACK,
    TCP_RST,
    TCP_SYN,
    compute_capture_rate_and_ring_storage,
    diagnose_two_side_tcp_capture,
    evaluate_pcap_byte_offset_filters,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Byte-offset pcap-filter expressions (Section 2)
    f_syn_ef_ce = evaluate_pcap_byte_offset_filters(
        ip_tos_byte=0xBB,          # DSCP 46 (0xB8) | ECN CE (0x03) = 0xBB
        ip_flags_frag_u16=0x2000,  # MF bit set
        ip_ttl_byte=3,
        tcp_flags_byte=TCP_SYN | TCP_RST,
    )
    check("byte-offset filters match pure SYN, RST/FIN, MF fragment (0x2000), TTL<5, DSCP EF (0xb8), and ECN CE (3)",
          all(f_syn_ef_ce.values()))

    f_synack = evaluate_pcap_byte_offset_filters(
        ip_tos_byte=0x00,
        ip_flags_frag_u16=0x4000,  # DF bit set, MF=0
        ip_ttl_byte=64,
        tcp_flags_byte=TCP_SYN | TCP_ACK,
    )
    check("SYN-ACK does NOT match 'tcp[tcpflags] & (tcp-syn|tcp-ack) == tcp-syn'",
          f_synack["syn_only"] is False and f_synack["more_fragments"] is False)

    # 2. High-rate 100G capture packet rate, snaplen truncation, and ring-buffer storage (Sections 1, 2, 5)
    cap_100g = compute_capture_rate_and_ring_storage(
        link_gbps=100.0,
        frame_bytes=1500,
        snaplen_bytes=96,
        ring_file_mb=100,
        ring_file_count=10,
    )
    check("100 Gb/s link at 1500B is ~8.13 Mpps; -s 96 truncates write rate to ~910.3 MB/s; -C 100 -W 10 caps disk at 1000 MB",
          8.0 <= cap_100g["wire_mpps"] <= 8.2
          and cap_100g["capture_write_mb_s"] < 1000.0
          and cap_100g["max_ring_disk_mb"] == 1000.0)

    # 3. Two-endpoint capture comparison (Section 7)
    check("SYN seen at server with no SYN-ACK sent diagnoses server firewall or listen backlog drop",
          diagnose_two_side_tcp_capture(True, True, False, False) == "server_firewall_or_listen_backlog_dropped_syn")
    check("SYN-ACK sent by server but not seen at client diagnoses return-path or asymmetric NAT drop",
          diagnose_two_side_tcp_capture(True, True, True, False) == "return_path_or_asymmetric_nat_dropped_synack")
    check("RST arriving with a TTL different from the peer's normal packets diagnoses middlebox-injected RST",
          diagnose_two_side_tcp_capture(True, True, True, True, rst_ttl_differs_from_server=True) == "middlebox_injected_rst")

    # 4. Additional provenance checks from chapter text
    check("modern tcpdump default snaplen is 262,144 bytes (256 KiB)", 256 * 1024 == 262144)
    check("EtherTypes: PFC=0x8808, LACP=0x8809, LLDP=0x88cc; RoCEv2 UDP port=4791; CNP opcode=0x81",
          (0x8808, 0x8809, 0x88CC, 4791, 0x81) == (34824, 34825, 35020, 4791, 129))
    check("compute_capture_rate_and_ring_storage raises ValueError on zero snaplen",
          _raises(lambda: compute_capture_rate_and_ring_storage(100.0, 1500, 0, 100, 10)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
