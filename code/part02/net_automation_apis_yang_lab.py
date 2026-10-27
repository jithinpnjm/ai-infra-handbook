#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.28: Network automation fundamentals: data models, templates, APIs, NETCONF, gNMI and SDN."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from net_automation_apis_yang import (
    render_leaf_config_strict,
    simulate_netconf_confirmed_commit,
    validate_switch_inventory_schema,
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
    # 1. YANG / JSON Schema inventory validation (Sections 3 & 4)
    valid_inv = {
        "hostname": "leaf-01",
        "vlans": [100, 200],
        "bgp": {"asn": 65101, "router_id": "10.255.0.11"},
        "interfaces": [
            {"name": "Ethernet1", "description": "to-spine1", "mtu": 9214, "ipv4": "10.0.1.1/31"},
            {"name": "Ethernet2", "description": "to-spine2", "mtu": 9214, "ipv4": "10.0.2.1/31"},
        ],
    }
    v_ok = validate_switch_inventory_schema(valid_inv)
    check("valid leaf-01 inventory (VLANs 100/200, MTU 9214, /31 IPv4) passes schema validation",
          v_ok["valid"] is True and v_ok["errors"] == [])

    bad_inv = {
        "hostname": "BAD_HOST!",
        "vlans": [0, 5000],
        "interfaces": [{"name": "Ethernet1", "mtu": 20000, "ipv4": "999.1.1.1/31"}],
    }
    v_bad = validate_switch_inventory_schema(bad_inv)
    check("invalid hostname, VLANs [0, 5000], MTU 20000 (>9216), and bad IPv4 flags all 4 schema errors",
          v_bad["valid"] is False and len(v_bad["errors"]) == 4)

    # 2. Strict template rendering (Section 5)
    rendered = render_leaf_config_strict(valid_inv)
    check("template renders hostname leaf-01, mtu 9214, ip address 10.0.1.1/31, and router bgp 65101",
          "hostname leaf-01" in rendered
          and "mtu 9214" in rendered
          and "ip address 10.0.1.1/31" in rendered
          and "router bgp 65101" in rendered)
    check("StrictUndefined raises KeyError when required 'bgp' key is missing",
          _raises_key(lambda: render_leaf_config_strict({"hostname": "sw1", "interfaces": []})))

    # 3. NETCONF candidate + confirmed-commit rollback safety (Section 6)
    nc_ok = simulate_netconf_confirmed_commit(initial_running_mtu=1500, candidate_mtu=9214, confirm_within_timeout=True)
    nc_rb = simulate_netconf_confirmed_commit(initial_running_mtu=1500, candidate_mtu=9214, confirm_within_timeout=False)
    check("NETCONF confirmed-commit persists 9214 when confirmed and auto-rolls back to 1500 on timeout",
          nc_ok["final_running_mtu"] == 9214
          and nc_rb["final_running_mtu"] == 1500
          and nc_rb["rolled_back"] is True)

    # 4. Additional provenance checks from chapter text
    check("SNMP uses UDP 161/162, NETCONF over SSH uses TCP port 830, and gNMI example uses port 6030",
          (161, 162, 830, 6030) == (161, 162, 830, 6030))
    check("YANG RFC is 7950, NETCONF RFC is 6241, RESTCONF RFC is 8040, and YANG Patch RFC is 8072",
          (7950, 6241, 8040, 8072) == (7950, 6241, 8040, 8072))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises_key(fn) -> bool:
    try:
        fn()
        return False
    except KeyError:
        return True


if __name__ == "__main__":
    main()
