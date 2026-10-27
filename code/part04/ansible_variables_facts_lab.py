#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.7: Ansible variables, facts, templates and filters."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_variables_facts import (
    dict2items_and_items2dict_roundtrip,
    parse_local_fact_file,
    project_group_hostvars,
    render_haproxy_backend_from_groups,
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
    # 1. AUR Ch. 5 Example 5-10 & Section 3: INI and JSON /etc/ansible/facts.d/*.fact -> ansible_local
    ini_fact = parse_local_fact_file(
        "/etc/ansible/facts.d/example.fact",
        "[book]\ntitle=Ansible: Up and Running\nauthors=Meijer, Hochstein, Moser\npublisher=O'Reilly\n",
    )
    json_fact = parse_local_fact_file("/etc/ansible/facts.d/gpu.fact", '{"count": 8, "model": "H100"}')
    check(
        "parse_local_fact_file maps INI example.fact to ansible_local.example.book.title and JSON gpu.fact to count=8",
        ini_fact["example"]["book"]["title"] == "Ansible: Up and Running"
        and ini_fact["example"]["book"]["publisher"] == "O'Reilly"
        and json_fact["gpu"]["count"] == 8,
    )

    # 2. AUR Ch. 5 & Section 3/6: Cross-host `groups` + `hostvars` projection (`extract`) and HAProxy template
    groups = {"web": ["georgia.example.com", "newhampshire.example.com", "newjersey.example.com"]}
    hostvars = {
        "georgia.example.com": {"ansible_default_ipv4": {"address": "203.0.113.15"}, "rack": "r01"},
        "newhampshire.example.com": {"ansible_default_ipv4": {"address": "203.0.113.25"}, "rack": "r01"},
        "newjersey.example.com": {"ansible_default_ipv4": {"address": "203.0.113.38"}, "rack": "r02"},
    }
    haproxy_cfg = render_haproxy_backend_from_groups(groups, hostvars, "web", port=80)
    racks = sorted(set(project_group_hostvars(groups, hostvars, "web", "rack")))
    missing_raised = False
    try:
        project_group_hostvars(groups, {"georgia.example.com": {}}, "web", "rack")
    except KeyError:
        missing_raised = True
    check(
        "render_haproxy_backend_from_groups renders all 3 web servers, extract projects unique racks ['r01', 'r02'], and missing facts raise",
        "server georgia.example.com 203.0.113.15:80" in haproxy_cfg
        and "server newjersey.example.com 203.0.113.38:80" in haproxy_cfg
        and racks == ["r01", "r02"]
        and missing_raised is True,
    )

    # 3. Section 5 & 6: dict2items and items2dict round-trip
    sysctls = {"vm.swappiness": 1, "kernel.numa_balancing": 0}
    items, rt = dict2items_and_items2dict_roundtrip(sysctls)
    check(
        "dict2items converts dict to [{'key': ..., 'value': ...}] list and items2dict reconstructs the dict",
        items == [{"key": "vm.swappiness", "value": 1}, {"key": "kernel.numa_balancing", "value": 0}]
        and rt == sysctls,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
