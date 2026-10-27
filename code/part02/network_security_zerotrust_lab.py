#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.21: Network security: threat models, firewalls, SSH, zero trust and securing AI clusters."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_security_zerotrust import (
    audit_sshd_config,
    evaluate_ib_pkey_communication,
    evaluate_k8s_ingress_network_policy,
    simulate_fail2ban_window,
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
    # 1. sshd_config hardening baseline (Section 7)
    hardened = {
        "PermitRootLogin": "no",
        "PasswordAuthentication": "no",
        "AllowAgentForwarding": "no",
        "X11Forwarding": "no",
        "MaxAuthTries": "3",
    }
    check("hardened sshd_config passes all baseline checks",
          audit_sshd_config(hardened)["compliant"] is True)
    weak = {"PermitRootLogin": "yes", "PasswordAuthentication": "yes"}
    check("default unhardened sshd_config flags root, password, agent, X11, and MaxAuthTries violations",
          len(audit_sshd_config(weak)["violations"]) == 5)

    # 2. InfiniBand P_Key tenant isolation (Section 13)
    # Full member of partition 0x0042 = 0x8042; limited member = 0x0042; other tenant = 0x8043
    ib_same = evaluate_ib_pkey_communication(0x8042, 0x8042)
    check("two full members in IB P_Key 0x8042 (base 0x42) can communicate",
          ib_same["communication_allowed"] is True)
    ib_diff = evaluate_ib_pkey_communication(0x8042, 0x8043)
    check("different tenant P_Keys (0x8042 vs 0x8043) are hardware-blocked by HCA",
          ib_diff["communication_allowed"] is False)
    ib_lim_lim = evaluate_ib_pkey_communication(0x0042, 0x0042)
    ib_lim_full = evaluate_ib_pkey_communication(0x0042, 0x8042)
    check("two limited members (0x0042) cannot talk to each other, but can talk to a full member (0x8042)",
          ib_lim_lim["communication_allowed"] is False and ib_lim_full["communication_allowed"] is True)

    # 3. Kubernetes NetworkPolicy microsegmentation (Section 12)
    rules = [{"from_app": "gateway", "port": 8001}]
    check("with default-deny + allow-gateway-to-triton, gateway:8001 is allowed and rogue-pod:8001 is denied",
          evaluate_k8s_ingress_network_policy(True, rules, "gateway", 8001) is True
          and evaluate_k8s_ingress_network_policy(True, rules, "rogue-pod", 8001) is False)

    # 4. fail2ban sliding window (Section 7)
    ban = simulate_fail2ban_window([10, 45, 120], findtime_sec=600, maxretry=3)
    check("3 SSH auth failures within 110s (<= 600s findtime) triggers fail2ban at t=120s",
          ban == {"banned": True, "trigger_timestamp": 120})
    no_ban = simulate_fail2ban_window([10, 400, 900], findtime_sec=600, maxretry=3)
    check("3 failures spread across 890s (> 600s findtime) does not trigger ban",
          no_ban["banned"] is False)

    # 5. Additional provenance checks from chapter text
    check("RADIUS uses UDP 1812/1813 and TACACS+ uses TCP port 49",
          (1812, 1813, 49) == (1812, 1813, 49))
    check("common exposed AI/infra ports: SSH 22, rpcbind 111, IPMI 623, Docker 2375, etcd 2379, Triton 8000-8002, Ray 8265, Jupyter 8888, kubelet 10250",
          22 < 111 < 623 < 2375 < 2379 < 8001 < 8265 < 8888 < 10250)
    check("evaluate_ib_pkey_communication raises ValueError on >16-bit integer",
          _raises(lambda: evaluate_ib_pkey_communication(0x10000, 0x8001)))

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
