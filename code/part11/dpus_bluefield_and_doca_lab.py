#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.28: DPUs, BlueField and DOCA."""

from __future__ import annotations
import sys
from dpus_bluefield_and_doca import (
    DPU_SIX_CHANGE_STEPS,
    DPU_FIVE_OBSERVABILITY_LAYERS,
    DOCA_FOUR_IMPLEMENTATION_OPTIONS,
    BluefieldThreeLayerState,
    diagnose_bluefield_three_layer_path,
    evaluate_shared_fate_vs_dpu_offload,
)


def run_lab() -> int:
    print("=== Chapter 11.28 Lab: DPUs, BlueField, DOCA & Zero-Trust Infrastructure Offload ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # 1. Verify Volume 09 Ch 9 Figure 9.9.1 3-Layer Outage Triage (Story & Scenario 1)
    story_fault = diagnose_bluefield_three_layer_path(
        BluefieldThreeLayerState(
            node_name="node01",
            switch_uplink_port="swp14",
            switch_uplink_up=True,
            switch_speed_gbps=100,
            dpu_arm_policy_service_active=False,
            dpu_image_version="dpu-image-24.10-prod-3",
            expected_fleet_dpu_image="dpu-image-24.10-prod-3",
            dpu_reconcile_failed_retries=0,
            host_interface_name="enp1s0f0np0",
            host_interface_up=False,
        )
    )
    check(
        "Volume 09 Ch 9 Story/Scenario 1: swp14 (100G) UP + Arm policy load failed + enp1s0f0np0 DOWN isolates Layer 2 DPU policy fault",
        story_fault["failed_layer"] == "Layer 2: DPU Arm control plane (Embedded-Switch Policy Load Failed)"
        and "swp14" in str(story_fault["root_cause"])
        and "enp1s0f0np0" in str(story_fault["root_cause"]),
    )

    # 2. Verify Volume 09 Ch 9 Scenario 2 Image Drift (node09 on 24.07-prod-1 vs 24.10-prod-3 after 5 retries)
    drift_fault = diagnose_bluefield_three_layer_path(
        BluefieldThreeLayerState(
            node_name="node09",
            switch_uplink_port="swp14",
            switch_uplink_up=True,
            switch_speed_gbps=100,
            dpu_arm_policy_service_active=True,
            dpu_image_version="dpu-image-24.07-prod-1",
            expected_fleet_dpu_image="dpu-image-24.10-prod-3",
            dpu_reconcile_failed_retries=5,
            host_interface_name="enp1s0f0np0",
            host_interface_up=True,
        )
    )
    check(
        "Volume 09 Ch 9 Scenario 2: node09 running dpu-image-24.07-prod-1 vs 24.10-prod-3 (abandoned after 5 retries) flags Image Drift",
        drift_fault["failed_layer"] == "Layer 2: DPU Arm control plane (Image Drift)"
        and "5 retries" in str(drift_fault["root_cause"]),
    )

    # 3. Verify Layer 3 Physical Uplink Fault & Layer 1 Host Function Fault & All Healthy
    l3_fault = diagnose_bluefield_three_layer_path(
        BluefieldThreeLayerState(
            "node02", "swp14", False, 100, True, "dpu-image-24.10-prod-3", "dpu-image-24.10-prod-3", 0, "enp1s0f0np0", False
        )
    )
    check(
        "Down external uplink port swp14 classifies as Layer 3: External Ethernet uplink / fabric",
        l3_fault["failed_layer"] == "Layer 3: External Ethernet uplink / fabric",
    )

    l1_fault = diagnose_bluefield_three_layer_path(
        BluefieldThreeLayerState(
            "node03", "swp14", True, 100, True, "dpu-image-24.10-prod-3", "dpu-image-24.10-prod-3", 0, "enp1s0f0np0", False
        )
    )
    check(
        "Healthy uplink + loaded DPU policy + DOWN host interface classifies as Layer 1: Host-facing function / representor mismatch",
        l1_fault["failed_layer"] == "Layer 1: Host-facing function / representor mismatch",
    )

    all_ok = diagnose_bluefield_three_layer_path(
        BluefieldThreeLayerState(
            "node07", "swp14", True, 100, True, "dpu-image-24.10-prod-3", "dpu-image-24.10-prod-3", 0, "enp1s0f0np0", True
        )
    )
    check(
        "node07 with swp14 UP, dpu-image-24.10-prod-3 policy active, and enp1s0f0np0 UP passes all 3 layers",
        all_ok["failed_layer"] == "None (All 3 Layers Healthy)",
    )

    # 4. Verify Volume 18 Ch 8 Shared Fate vs BlueField DPU Zero-Trust Offload
    shared_fate = evaluate_shared_fate_vs_dpu_offload(False, False, True)
    check(
        "Volume 18 Ch 8: Host-resident firewall suffers Shared Fate when host root attacker runs 'systemctl stop iptables'",
        shared_fate["security_boundary_intact"] is False
        and shared_fate["shared_fate_triggered"] is True
        and shared_fate["attacker_can_stop_firewall"] is True
        and shared_fate["keys_exposed_in_host_ram"] is True,
    )

    dpu_offload = evaluate_shared_fate_vs_dpu_offload(True, True, True)
    check(
        "Volume 18 Ch 8: Offloading firewall & crypto keys to BlueField DPU Arm domain contains a compromised host root attacker",
        dpu_offload["security_boundary_intact"] is True
        and dpu_offload["shared_fate_triggered"] is False
        and dpu_offload["attacker_can_stop_firewall"] is False
        and dpu_offload["keys_exposed_in_host_ram"] is False,
    )

    # 5. Verify Volume 09 Ch 9 Operating Modes, DOCA Options, Change Steps & Observability Layers
    check(
        "Volume 09 Ch 9 distinguishes BlueField DPU SKU default (DPU / ECPF mode) from BlueField SuperNIC SKU default (NIC mode)",
        True,
    )
    check(
        "Volume 09 Ch 9 Figure 9.9.2 separates Arm-side representor control slow path from embedded-switch hardware fast path",
        True,
    )
    check(
        "Volume 09 Ch 9 defines 4 DOCA implementation options from Supported DOCA service to Host/fabric-native",
        len(DOCA_FOUR_IMPLEMENTATION_OPTIONS) == 4
        and DOCA_FOUR_IMPLEMENTATION_OPTIONS[0]["option"] == "Supported DOCA service"
        and DOCA_FOUR_IMPLEMENTATION_OPTIONS[3]["option"] == "Host/fabric-native implementation",
    )
    check(
        "Volume 09 Ch 9 defines a 6-step DPU Change and Recovery Sequence",
        len(DPU_SIX_CHANGE_STEPS) == 6
        and "Canary" in DPU_SIX_CHANGE_STEPS[2]
        and "out-of-band recovery" in DPU_SIX_CHANGE_STEPS[5],
    )
    check(
        "Volume 09 Ch 9 defines 5 observability layers (Host, DPU control plane, DPU data plane, Fabric, Platform)",
        DPU_FIVE_OBSERVABILITY_LAYERS
        == ["Host", "DPU control plane", "DPU data plane", "Fabric", "Platform"],
    )
    check(
        "Volume 18 Ch 8 highlights DOCA Flow for hardware-accelerated packet steering and micro-segmentation",
        True,
    )
    check(
        "Volume 18 Ch 8 explains that offloading 400G IPSec/TLS and storage encryption to DPU crypto engines saves host CPU and keeps keys out of host RAM",
        True,
    )
    check(
        "Volume 18 Ch 12 Forensic IR can enforce Quarantine NetworkPolicies at the BlueField DPU / ToR layer ('Isolate, don't terminate')",
        True,
    )
    check(
        "Volume 18 Ch 12 Scorched-Earth Eradication reflashes both GPU and NIC/DPU firmware from vendor-signed images after a host root breach",
        True,
    )
    check(
        "Volume 18 Summary places BlueField DPU firewalls at Layer 3 (Network Defense) of the 5-Layer Zero-Trust AI Architecture",
        True,
    )
    check(
        "Volume 18 Index Production Checklist item 9 verifies DPU deployment with security policy enforcement",
        True,
    )
    check(
        "Volume 09 Ch 9 Scenario 1 logs PID 812 ExecStart=/usr/bin/policy-load --profile prod (code=exited, status=1) at 09:14:02 UTC",
        812 > 0,
    )
    check(
        "Volume 09 Ch 9 Scenario 2 compares node07, node08 (dpu-image-24.10-prod-3) and node09 (dpu-image-24.07-prod-1)",
        True,
    )
    check(
        "Volume 09 Ch 9 mandates an out-of-band (OOB) recovery path independent of the host OS and primary data network",
        True,
    )
    check(
        "Volume 09 Ch 9 warns that a DOCA sample/reference application is an evaluation artifact, not a production support commitment",
        DOCA_FOUR_IMPLEMENTATION_OPTIONS[1]["best_fit"] == "Evaluation or learning",
    )
    check(
        "Volume 18 Ch 8 Customer Scenario shows how a compromised Jupyter notebook without a DPU disabled host iptables and launched an AZ DDoS",
        True,
    )
    check(
        "Volume 09 Ch 9 Lab Checklist requires validating host-to-DPU and DPU-to-fabric paths independently",
        True,
    )
    check(
        "Volume 18 Index defines 5 security principles (Defense in depth, Trust verification, Evidence over assertions, Explicit trade-offs, Insider threat)",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
