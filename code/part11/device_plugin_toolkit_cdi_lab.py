"""Chapter 11.2 Lab — Device plugin, container toolkit, CDI and runtime classes.

Run with:
    python3 code/part11/device_plugin_toolkit_cdi_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from device_plugin_toolkit_cdi import (
    KubeletDevicePluginState,
    MissingGpuTriageCase,
    compute_underspecified_placement_risk,
    generate_cdi_spec,
    triage_gpu_node_or_pod,
    validate_extended_resource_spec,
)


def _check(condition: bool, label: str, passed: list[str], failed: list[str]) -> None:
    if condition:
        passed.append(label)
        print(f"  [PASS] {label}")
    else:
        failed.append(label)
        print(f"  [ERR]  {label}")


def main() -> int:
    passed: list[str] = []
    failed: list[str] = []

    print("=== Chapter 11.2 Lab: Device Plugin, Container Toolkit, CDI & RuntimeClass ===")

    # 1. CDI Specification Generation (`cdiVersion: 0.5.0`, `kind: nvidia.com/gpu`)
    uuids = [f"GPU-3a1e9f2b-000{i}" for i in range(8)]
    cdi = generate_cdi_spec(uuids, uvm_major=238)
    _check(cdi.cdi_version == "0.5.0", "CDI version is 0.5.0", passed, failed)
    _check(cdi.kind == "nvidia.com/gpu", "CDI kind is nvidia.com/gpu", passed, failed)
    _check(len(cdi.devices) == 8, "CDI spec contains 8 GPU device entries", passed, failed)
    dev0 = cdi.devices[0]
    _check(dev0.name == "0", "First CDI device entry is named '0'", passed, failed)
    _check(
        dev0.device_nodes[0].path == "/dev/nvidia0"
        and dev0.device_nodes[0].major == 195
        and dev0.device_nodes[0].minor == 0,
        "GPU 0 node is /dev/nvidia0 (char 195:0)",
        passed,
        failed,
    )
    _check(
        dev0.device_nodes[1].path == "/dev/nvidiactl"
        and dev0.device_nodes[1].major == 195
        and dev0.device_nodes[1].minor == 255,
        "Control node is /dev/nvidiactl (char 195:255)",
        passed,
        failed,
    )
    _check(
        dev0.device_nodes[2].path == "/dev/nvidia-uvm"
        and dev0.device_nodes[2].major == 238
        and dev0.device_nodes[2].minor == 0,
        "UVM node is /dev/nvidia-uvm (char 238:0)",
        passed,
        failed,
    )
    _check(
        any(m.host_path.endswith("libcuda.so.1") for m in dev0.mounts)
        and any(m.host_path.endswith("nvidia-smi") for m in dev0.mounts),
        "CDI mounts include host libcuda.so.1 and nvidia-smi with ro bind options",
        passed,
        failed,
    )

    # 2. Kubelet <-> Device Plugin gRPC Contract (Capacity, Allocatable, Allocated)
    node = KubeletDevicePluginState(node_name="gpu-node-07")
    pre_status = node.node_status()
    _check(
        pre_status["capacity"] is None and pre_status["allocatable"] is None,
        "Before first registration, Capacity and Allocatable are both absent (None)",
        passed,
        failed,
    )

    node.register(uuids)
    healthy_status = node.node_status()
    _check(
        healthy_status["capacity"] == 8 and healthy_status["allocatable"] == 8,
        "After Register() + ListAndWatch(), Capacity=8 and Allocatable=8",
        passed,
        failed,
    )

    # Allocate 6 GPUs (as in gpu-node-07 example: 6 allocated, 2 free)
    alloc_resp = node.allocate(6, strategy="cdi-annotations")
    after_alloc = node.node_status()
    _check(
        after_alloc["allocated"] == 6 and after_alloc["free_schedulable"] == 2,
        "After allocating 6 GPUs, Allocated=6 and free schedulable=2 while Allocatable=8",
        passed,
        failed,
    )
    _check(
        alloc_resp["cdi_devices"] == [f"nvidia.com/gpu={i}" for i in range(6)],
        "CDI Allocate() response returns fully qualified nvidia.com/gpu=0..5 names",
        passed,
        failed,
    )

    # Mark 3 devices unhealthy on a fresh node: Capacity stays 8, Allocatable drops to 5
    node_degraded = KubeletDevicePluginState(node_name="gpu-node-08")
    node_degraded.register(uuids)
    for bad_uuid in uuids[:3]:
        node_degraded.mark_unhealthy(bad_uuid)
    deg_status = node_degraded.node_status()
    _check(
        deg_status["capacity"] == 8 and deg_status["allocatable"] == 5,
        "When 3 of 8 GPUs turn Unhealthy, Capacity stays 8 while Allocatable drops to 5",
        passed,
        failed,
    )

    # Drop stream (plugin crash after registration): Capacity=8 survives, Allocatable=None
    node_crashed = KubeletDevicePluginState(node_name="gpu-node-11")
    node_crashed.register(uuids)
    node_crashed.drop_stream()
    crash_status = node_crashed.node_status()
    _check(
        crash_status["capacity"] == 8 and crash_status["allocatable"] is None,
        "When plugin crashes after registration, historical Capacity=8 survives while Allocatable is absent",
        passed,
        failed,
    )

    # Legacy env var allocation strategy
    node_legacy = KubeletDevicePluginState(node_name="gpu-node-legacy")
    node_legacy.register(uuids)
    legacy_resp = node_legacy.allocate(1, strategy="envvar")
    _check(
        legacy_resp["env"] == {"NVIDIA_VISIBLE_DEVICES": "GPU-3a1e9f2b-0000"},
        "Envvar Allocate() response sets NVIDIA_VISIBLE_DEVICES to allocated UUID",
        passed,
        failed,
    )

    # 3. Extended Resource Validation Rules
    ok_limits_only, _ = validate_extended_resource_spec(None, {"nvidia.com/gpu": 1})
    ok_matching, _ = validate_extended_resource_spec(
        {"nvidia.com/gpu": 4}, {"nvidia.com/gpu": 4}
    )
    bad_req_only, _ = validate_extended_resource_spec({"nvidia.com/gpu": 1}, None)
    bad_mismatch, _ = validate_extended_resource_spec(
        {"nvidia.com/gpu": 1}, {"nvidia.com/gpu": 2}
    )
    _check(
        ok_limits_only and ok_matching,
        "Extended resource spec accepts limits-only (1) and matching requests/limits (4)",
        passed,
        failed,
    )
    _check(
        (not bad_req_only) and (not bad_mismatch),
        "Extended resource spec rejects requests-without-limits and mismatched requests/limits",
        passed,
        failed,
    )

    # 4. Underspecified Placement Risk (40 nodes: 25 NVLink + 15 older PCIe = 37.5%)
    risk_no_affinity = compute_underspecified_placement_risk(
        total_nodes=40,
        qualified_nvlink_nodes=25,
        older_pcie_nodes=15,
        has_required_affinity=False,
    )
    risk_with_affinity = compute_underspecified_placement_risk(
        total_nodes=40,
        qualified_nvlink_nodes=25,
        older_pcie_nodes=15,
        has_required_affinity=True,
    )
    _check(
        risk_no_affinity["wrong_pool_probability_pct"] == 37.5
        and risk_no_affinity["eligible_nodes"] == 40.0,
        "Bare nvidia.com/gpu request on 40-node mixed fleet has 37.5% (15/40) wrong-pool risk",
        passed,
        failed,
    )
    _check(
        risk_with_affinity["wrong_pool_probability_pct"] == 0.0
        and risk_with_affinity["eligible_nodes"] == 25.0,
        "Required nodeAffinity restricts scheduling to the 25 qualified NVLink nodes (0.0% wrong-pool risk)",
        passed,
        failed,
    )

    # 5. Dependency-Ordered Triage Engine (6 boundaries)
    t_pci = triage_gpu_node_or_pod(
        MissingGpuTriageCase("no-pci", False, False, False, False, 0, False, False)
    )
    t_drv = triage_gpu_node_or_pod(
        MissingGpuTriageCase("rm-init-fail", True, False, False, False, 0, False, False)
    )
    t_dp = triage_gpu_node_or_pod(
        MissingGpuTriageCase("dp-crashloop", True, True, False, False, 0, False, False)
    )
    t_kub = triage_gpu_node_or_pod(
        MissingGpuTriageCase("dial-timeout", True, True, True, False, 0, False, False)
    )
    t_inj = triage_gpu_node_or_pod(
        MissingGpuTriageCase("empty-devices", True, True, True, True, 8, False, False)
    )
    t_compat = triage_gpu_node_or_pod(
        MissingGpuTriageCase("abi-mismatch", True, True, True, True, 8, True, False)
    )
    t_ok = triage_gpu_node_or_pod(
        MissingGpuTriageCase("healthy", True, True, True, True, 8, True, True)
    )

    _check(
        t_pci["failing_boundary"] == "hardware_pci_passthrough",
        "Triage routes missing lspci device to hardware_pci_passthrough",
        passed,
        failed,
    )
    _check(
        t_drv["failing_boundary"] == "driver_kernel_boundary",
        "Triage routes RmInitAdapter / failed host nvidia-smi to driver_kernel_boundary before touching plugin",
        passed,
        failed,
    )
    _check(
        t_dp["failing_boundary"] == "device_plugin_boundary",
        "Triage routes healthy host driver + failing plugin Pod to device_plugin_boundary",
        passed,
        failed,
    )
    _check(
        t_kub["failing_boundary"] == "kubelet_registration_boundary",
        "Triage routes healthy plugin + kubelet socket dial timeout to kubelet_registration_boundary",
        passed,
        failed,
    )
    _check(
        t_inj["failing_boundary"] == "runtime_injection_boundary",
        "Triage routes empty crictl inspect devices[] array to runtime_injection_boundary",
        passed,
        failed,
    )
    _check(
        t_compat["failing_boundary"] == "driver_to_image_compatibility",
        "Triage routes populated devices[] + failed container nvidia-smi to driver_to_image_compatibility",
        passed,
        failed,
    )
    _check(
        t_ok["failing_boundary"] == "healthy_or_scheduling_policy",
        "Triage routes all-green node and container checks to healthy_or_scheduling_policy",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
