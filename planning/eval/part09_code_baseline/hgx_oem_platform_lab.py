#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.3: HGX platforms and OEM integration."""

from __future__ import annotations

import sys

from hgx_oem_platform import (
    audit_oem_hgx_topology,
    calculate_dc_bus_current_and_loss,
    diagnose_hgx_fault_boundary,
    review_hgx_rack_power,
)


def run_checks() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label} -- {detail}")

    print("=== Chapter 9.3 Lab: HGX Platforms and OEM Integration ===")

    # 1. 12V vs 48V/54V DC bus electrical physics checks (V6 Ch 2 & Ch 5)
    dc_54 = calculate_dc_bus_current_and_loss(10000.0, voltage_a=12.0, voltage_b=54.0)
    check(
        "V6 Ch5: 10 kW at 12V draws 833.33 A vs 185.19 A at 54V",
        dc_54["current_a_amps"] == 833.33 and dc_54["current_b_amps"] == 185.19,
        f"got {dc_54}",
    )
    check(
        "V6 Ch5: 54V reduces current by 4.5x and I^2*R resistive loss by 20.25x vs 12V",
        dc_54["current_reduction_factor"] == 4.5
        and dc_54["resistive_loss_reduction_factor"] == 20.25,
        f"got {dc_54}",
    )

    dc_48 = calculate_dc_bus_current_and_loss(10000.0, voltage_a=12.0, voltage_b=48.0)
    check(
        "V6 Ch2/Ch5: 10 kW at 48V draws 208.33 A (4.0x lower current, 16.0x lower I^2*R loss)",
        dc_48["current_b_amps"] == 208.33
        and dc_48["current_reduction_factor"] == 4.0
        and dc_48["resistive_loss_reduction_factor"] == 16.0,
        f"got {dc_48}",
    )

    try:
        calculate_dc_bus_current_and_loss(0.0)
        check("Rejects non-positive power in DC bus calculator", False)
    except ValueError:
        check("Rejects non-positive power in DC bus calculator", True)

    # 2. HGX physical FRU & OEM RMA boundary checks (V6 Ch 2 & Ch 3)
    f_nvsw = diagnose_hgx_fault_boundary(
        {"oem_vendor": "Supermicro", "gpu_pcie_healthy": True, "nvswitch_silicon_fault": True}
    )
    check(
        "V6 Ch2 Customer Scenario: Failed NVSwitch ASIC requires full HGX baseboard RMA via OEM (GPU swap = no)",
        f_nvsw["primary_rma_contact"] == "Supermicro"
        and f_nvsw["fault_domain"] == "hgx_baseboard_nvswitch"
        and f_nvsw["sxm_gpu_swap_fixes_issue"] == "no",
        f"got {f_nvsw}",
    )

    f_xid79 = diagnose_hgx_fault_boundary(
        {"oem_vendor": "Lenovo", "xid_79_fallen_off_bus": True}
    )
    check(
        "V6 Ch3 Customer Scenario: Xid 79 escalates to Lenovo with riser/cable + SXM GPU FRU",
        f_xid79["primary_rma_contact"] == "Lenovo"
        and f_xid79["fault_domain"] == "pcie_host_to_hgx_path"
        and "PCIe riser" in f_xid79["fru_to_replace"],
        f"got {f_xid79}",
    )

    f_sxm = diagnose_hgx_fault_boundary(
        {"oem_vendor": "Dell", "single_sxm_gpu_fault": True}
    )
    check(
        "V6 Ch2: Single SXM GPU silicon fault replaces only the bolted SXM FRU via OEM",
        f_sxm["primary_rma_contact"] == "Dell"
        and f_sxm["fault_domain"] == "sxm_module"
        and f_sxm["sxm_gpu_swap_fixes_issue"] == "yes",
        f"got {f_sxm}",
    )

    # 3. OEM HGX server architecture & Lab 01 proposal comparison checks (V6 Ch 4, 5, 6, Lab 01)
    platform_a = {
        "gpu_count": 8,
        "has_nvswitch": True,
        "topo_m_provided": True,
        "gpu_to_nic_topo": "PIX",
        "compute_nic_count": 8,
        "isolated_storage_network": True,
        "nvme_attachment": "pcie_switch",
        "nccl_p2p_disable_set": False,
        "raw_vendor_vbios_flashed": False,
        "rear_gpu_thermal_slowdown": False,
    }
    res_a = audit_oem_hgx_topology(platform_a)
    check(
        "V6 Lab 01 Platform A (8x H100, PIX, 8x 400G NICs, isolated storage, PCIe-switched NVMe) passes gate",
        res_a["passes_architecture_gate"] is True
        and len(res_a["mandatory_failures"]) == 0
        and len(res_a["evidence_gaps"]) == 0,
        f"got {res_a}",
    )

    platform_b = {
        "gpu_count": 8,
        "has_nvswitch": True,
        "topo_m_provided": False,
        "compute_nic_count": 4,
        "isolated_storage_network": False,
        "nvme_attachment": "cpu_root_complex",
    }
    res_b = audit_oem_hgx_topology(platform_b)
    check(
        "V6 Lab 01 Platform B flags missing topo -m evidence gap",
        res_b["passes_architecture_gate"] is False
        and "missing_nvidia_smi_topo_m_evidence" in res_b["evidence_gaps"],
        f"got {res_b}",
    )
    check(
        "V6 Lab 01 Platform B flags 4:8 NIC underprovisioning, shared storage network, and CPU-wired NVMe",
        any("underprovisioned_compute_nics" in m for m in res_b["mandatory_failures"])
        and "storage_network_not_isolated_from_compute_fabric" in res_b["mandatory_failures"]
        and any("nvme_wired_to_cpu_root_complex" in m for m in res_b["mandatory_failures"]),
        f"got {res_b}",
    )

    unbalanced_2nic = dict(
        platform_a,
        compute_nic_count=2,
        gpu_to_nic_topo="SYS",
        nccl_p2p_disable_set=True,
    )
    res_unb = audit_oem_hgx_topology(unbalanced_2nic)
    check(
        "V6 Ch4 Customer Scenario: 2-NIC SYS topology + NCCL_P2P_DISABLE=1 anti-pattern caught",
        any("unbalanced_gpu_to_nic_path" in m for m in res_unb["mandatory_failures"])
        and "nccl_p2p_disable_antipattern (disables direct NVLink peer-to-peer)"
        in res_unb["mandatory_failures"],
        f"got {res_unb}",
    )

    redstone_upgrade = dict(
        platform_a,
        gpu_count=4,
        has_nvswitch=False,
        compute_nic_count=4,
        plan_upgrade_to_8_gpus=True,
    )
    check(
        "V6 Ch2: Flags attempting to upgrade a 4-GPU point-to-point board to 8 GPUs",
        any("4gpu_board_not_upgradeable_to_8gpu" in m for m in audit_oem_hgx_topology(redstone_upgrade)["mandatory_failures"]),
    )

    frankenstein_fw = dict(platform_a, raw_vendor_vbios_flashed=True)
    check(
        "V6 Ch3: Flags flashing raw NVIDIA VBIOS outside OEM-certified bundle",
        any("frankenstein_firmware_risk" in m for m in audit_oem_hgx_topology(frankenstein_fw)["mandatory_failures"]),
    )

    shadowing = dict(platform_a, rear_gpu_thermal_slowdown=True)
    check(
        "V6 Ch5: Flags airflow shadowing thermal slowdown on rear row of GPUs",
        any("airflow_shadowing_on_rear_gpus" in m for m in audit_oem_hgx_topology(shadowing)["mandatory_failures"]),
    )

    # 4. V6 Lab 01 & Lab 02 Rack Power & Single-Feed Survival checks
    rack_4node = review_hgx_rack_power(
        nodes_per_rack=4,
        node_power_kw=7.9,
        switch_overhead_kw=0.6,
        facility_rack_limit_kw=18.0,
    )
    check(
        "V6 Lab 01 Step 5: 4 nodes/rack at 7.9 kW + 0.6 kW switches = 32.2 kW > 18.0 kW limit -> No-go",
        rack_4node["total_rack_kw"] == 32.2
        and rack_4node["within_facility_limit"] is False
        and rack_4node["decision"] == "No-go",
        f"got {rack_4node}",
    )

    rack_2node = review_hgx_rack_power(
        nodes_per_rack=2,
        node_power_kw=7.9,
        switch_overhead_kw=0.6,
        facility_rack_limit_kw=18.0,
        pdu_voltage_v=415.0,
        pdu_current_a=32.0,
        phases=3,
        derating_factor=0.80,
        has_redundant_compute_nics=False,
    )
    check(
        "V6 Lab 02 Step 2: 2 nodes * 7.9 kW + 0.6 kW switches == 16.4 kW (1.6 kW facility headroom)",
        rack_2node["total_rack_kw"] == 16.4 and rack_2node["facility_headroom_kw"] == 1.6,
        f"got {rack_2node}",
    )
    check(
        "V6 Lab 02 Step 2: 415V 3-phase 32A feed is 23.0 kW nameplate and 18.4 kW at 80% continuous derating",
        rack_2node["nameplate_per_feed_kw"] == 23.0 and rack_2node["derated_per_feed_kw"] == 18.4,
        f"got {rack_2node}",
    )
    check(
        "V6 Lab 02 Step 10: 2-node rack survives single-feed failure (2.0 kW margin) with Conditional go",
        rack_2node["survives_single_feed_loss"] is True
        and rack_2node["single_feed_margin_kw"] == 2.0
        and rack_2node["decision"] == "Conditional go",
        f"got {rack_2node}",
    )

    rack_go = review_hgx_rack_power(
        nodes_per_rack=2,
        node_power_kw=7.9,
        switch_overhead_kw=0.6,
        facility_rack_limit_kw=22.0,
        pdu_voltage_v=415.0,
        pdu_current_a=60.0,
        phases=3,
        derating_factor=0.80,
        has_redundant_compute_nics=True,
    )
    check(
        "Rack with >=3 kW headroom and accepted/redundant NIC design achieves Go",
        rack_go["decision"] == "Go",
        f"got {rack_go}",
    )

    # Additional boundary & acceptance checks (V6 Ch 2, Ch 4, Ch 6, Ch 7, Lab 01, Lab 02)
    f_unknown = diagnose_hgx_fault_boundary({"oem_vendor": "HPE"})
    check(
        "Unclassified HGX fault still routes primary RMA to HPE and recommends dcgmi/nvlink/BMC diagnostics",
        f_unknown["primary_rma_contact"] == "HPE" and f_unknown["fault_domain"] == "unknown",
        f"got {f_unknown}",
    )

    pxb_platform = dict(platform_a, gpu_to_nic_topo="PXB")
    check(
        "PXB (multi-PCIe-switch P2P without crossing CPU root complex) passes topology gate",
        audit_oem_hgx_topology(pxb_platform)["passes_architecture_gate"] is True,
    )

    node_platform = dict(platform_a, gpu_to_nic_topo="NODE")
    check(
        "NODE (crossing PCIe host bridge on same NUMA socket) flagged as unbalanced GPU-to-NIC path",
        any("unbalanced_gpu_to_nic_path (NODE" in m for m in audit_oem_hgx_topology(node_platform)["mandatory_failures"]),
    )

    phb_platform = dict(platform_a, gpu_to_nic_topo="PHB")
    check(
        "PHB (PCIe host bridge traversal) flagged as unbalanced GPU-to-NIC path",
        any("unbalanced_gpu_to_nic_path (PHB" in m for m in audit_oem_hgx_topology(phb_platform)["mandatory_failures"]),
    )

    valid_4gpu = dict(platform_a, gpu_count=4, has_nvswitch=False, compute_nic_count=4, plan_upgrade_to_8_gpus=False)
    check(
        "4-GPU HGX server with 4 compute NICs and no 8-GPU upgrade assumption passes gate",
        audit_oem_hgx_topology(valid_4gpu)["passes_architecture_gate"] is True,
    )

    rack_feed_fail = review_hgx_rack_power(
        nodes_per_rack=2,
        node_power_kw=7.9,
        switch_overhead_kw=0.6,
        facility_rack_limit_kw=18.0,
        pdu_voltage_v=208.0,
        pdu_current_a=30.0,
        phases=3,
        derating_factor=0.80,
    )
    check(
        "Under-sized 208V 3-phase 30A feed (8.65 kW derated) fails single-feed survival test -> No-go",
        rack_feed_fail["survives_single_feed_loss"] is False
        and rack_feed_fail["decision"] == "No-go",
        f"got {rack_feed_fail}",
    )

    try:
        review_hgx_rack_power(0, 7.9, 0.6, 18.0)
        check("Rejects non-positive nodes_per_rack in rack power review", False)
    except ValueError:
        check("Rejects non-positive nodes_per_rack in rack power review", True)

    dc_1kw_12v = calculate_dc_bus_current_and_loss(1000.0, voltage_a=12.0, voltage_b=54.0)
    check(
        "V6 Ch2 rule: 1 kW at 12V is 83.33 A (> 80 Amps per kW)",
        dc_1kw_12v["current_a_amps"] == 83.33,
        f"got {dc_1kw_12v}",
    )

    dc_5_6kw = calculate_dc_bus_current_and_loss(5600.0, voltage_a=12.0, voltage_b=54.0)
    check(
        "V6 Ch2/Ch5: 8x 700W GPUs (5.6 kW) draw 466.67 A at 12V vs 103.70 A at 54V",
        dc_5_6kw["current_a_amps"] == 466.67 and dc_5_6kw["current_b_amps"] == 103.7,
        f"got {dc_5_6kw}",
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
