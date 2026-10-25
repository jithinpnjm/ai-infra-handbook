#!/usr/bin/env python3
"""Part 9, Chapter 9.3: HGX platforms and OEM integration model.

Encodes the engineering rules, electrical formulas, topology checks, support
boundaries, proposal comparison matrix, and rack power/thermal review from:
- nvidia-devops Volume 06 Chapters 1-7 & Labs 01-02
- Distributed AI Systems Chapter 2
- AI Systems Performance Engineering Chapter 2
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List


def calculate_dc_bus_current_and_loss(
    power_watts: float,
    voltage_a: float = 12.0,
    voltage_b: float = 54.0,
) -> Dict[str, float]:
    """Compare current (I = P / V) and relative resistive loss (I^2 * R) across two DC bus voltages.

    Sources:
    - nvidia-devops Volume 06 Chapter 2 ("2. Power Delivery: The 54V Shift")
    - nvidia-devops Volume 06 Chapter 5 ("1. Power Delivery: The 54-Volt Transition")
    Example: 10,000 W at 12 V = 833.33 A; at 54 V = 185.19 A (4.5x lower current,
    20.25x lower I^2*R resistive loss; at 48 V = 208.33 A, 4.0x lower current, 16.0x lower loss).
    """
    if power_watts <= 0 or voltage_a <= 0 or voltage_b <= 0:
        raise ValueError("power_watts and voltages must be positive.")
    current_a = power_watts / voltage_a
    current_b = power_watts / voltage_b
    current_ratio = current_a / current_b
    loss_ratio = (current_a ** 2) / (current_b ** 2)
    return {
        "current_a_amps": round(current_a, 2),
        "current_b_amps": round(current_b, 2),
        "current_reduction_factor": round(current_ratio, 2),
        "resistive_loss_reduction_factor": round(loss_ratio, 2),
    }


def diagnose_hgx_fault_boundary(symptom: Dict[str, object]) -> Dict[str, str]:
    """Determine the physical fault component, RMA owner, and FRU scope on an OEM HGX server.

    Sources:
    - nvidia-devops Volume 06 Chapter 2 ("1.1 The SXM Modules", "1.2 The NVSwitches", Customer Scenario)
    - nvidia-devops Volume 06 Chapter 3 ("1. The Physical Boundary", "2. The Firmware Boundary", Customer Scenario)
    Rules:
    - Primary RMA contact is ALWAYS the OEM (Dell, Lenovo, HPE, Supermicro), never direct to NVIDIA,
      because the customer purchased the integrated server from the OEM.
    - If a single GPU is healthy on PCIe (`gpu_pcie_healthy=True`) but all GPUs or a GPU fail NVLink due
      to a dead NVSwitch ASIC (`nvswitch_silicon_fault=True`), replacing the bolted SXM GPU FRU will NOT
      fix the issue; the permanently soldered HGX baseboard must be RMA'd via the OEM.
    - If a single SXM GPU has uncorrected HBM ECC / silicon failure (`single_sxm_gpu_fault=True`),
      only that bolted SXM module FRU is replaced by the OEM field technician.
    - If `Xid 79 (GPU has fallen off the bus)` occurs (`xid_79_fallen_off_bus=True`), the fault lies in the
      host-to-baseboard PCIe path (OEM riser, high-speed cable, HGX retimer, or SXM socket); collect
      `nvidia-bug-report.sh` + OEM BMC diagnostics and have the OEM dispatch both a replacement PCIe riser/cable
      and an SXM GPU FRU.
    """
    oem_vendor = str(symptom.get("oem_vendor", "OEM"))

    if bool(symptom.get("nvswitch_silicon_fault", False)):
        return {
            "primary_rma_contact": oem_vendor,
            "fault_domain": "hgx_baseboard_nvswitch",
            "fru_to_replace": "Entire HGX 8-GPU Baseboard (NVSwitch ASICs are permanently soldered)",
            "sxm_gpu_swap_fixes_issue": "no",
        }

    if bool(symptom.get("xid_79_fallen_off_bus", False)):
        return {
            "primary_rma_contact": oem_vendor,
            "fault_domain": "pcie_host_to_hgx_path",
            "fru_to_replace": "OEM PCIe riser/high-speed cable + SXM GPU FRU (verify with nvidia-bug-report.sh and OEM BMC logs)",
            "sxm_gpu_swap_fixes_issue": "maybe",
        }

    if bool(symptom.get("single_sxm_gpu_fault", False)):
        return {
            "primary_rma_contact": oem_vendor,
            "fault_domain": "sxm_module",
            "fru_to_replace": "Single bolted SXM GPU module FRU (HGX baseboard remains in chassis)",
            "sxm_gpu_swap_fixes_issue": "yes",
        }

    return {
        "primary_rma_contact": oem_vendor,
        "fault_domain": "unknown",
        "fru_to_replace": "Run dcgmi diag -r 3, nvidia-smi nvlink --status, and OEM BMC hardware diagnostics",
        "sxm_gpu_swap_fixes_issue": "unknown",
    }


def audit_oem_hgx_topology(proposal: Dict[str, object]) -> Dict[str, object]:
    """Audit an OEM HGX server's PCIe, NIC, NVMe, and cooling design for architectural bottlenecks.

    Sources:
    - nvidia-devops Volume 06 Chapters 4, 5, 6
    - nvidia-devops Volume 06 Lab 01 ("Compare HGX-Based Server Designs")
    """
    issues: List[str] = []
    evidence_gaps: List[str] = []

    gpu_count = int(proposal.get("gpu_count", 8))
    has_nvswitch = bool(proposal.get("has_nvswitch", gpu_count == 8))
    if gpu_count == 4 and not has_nvswitch and bool(proposal.get("plan_upgrade_to_8_gpus", False)):
        issues.append("4gpu_board_not_upgradeable_to_8gpu (fixed PCB traces, no NVSwitches)")

    if not bool(proposal.get("topo_m_provided", False)):
        evidence_gaps.append("missing_nvidia_smi_topo_m_evidence")
    else:
        gpu_to_nic_hop = str(proposal.get("gpu_to_nic_topo", "PIX"))
        if gpu_to_nic_hop in ("SYS", "NODE", "PHB"):
            issues.append(f"unbalanced_gpu_to_nic_path ({gpu_to_nic_hop} hits CPU root complex/UPI)")

    compute_nics = int(proposal.get("compute_nic_count", 0))
    if compute_nics < gpu_count:
        issues.append(f"underprovisioned_compute_nics ({compute_nics}:{gpu_count} ratio instead of 1:1)")

    if not bool(proposal.get("isolated_storage_network", False)):
        issues.append("storage_network_not_isolated_from_compute_fabric")

    nvme_attachment = str(proposal.get("nvme_attachment", "pcie_switch"))
    if nvme_attachment == "cpu_root_complex":
        issues.append("nvme_wired_to_cpu_root_complex (GDS falls back to CPU bounce buffer)")

    if bool(proposal.get("nccl_p2p_disable_set", False)):
        issues.append("nccl_p2p_disable_antipattern (disables direct NVLink peer-to-peer)")

    if bool(proposal.get("raw_vendor_vbios_flashed", False)):
        issues.append("frankenstein_firmware_risk (must use OEM-certified firmware bundle)")

    if bool(proposal.get("rear_gpu_thermal_slowdown", False)):
        issues.append("airflow_shadowing_on_rear_gpus (front GPUs pre-heating intake air)")

    return {
        "passes_architecture_gate": len(issues) == 0 and len(evidence_gaps) == 0,
        "mandatory_failures": issues,
        "evidence_gaps": evidence_gaps,
    }


def review_hgx_rack_power(
    nodes_per_rack: int,
    node_power_kw: float,
    switch_overhead_kw: float,
    facility_rack_limit_kw: float,
    pdu_voltage_v: float = 415.0,
    pdu_current_a: float = 32.0,
    phases: int = 3,
    derating_factor: float = 0.80,
    has_redundant_compute_nics: bool = False,
) -> Dict[str, object]:
    """Perform the Volume 06 Lab 01 & Lab 02 rack power and single-feed survival calculation.

    Sources:
    - nvidia-devops Volume 06 Lab 01 Step 5 ("Evaluate facility fit"):
      4 nodes * 7.9 kW = 31.6 kW > 18 kW limit (Fail -> reduce to 2 nodes/rack).
    - nvidia-devops Volume 06 Lab 02 Step 2 ("Calculate power") & Step 10 ("Verification"):
      - 2 nodes * 7.9 kW + 0.6 kW switches = 16.4 kW vs 18.0 kW limit (1.6 kW headroom).
      - 3-phase 415V 32A nameplate = sqrt(3) * 415 * 32 / 1000 = 23.00 kW.
      - With 80% continuous-load derating: 23.00 * 0.80 = 18.40 kW continuous capacity per feed.
      - Single-feed failure test: 16.4 kW <= 18.40 kW (passes with ~2.0 kW margin -> Conditional go).
    """
    if nodes_per_rack <= 0 or node_power_kw <= 0 or facility_rack_limit_kw <= 0:
        raise ValueError("nodes_per_rack, node_power_kw, and facility_rack_limit_kw must be positive.")

    total_rack_kw = round(nodes_per_rack * node_power_kw + switch_overhead_kw, 2)
    phase_mult = math.sqrt(3.0) if phases == 3 else 1.0
    nameplate_feed_kw = round((phase_mult * pdu_voltage_v * pdu_current_a) / 1000.0, 2)
    derated_feed_kw = round(nameplate_feed_kw * derating_factor, 2)

    within_facility_limit = total_rack_kw <= facility_rack_limit_kw
    survives_single_feed_loss = total_rack_kw <= derated_feed_kw
    headroom_kw = round(facility_rack_limit_kw - total_rack_kw, 2)
    single_feed_margin_kw = round(derated_feed_kw - total_rack_kw, 2)

    if not within_facility_limit or not survives_single_feed_loss:
        decision = "No-go"
    elif headroom_kw < 3.0 or not has_redundant_compute_nics:
        decision = "Conditional go"
    else:
        decision = "Go"

    return {
        "nodes_per_rack": nodes_per_rack,
        "total_rack_kw": total_rack_kw,
        "facility_limit_kw": facility_rack_limit_kw,
        "facility_headroom_kw": headroom_kw,
        "nameplate_per_feed_kw": nameplate_feed_kw,
        "derated_per_feed_kw": derated_feed_kw,
        "single_feed_margin_kw": single_feed_margin_kw,
        "within_facility_limit": within_facility_limit,
        "survives_single_feed_loss": survives_single_feed_loss,
        "decision": decision,
    }
