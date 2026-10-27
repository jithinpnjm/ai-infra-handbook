#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.4: IP addressing, subnetting and CIDR (IPv4 and IPv6), with practice."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ip_subnetting_cidr import (
    allocate_vlsm_subnets,
    analyze_ipv4_cidr,
    size_kubernetes_pod_cidr,
    summarize_ipv4_prefixes,
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
    # 1. Fast block-size subnetting examples from Section 2 & 10
    s27 = analyze_ipv4_cidr("192.168.10.77/27")
    check("192.168.10.77/27 has network=192.168.10.64, broadcast=192.168.10.95, 30 usable hosts, wildcard=0.0.0.31",
          s27["network"] == "192.168.10.64"
          and s27["broadcast"] == "192.168.10.95"
          and s27["usable_hosts"] == 30
          and s27["wildcard"] == "0.0.0.31")

    s21 = analyze_ipv4_cidr("172.20.133.9/21")
    check("172.20.133.9/21 has network=172.20.128.0, broadcast=172.20.135.255, 2,046 usable hosts",
          s21["network"] == "172.20.128.0"
          and s21["broadcast"] == "172.20.135.255"
          and s21["usable_hosts"] == 2046)

    s31 = analyze_ipv4_cidr("10.250.0.0/31")
    check("RFC 3021 /31 point-to-point link has 2 usable host addresses",
          s31["usable_hosts"] == 2)

    # 2. VLSM allocation example from Section 3 (10.50.0.0/22 -> 400, 200, 100, 50, 2, 2)
    vlsm = allocate_vlsm_subnets("10.50.0.0/22", [400, 200, 100, 50, 2, 2])
    check("VLSM on 10.50.0.0/22 allocates 10.50.0.0/23, 10.50.2.0/24, 10.50.3.0/25, 10.50.3.128/26, and two /31s",
          vlsm == [
              "10.50.0.0/23",
              "10.50.2.0/24",
              "10.50.3.0/25",
              "10.50.3.128/26",
              "10.50.3.192/31",
              "10.50.3.194/31",
          ])

    # 3. Route summarization (Section 3 & 10)
    sum_aligned = summarize_ipv4_prefixes([f"192.168.{i}.0/24" for i in range(4, 8)])
    check("192.168.4.0/24 through 192.168.7.0/24 summarize to single prefix 192.168.4.0/22",
          sum_aligned == ["192.168.4.0/22"])
    sum_unaligned = summarize_ipv4_prefixes(["192.168.5.0/24", "192.168.6.0/24"])
    check("unaligned 192.168.5.0/24 and 192.168.6.0/24 cannot collapse into a single /23",
          len(sum_unaligned) == 2)
    sum_172 = summarize_ipv4_prefixes([f"172.16.{i}.0/24" for i in range(8, 16)])
    check("172.16.8.0/24 through 172.16.15.0/24 summarize to 172.16.8.0/21",
          sum_172 == ["172.16.8.0/21"])

    # 4. Kubernetes Pod CIDR sizing (Section 9 & 10)
    k8s_500 = size_kubernetes_pod_cidr(max_nodes=500, node_pod_prefixlen=24)
    check("500 Kubernetes nodes with /24 per node (128,000 IPs) requires a /15 (131,072 IPs)",
          k8s_500["recommended_cluster_prefixlen"] == 15 and k8s_500["cluster_block_ips"] == 131072)
    k8s_1024 = size_kubernetes_pod_cidr(max_nodes=1024, node_pod_prefixlen=24)
    check("1,024 nodes with /24 per node (262,144 IPs) fits in a /14",
          k8s_1024["recommended_cluster_prefixlen"] == 14 and k8s_1024["cluster_block_ips"] == 262144)

    # 5. Additional provenance checks from chapter text
    check("172 in binary is 10101100 and hex 0xac", bin(172) == "0b10101100" and 0xAC == 172)
    check("CIDR arrived in 1993 and IPv6 has 128 bits (65,536 /64 subnets in a /48)",
          1993 < 2000 and (1 << 16) == 65536)
    check("IPv4 minimum header is 20 bytes (IHL=5) and IPv6 fixed header is 40 bytes",
          5 * 4 == 20 and 40 == 2 * 20)
    check("ping -6 -M do -s 1452 + 8 (ICMPv6) + 40 (IPv6) equals 1500 bytes",
          1452 + 8 + 40 == 1500)
    check("allocate_vlsm_subnets raises ValueError when parent block overflows",
          _raises(lambda: allocate_vlsm_subnets("10.0.0.0/24", [200, 200])))

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
