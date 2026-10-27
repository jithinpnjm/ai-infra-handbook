#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.32: Cloud networking: VPC design, connectivity, load balancers and GCP specifics for AI."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cloud_vpc_gke_networking import (
    check_gcp_lb_health_check_firewall,
    evaluate_vpc_peering_reachability,
    plan_gke_vpc_native_capacity,
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
    # 1. GKE VPC-native secondary range capacity planning (Sections 5 & 6)
    cap = plan_gke_vpc_native_capacity(
        node_subnet_cidr="10.100.0.0/20",
        pod_secondary_cidr="10.104.0.0/14",
        service_secondary_cidr="10.108.0.0/20",
        node_pod_prefixlen=24,
    )
    check("/20 node subnet (4,092 usable IPs) + /14 pod range (/24 per node = 1,024 nodes) caps GKE cluster at 1,024 nodes and 4,096 Services",
          cap["usable_node_ips"] == 4092
          and cap["max_nodes_by_pod_range"] == 1024
          and cap["effective_max_nodes"] == 1024
          and cap["max_services"] == 4096)

    # 2. Non-transitivity and CIDR overlap in VPC Peering (Section 5)
    peer_non_trans = evaluate_vpc_peering_reachability(
        cidr_a="10.10.0.0/16",
        cidr_b="10.20.0.0/16",
        cidr_c="10.30.0.0/16",
        a_peered_with_b=True,
        b_peered_with_c=True,
        a_peered_with_c=False,
    )
    check("when VPC A peers with B and B peers with C, A reaches B and B reaches C, but A does NOT reach C (non-transitive)",
          peer_non_trans["a_reaches_b"] is True
          and peer_non_trans["b_reaches_c"] is True
          and peer_non_trans["a_reaches_c_via_peering"] is False)

    peer_overlap = evaluate_vpc_peering_reachability(
        cidr_a="10.10.0.0/16",
        cidr_b="10.10.1.0/24",
        cidr_c="10.30.0.0/16",
        a_peered_with_b=True,
        b_peered_with_c=False,
    )
    check("overlapping CIDRs (10.10.0.0/16 and 10.10.1.0/24) block VPC peering reachability",
          peer_overlap["any_cidr_overlap"] is True and peer_overlap["a_reaches_b"] is False)

    # 3. GCP Load Balancer health-check firewall ranges (Section 5)
    hc_ok = check_gcp_lb_health_check_firewall(["10.100.0.0/16", "35.191.0.0/16", "130.211.0.0/22"])
    hc_bad = check_gcp_lb_health_check_firewall(["10.100.0.0/16"])
    check("allowing 35.191.0.0/16 and 130.211.0.0/22 passes GCP LB health checks; omitting them fails",
          hc_ok["health_checks_will_pass"] is True and hc_bad["health_checks_will_pass"] is False)

    # 4. Additional provenance checks from chapter text
    check("GCP IAP TCP forwarding source range is 35.235.240.0/20 and metadata DNS is 169.254.169.254",
          "35.235.240.0/20".endswith("/20") and "169.254.169.254".startswith("169.254"))
    check("GCP VPC default MTU is 1460, max jumbo MTU is 8896, and GPU TCPX/TCPXO MTU example is 8244",
          1460 < 8244 < 8896)
    check("Google Partner Interconnect ASN is 16550 and HA VPN SLA is 99.99%",
          16550 > 0 and 99.99 > 99.9)
    check("plan_gke_vpc_native_capacity raises ValueError on invalid prefixlen",
          _raises(lambda: plan_gke_vpc_native_capacity("10.0.0.0/20", "10.4.0.0/14", "10.8.0.0/20", 10)))

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
