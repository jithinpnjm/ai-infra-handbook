#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.4: Bare-metal Kubernetes from scratch with kubeadm (lab)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kubeadm_bootstrap_validator import (
    KUBEADM_INIT_PHASES,
    validate_node_preflight_and_cidrs,
    verify_kubeadm_join_credentials,
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
    # 1. Section 1, 2, 3, 4: Node preflight and CIDR non-overlap checks
    good_node = {
        "swap_enabled": False,
        "loaded_modules": ["overlay", "br_netfilter"],
        "sysctls": {"net.bridge.bridge-nf-call-iptables": 1, "net.ipv4.ip_forward": 1},
        "kubelet_cgroup_driver": "systemd",
        "containerd_systemd_cgroup": True,
        "node_cidr": "10.0.0.0/24",
        "pod_subnet": "10.244.0.0/16",
        "service_subnet": "10.96.0.0/12",
        "cni_pool_cidr": "10.244.0.0/16",
    }
    bad_node = {
        "swap_enabled": True,
        "loaded_modules": ["overlay"],
        "sysctls": {"net.bridge.bridge-nf-call-iptables": 0, "net.ipv4.ip_forward": 1},
        "kubelet_cgroup_driver": "systemd",
        "containerd_systemd_cgroup": False,
        "node_cidr": "10.244.1.0/24",  # overlaps pod_subnet!
        "pod_subnet": "10.244.0.0/16",
        "service_subnet": "10.96.0.0/12",
        "cni_pool_cidr": "192.168.0.0/16",  # mismatches pod_subnet!
    }
    ok_good, _ = validate_node_preflight_and_cidrs(good_node)
    ok_bad, errs_bad = validate_node_preflight_and_cidrs(bad_node)
    check(
        "validate_node_preflight_and_cidrs passes compliant node and flags swap, missing br_netfilter, sysctl=0, cgroup mismatch, CIDR overlap, and CNI mismatch",
        ok_good is True and ok_bad is False and len(errs_bad) == 6,
    )

    # 2. Section 3, 5, 7: kubeadm init phases and kubeadm join token + CA hash + 2-hour upload-certs check
    ca_hex = "a" * 64
    ok_join, _ = verify_kubeadm_join_credentials(
        "abcdef.0123456789abcdef",
        f"sha256:{ca_hex}",
        ca_hex,
        is_control_plane_join=True,
        certificate_key_age_minutes=30,
    )
    bad_join, errs_join = verify_kubeadm_join_credentials(
        "bad-token",
        f"sha256:{'b' * 64}",
        ca_hex,
        is_control_plane_join=True,
        certificate_key_age_minutes=150,
    )
    check(
        "verify_kubeadm_join_credentials validates 11 init phases, accepts valid token+CA hash, and flags bad token, rogue CA hash, and expired (>120m) upload-certs key",
        len(KUBEADM_INIT_PHASES) == 11
        and ok_join is True
        and bad_join is False
        and len(errs_join) == 3,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
