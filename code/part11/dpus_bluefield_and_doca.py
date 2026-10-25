#!/usr/bin/env python3
"""Chapter 11.28 model: BlueField DPUs, DOCA, Zero-Trust Offload & 3-Layer Incident Triage.

Models:
1. Volume 09 Chapter 9 BlueField SKU Operating Modes & Traffic Path Classifier:
   - BlueField DPU SKU default = DPU mode (Embedded CPU Function Ownership, ECPF)
     where Arm owns NIC resources & embedded switch (representor slow path ->
     embedded-switch flow-rule fast path),
   - BlueField SuperNIC SKU default = NIC mode.
2. Volume 09 Chapter 9 Figure 9.9.1 3-Layer Outage Triage Engine:
   - Layer 3 External uplink (leaf switch swp14 up 100G full RoCE-compute),
   - Layer 2 DPU Arm control plane (openvswitch-policy-load.service Active: failed,
     status=1, or image drift node09 on dpu-image-24.07-prod-1 vs 24.10-prod-3 after 5 retries),
   - Layer 1 Host interface (enp1s0f0np0 DOWN / DORMANT).
3. Volume 18 Chapter 8 Shared Fate vs BlueField DPU Zero-Trust Security Offload
   (DOCA Flow micro-segmentation, 400G IPSec/TLS & storage encryption offload keeping
   keys in DPU RAM out of untrusted x86 Host RAM) + Volume 18 Ch 12 Forensic IR integration.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


DPU_SIX_CHANGE_STEPS: List[str] = [
    "1. Qualify release set (DPU firmware/image, DOCA components, host driver, switch/NOS profile, service)",
    "2. Capture baseline data-plane behavior, host/DPU/fabric telemetry, and rollback artifacts",
    "3. Canary a representative hardware and workload group",
    "4. Verify DPU readiness, host-facing function, external uplink, policy enforcement, and app traffic separately",
    "5. Expand in batches only after comparing workload and failure-path evidence with baseline",
    "6. Preserve a documented out-of-band recovery and image rollback procedure",
]

DPU_FIVE_OBSERVABILITY_LAYERS: List[str] = [
    "Host",
    "DPU control plane",
    "DPU data plane",
    "Fabric",
    "Platform",
]

DOCA_FOUR_IMPLEMENTATION_OPTIONS: List[Dict[str, str]] = [
    {
        "option": "Supported DOCA service",
        "best_fit": "Documented use case matching the required outcome",
        "tradeoff": "Still needs version, security, and operations qualification",
    },
    {
        "option": "DOCA reference application/sample",
        "best_fit": "Evaluation or learning",
        "tradeoff": "Not a production support commitment by itself",
    },
    {
        "option": "Custom DOCA application",
        "best_fit": "Differentiated requirement with long-term engineering ownership",
        "tradeoff": "Full test, security, release, and on-call support burden",
    },
    {
        "option": "Host/fabric-native implementation",
        "best_fit": "DPU adds no measurable value or lacks an operational owner",
        "tradeoff": "Retains host CPU overhead or a weaker host-edge boundary",
    },
]


@dataclass(frozen=True)
class BluefieldThreeLayerState:
    node_name: str
    switch_uplink_port: str
    switch_uplink_up: bool
    switch_speed_gbps: int
    dpu_arm_policy_service_active: bool
    dpu_image_version: str
    expected_fleet_dpu_image: str
    dpu_reconcile_failed_retries: int
    host_interface_name: str
    host_interface_up: bool


def diagnose_bluefield_three_layer_path(state: BluefieldThreeLayerState) -> Dict[str, object]:
    """Implements Volume 09 Chapter 9 Figure 9.9.1 & Scenarios 1-2 3-layer DPU diagnosis."""
    if not state.switch_uplink_up:
        return {
            "failed_layer": "Layer 3: External Ethernet uplink / fabric",
            "root_cause": f"Switch port {state.switch_uplink_port} is DOWN",
            "remediation": "Perform standard physical link/optics/switch-port troubleshooting",
        }
    if state.dpu_image_version != state.expected_fleet_dpu_image:
        return {
            "failed_layer": "Layer 2: DPU Arm control plane (Image Drift)",
            "root_cause": (
                f"{state.node_name} running stale {state.dpu_image_version} vs {state.expected_fleet_dpu_image} "
                f"(reconcile abandoned after {state.dpu_reconcile_failed_retries} retries)"
            ),
            "remediation": "Re-trigger controlled DPU image reconciliation via OOB/BMC and verify version convergence",
        }
    if not state.dpu_arm_policy_service_active:
        return {
            "failed_layer": "Layer 2: DPU Arm control plane (Embedded-Switch Policy Load Failed)",
            "root_cause": (
                f"External uplink {state.switch_uplink_port} ({state.switch_speed_gbps}G) is UP, but Arm policy load "
                f"failed on boot, leaving host interface {state.host_interface_name} DOWN/DORMANT"
            ),
            "remediation": "Restore approved DPU policy/image via OOB recovery and gate node readiness on policy + host link UP",
        }
    if not state.host_interface_up:
        return {
            "failed_layer": "Layer 1: Host-facing function / representor mismatch",
            "root_cause": f"DPU policy loaded, but host interface {state.host_interface_name} is DOWN",
            "remediation": "Inspect host mlx5 driver, VF/PF representor mapping, and host network config",
        }
    return {
        "failed_layer": "None (All 3 Layers Healthy)",
        "root_cause": "External uplink, DPU Arm/embedded switch, and host interface are all UP",
        "remediation": "Proceed to application/workload layer if symptoms persist",
    }


def evaluate_shared_fate_vs_dpu_offload(
    firewall_runs_on_dpu_arm: bool,
    encryption_keys_in_dpu_ram: bool,
    host_os_compromised_by_root_attacker: bool,
) -> Dict[str, object]:
    """Models Volume 18 Chapter 8 Shared Fate vs BlueField DPU Zero-Trust Offload."""
    if not firewall_runs_on_dpu_arm and host_os_compromised_by_root_attacker:
        return {
            "security_boundary_intact": False,
            "shared_fate_triggered": True,
            "attacker_can_stop_firewall": True,
            "keys_exposed_in_host_ram": not encryption_keys_in_dpu_ram,
            "verdict": "BREACH_UNCONTAINED: Host root attacker runs 'systemctl stop iptables' and launches lateral/DDoS attack",
        }
    return {
        "security_boundary_intact": True,
        "shared_fate_triggered": False,
        "attacker_can_stop_firewall": False,
        "keys_exposed_in_host_ram": not encryption_keys_in_dpu_ram,
        "verdict": "BREACH_CONTAINED_BY_DPU: Isolated Arm OS and DOCA Flow hardware firewall drop unauthorized packets on the wire",
    }
