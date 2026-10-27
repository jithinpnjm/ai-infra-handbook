"""Chapter 2.21 model: sshd_config hardening policy auditor, InfiniBand 16-bit
Partition Key (P_Key: 1-bit membership flag + 15-bit partition ID) isolation
evaluator, Kubernetes NetworkPolicy ingress/egress traffic evaluator, and fail2ban
sliding-window ban simulator.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapters 10 and 21 ("Security: A Broader Sweep": biometric identity conundrum,
  definitions, defense in depth, AAA RADIUS/TACACS+/802.1X, data protection, DoS
  and BGP NO_PEER / NO_ADVERTISE / RTBH mitigation, Colonel John Boyd's OODA loop).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapters 9
  and 10 (sshd_config hardening, host keys, fail2ban, nmap auditing).
- Josh Rosso et al., Production Kubernetes (PK), Chapters 7 and 8, and James
  Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapter 4
  (Kubernetes NetworkPolicy microsegmentation).
"""
from typing import Dict, List


def audit_sshd_config(config: Dict[str, str]) -> Dict[str, object]:
    """Audit sshd_config directives against production hardening baseline."""
    violations: List[str] = []
    if config.get("PermitRootLogin", "yes") not in {"no", "prohibit-password"}:
        violations.append("PermitRootLogin_must_be_no_or_prohibit_password")
    if config.get("PasswordAuthentication", "yes") != "no":
        violations.append("PasswordAuthentication_must_be_no")
    if config.get("AllowAgentForwarding", "yes") != "no":
        violations.append("AllowAgentForwarding_must_be_no")
    if config.get("X11Forwarding", "yes") != "no":
        violations.append("X11Forwarding_must_be_no")
    if int(config.get("MaxAuthTries", "6")) > 4:
        violations.append("MaxAuthTries_exceeds_4")
    return {"compliant": len(violations) == 0, "violations": violations}


def evaluate_ib_pkey_communication(pkey_a: int, pkey_b: int) -> Dict[str, object]:
    """Evaluate InfiniBand 16-bit P_Key isolation.
    Bit 15 (0x8000) is the membership bit (1 = full member, 0 = limited member).
    Bits 0..14 (0x7FFF) are the 15-bit Partition ID.
    Two ports communicate iff their 15-bit base Partition IDs match AND at least
    one of the two is a full member (limited-to-limited is blocked).
    """
    if not (0 <= pkey_a <= 0xFFFF) or not (0 <= pkey_b <= 0xFFFF):
        raise ValueError("P_Key must be a 16-bit integer (0..0xFFFF)")
    base_a = pkey_a & 0x7FFF
    base_b = pkey_b & 0x7FFF
    full_a = bool(pkey_a & 0x8000)
    full_b = bool(pkey_b & 0x8000)
    allowed = (base_a != 0) and (base_a == base_b) and (full_a or full_b)
    return {
        "base_pkey_a": hex(base_a),
        "base_pkey_b": hex(base_b),
        "full_member_a": full_a,
        "full_member_b": full_b,
        "communication_allowed": allowed,
    }


def evaluate_k8s_ingress_network_policy(
    default_deny_enabled: bool,
    allowed_Rules: List[Dict[str, object]],
    source_label_app: str,
    dst_port: int,
) -> bool:
    """Evaluate whether an incoming pod connection is permitted by Kubernetes NetworkPolicy."""
    for rule in allowed_Rules:
        if rule.get("from_app") == source_label_app and int(rule.get("port", -1)) == dst_port:
            return True
    return not default_deny_enabled


def simulate_fail2ban_window(
    failure_timestamps_sec: List[int],
    findtime_sec: int = 600,
    maxretry: int = 3,
) -> Dict[str, object]:
    """Determine if a sequence of auth failure timestamps triggers a fail2ban ban."""
    if findtime_sec <= 0 or maxretry <= 0:
        raise ValueError("findtime_sec and maxretry must be positive")
    sorted_ts = sorted(failure_timestamps_sec)
    for i in range(len(sorted_ts)):
        window_start = sorted_ts[i]
        count = sum(1 for t in sorted_ts[i:] if t - window_start <= findtime_sec)
        if count >= maxretry:
            return {"banned": True, "trigger_timestamp": sorted_ts[i + maxretry - 1]}
    return {"banned": False, "trigger_timestamp": None}
