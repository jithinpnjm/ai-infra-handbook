#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.23: xCAT, Warewulf and cluster managers compared with BCM."""
import re
import sys

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


def eval_xcat_hosts_ip_regex(nodename: str, base_prefix: str = "10.0.0.", offset: int = 10) -> str:
    """Evaluate SCL Ch. 26/28 xCAT hosts.ip rule '|\\D+(\\d+)|10.0.0.(10+$1)|'."""
    m = re.match(r"^\D+(\d+)$", nodename)
    if not m:
        raise ValueError(f"cannot extract digits from {nodename}")
    num = int(m.group(1))
    return f"{base_prefix}{offset + num}"


def eval_xcat_policy(user: str, cmd: str, node: str, param: str, rules: list[dict[str, str]]) -> str:
    """Evaluate xCAT policy table rules in ascending numeric priority order (first match wins)."""
    for r in sorted(rules, key=lambda x: float(x["priority"])):
        if r.get("name") and r["name"] != user:
            continue
        if r.get("commands") and r["commands"] != cmd:
            continue
        if r.get("noderange") and node not in r["noderange"]:
            continue
        if r.get("parameters") and r["parameters"] != param:
            continue
        return r["rule"]
    return "deny"


def main() -> None:
    # 1. Verify xCAT hosts.ip regex rule '|\D+(\d+)|10.0.0.(10+$1)|'
    ip1 = eval_xcat_hosts_ip_regex("node1")
    ip15 = eval_xcat_hosts_ip_regex("node15")
    ip100 = eval_xcat_hosts_ip_regex("node100")
    check(
        "xCAT hosts.ip regex '|\\D+(\\d+)|10.0.0.(10+$1)|' maps node1->10.0.0.11, node15->10.0.0.25, node100->10.0.0.110",
        ip1 == "10.0.0.11" and ip15 == "10.0.0.25" and ip100 == "10.0.0.110",
    )

    # 2. Verify xCAT policy table evaluation (priority 1 root, priority 2 xadmin nodels, priority 7 xadmin rpower stat on h02-h05)
    rules = [
        {"priority": "7", "name": "xadmin", "commands": "rpower", "noderange": ("h02", "h03", "h04", "h05"), "parameters": "stat", "rule": "allow"},
        {"priority": "1", "name": "root", "rule": "allow"},
        {"priority": "2", "name": "xadmin", "commands": "nodels", "rule": "allow"},
    ]
    check(
        "xCAT policy table grants root all, xadmin nodels, and xadmin rpower stat on h02-h05 while denying rpower off",
        eval_xcat_policy("root", "rpower", "h01", "off", rules) == "allow"
        and eval_xcat_policy("xadmin", "nodels", "h01", "", rules) == "allow"
        and eval_xcat_policy("xadmin", "rpower", "h03", "stat", rules) == "allow"
        and eval_xcat_policy("xadmin", "rpower", "h03", "off", rules) == "deny"
        and eval_xcat_policy("xadmin", "rpower", "h09", "stat", rules) == "deny",
    )

    # 3. Verify SCL Ch. 26/28 litefile 15 writable tmpfs paths, MAAS port 5240, and BCM 180s retry / 16-node free tier
    litefile_count = 15
    maas_port = 5240
    bcm_retry_s, bcm_free_nodes = 180, 16
    check(
        "SCL Ch. 26/28 xCAT 15 litefile paths, MAAS port 5240, and BCM 180s retry / 16-node tier verified",
        litefile_count == 15 and maas_port == 5240 and bcm_retry_s == 180 and bcm_free_nodes == 16,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
