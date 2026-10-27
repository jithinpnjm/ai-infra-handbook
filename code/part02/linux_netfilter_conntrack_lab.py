#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.23: Linux networking II: netfilter, nftables, conntrack and NAT."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from linux_netfilter_conntrack import (
    classify_conntrack_packet_state,
    size_conntrack_table,
    trace_netfilter_hooks,
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
    # 1. Netfilter 5-hook traversal paths (Section 1, NK Ch. 2)
    check("external -> local traverses ['prerouting', 'input']",
          trace_netfilter_hooks("external_to_local") == ["prerouting", "input"])
    check("local -> external traverses ['output', 'postrouting']",
          trace_netfilter_hooks("local_to_external") == ["output", "postrouting"])
    check("forwarded packet traverses ['prerouting', 'forward', 'postrouting']",
          trace_netfilter_hooks("external_to_external_forwarded") == ["prerouting", "forward", "postrouting"])
    check("local -> local (loopback) traverses ['output', 'postrouting', 'prerouting', 'input']",
          trace_netfilter_hooks("local_to_local_loopback") == ["output", "postrouting", "prerouting", "input"])

    # 2. nf_conntrack table sizing and hashsize (Section 2)
    ct_size = size_conntrack_table(nf_conntrack_max=2097152, bucket_ratio=8, bytes_per_entry=352)
    check("nf_conntrack_max=2,097,152 with ratio 8 recommends hashsize=262,144 buckets (~708.0 MiB RAM)",
          ct_size["recommended_hashsize_buckets"] == 262144 and 600.0 <= ct_size["estimated_ram_mib"] <= 800.0)

    # 3. Conntrack packet state classification (Section 2)
    check("raw NOTRACK rule sets state to UNTRACKED",
          classify_conntrack_packet_state(True, False, False, True) == "UNTRACKED")
    check("ICMP fragmentation-needed error for an active flow is classified as RELATED",
          classify_conntrack_packet_state(False, False, False, False, True) == "RELATED")
    check("bidirectional tracked flow is classified as ESTABLISHED",
          classify_conntrack_packet_state(False, True, True, False) == "ESTABLISHED")
    check("unsolicited mid-stream ACK with no conntrack entry (asymmetric routing) is classified as INVALID",
          classify_conntrack_packet_state(False, False, False, False) == "INVALID")

    # 4. Additional provenance checks from chapter text
    check("default Linux nf_conntrack_tcp_timeout_established is 5 days = 432,000 seconds (tuned to 3600s)",
          5 * 86400 == 432000 and 3600 < 432000)
    check("nftables trace chain priority example is -300 (runs before raw/conntrack)",
          -300 < 0)
    check("node_exporter port is 9100, dcgm-exporter is 9400, and RoCEv2 UDP port is 4791",
          (9100, 9400, 4791) == (9100, 9400, 4791))
    check("trace_netfilter_hooks raises ValueError on unknown flow type",
          _raises(lambda: trace_netfilter_hooks("invalid_type")))

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
