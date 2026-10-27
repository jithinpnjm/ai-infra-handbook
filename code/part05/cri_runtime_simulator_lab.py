#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.2: Container runtimes: containerd, runc, CRI and OCI."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cri_runtime_simulator import (
    CRIRuntimeSimulator,
    validate_cgroup_and_runtime_class,
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
    # 1. Section 1 & 2: CRI RunPodSandbox -> CreateContainer -> StartContainer & shim survival across containerd restart
    sim = CRIRuntimeSimulator(configured_runtimes={"runc", "nvidia", "kata"})
    sb = sim.run_pod_sandbox("uid1", "gpu-train-0", runtime_handler="nvidia", cni_ok=True)
    c1 = sim.create_and_start_container(sb, "trainer", "nvcr.io/nvidia/pytorch:24.06-py3")
    after_restart = sim.restart_containerd_daemon()
    cni_failed = False
    try:
        sim.run_pod_sandbox("uid2", "bad-cni-pod", cni_ok=False)
    except RuntimeError:
        cni_failed = True
    check(
        "CRIRuntimeSimulator creates pause sandbox + trainer container, keeps container running across containerd restart (via shim), and catches CNI error",
        sim.containers[c1]["state"] == "TASK_RUNNING"
        and after_restart["running_containers"] == 1
        and cni_failed is True,
    )

    # 2. Section 2, 4, 7: Kubelet vs containerd SystemdCgroup match and RuntimeClass overhead accounting
    ok_cfg, _, eff = validate_cgroup_and_runtime_class(
        kubelet_cgroup_driver="systemd",
        containerd_systemd_cgroup=True,
        runtime_class_handler="nvidia",
        containerd_runtimes={"runc": "io.containerd.runc.v2", "nvidia": "io.containerd.runc.v2"},
        pod_cpu_request_m=8000,
        pod_mem_request_mi=32768,
        overhead_cpu_m=100,
        overhead_mem_mi=64,
    )
    bad_cfg, errs, _ = validate_cgroup_and_runtime_class(
        kubelet_cgroup_driver="systemd",
        containerd_systemd_cgroup=False,
        runtime_class_handler="missing_handler",
        containerd_runtimes={"runc": "io.containerd.runc.v2"},
        pod_cpu_request_m=1000,
        pod_mem_request_mi=1024,
    )
    check(
        "validate_cgroup_and_runtime_class adds RuntimeClass overhead (8100m CPU, 32832Mi RAM) and catches SystemdCgroup mismatch + missing handler",
        ok_cfg is True
        and eff == {"effective_cpu_m": 8100, "effective_mem_mi": 32832}
        and bad_cfg is False
        and len(errs) == 2,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
