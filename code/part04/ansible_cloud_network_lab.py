#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.16: Ansible for containers, cloud and network devices."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_cloud_network import (
    apply_vlan_resource_module,
    select_latest_ami,
    verify_lldp_against_cabling_plan,
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
    # 1. Section 3 & NPA Ch. 12: Network resource module states (merged vs overridden vs deleted vs rendered)
    running = {10: "mgmt", 99: "legacy_unused"}
    desired = [{"vlan_id": 10, "name": "mgmt"}, {"vlan_id": 20, "name": "roce_storage"}]
    r_merged = apply_vlan_resource_module(running, desired, state="merged")
    r_overridden = apply_vlan_resource_module(running, desired, state="overridden")
    r_rendered = apply_vlan_resource_module({}, desired, state="rendered")
    check(
        "VLAN resource module keeps vlan 99 in 'merged', prunes vlan 99 in 'overridden', and generates offline CLI in 'rendered'",
        r_merged["after"] == {10: "mgmt", 20: "roce_storage", 99: "legacy_unused"}
        and r_overridden["after"] == {10: "mgmt", 20: "roce_storage"}
        and "no vlan 99" in r_overridden["commands"]
        and len(r_rendered["rendered"]) == 2,
    )

    # 2. Section 3: LLDP topology vs cabling-plan verifier (detects swapped spine port)
    plan = {
        ("leaf01", "swp49"): ("spine01", "swp1"),
        ("leaf01", "swp50"): ("spine02", "swp1"),
    }
    good_lldp = dict(plan)
    swapped_lldp = {
        ("leaf01", "swp49"): ("spine01", "swp2"),  # wrong port on spine01!
    }
    errs = verify_lldp_against_cabling_plan(plan, swapped_lldp)
    check(
        "verify_lldp_against_cabling_plan passes when LLDP matches plan and flags swapped/missing links",
        verify_lldp_against_cabling_plan(plan, good_lldp) == []
        and len(errs) == 2
        and "cabling mismatch on leaf01:swp49" in errs[0]
        and "missing LLDP neighbor on leaf01:swp50" in errs[1],
    )

    # 3. AUR Ch. 17 Example 17-9: Select latest Ubuntu AMI by creation_date
    amis = [
        {"image_id": "ami-old", "creation_date": "2024-01-10T00:00:00.000Z"},
        {"image_id": "ami-newest", "creation_date": "2024-06-15T12:00:00.000Z"},
        {"image_id": "ami-mid", "creation_date": "2024-03-01T00:00:00.000Z"},
    ]
    check(
        "select_latest_ami picks 'ami-newest' via sort(attribute='creation_date') | last",
        select_latest_ami(amis)["image_id"] == "ami-newest",
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
