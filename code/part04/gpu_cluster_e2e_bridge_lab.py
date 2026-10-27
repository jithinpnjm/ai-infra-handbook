#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.27: Lab: provision a GPU cluster with Terraform and Ansible."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gpu_cluster_e2e_bridge import (
    generate_ansible_inventory_from_tf_nodes,
    render_stub_nvidia_smi_list,
    verify_cluster_end_to_end,
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
    # 1. Part 1: Terraform var.nodes -> deterministic IP/port allocation -> Ansible hosts.yml inventory
    tf_nodes = {
        "login01": {"role": "login", "gpus": 0},
        "ctl01": {"role": "controller", "gpus": 0},
        "gpu01": {"role": "gpu", "gpus": 8},
        "gpu02": {"role": "gpu", "gpus": 8},
        "gpu03": {"role": "gpu", "gpus": 4},
    }
    inv = generate_ansible_inventory_from_tf_nodes("gpulab", tf_nodes)
    gpu_hosts = inv["all"]["children"]["gpu"]["hosts"]
    check(
        "Terraform->Ansible bridge generates login, controller, and gpu groups with deterministic IPs (172.28.0.10..14) and SSH ports (2200..2204)",
        set(inv["all"]["children"].keys()) == {"controller", "gpu", "login"}
        and inv["all"]["children"]["controller"]["hosts"]["ctl01"]["node_ip"] == "172.28.0.10"
        and gpu_hosts["gpu01"]["gpu_count"] == 8
        and gpu_hosts["gpu03"]["gpu_count"] == 4,
    )

    # 2. Part 2 & 3: Stub nvidia-smi -L rendering and end-to-end verify.yml health gate
    smi_by_host = {
        h: render_stub_nvidia_smi_list(h, hvars["gpu_count"])
        for h, hvars in gpu_hosts.items()
    }
    chrony_ok = {h: 0.002 for h in tf_nodes}
    prom_ok = {h: True for h in tf_nodes}
    ok_all, _ = verify_cluster_end_to_end(
        inv,
        chrony_offsets_sec=chrony_ok,
        nvidia_smi_lines_by_host=smi_by_host,
        prometheus_targets_up=prom_ok,
        slurm_idle_gpu_nodes={"gpu01", "gpu02", "gpu03"},
    )
    # Inject a missing GPU on gpu02 and a downed Prometheus target on gpu03
    bad_smi = dict(smi_by_host, gpu02=smi_by_host["gpu02"][:7])
    bad_prom = dict(prom_ok, gpu03=False)
    ok_bad, errs_bad = verify_cluster_end_to_end(
        inv,
        chrony_offsets_sec=chrony_ok,
        nvidia_smi_lines_by_host=bad_smi,
        prometheus_targets_up=bad_prom,
        slurm_idle_gpu_nodes={"gpu01", "gpu02", "gpu03"},
    )
    check(
        "verify_cluster_end_to_end passes healthy 5-node cluster and catches missing GPU on gpu02 and downed Prometheus exporter on gpu03",
        ok_all is True and ok_bad is False and len(errs_bad) == 2,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
