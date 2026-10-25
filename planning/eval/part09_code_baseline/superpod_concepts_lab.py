#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.6: DGX SuperPOD concepts: scalable units, fabrics and tiers."""

from __future__ import annotations

import sys

from superpod_concepts import (
    FIVE_NETWORK_SEGMENTS,
    FOUR_PHYSICAL_FABRICS,
    audit_superpod_design_rules,
    calculate_adamw_checkpoint_footprint,
    size_b200_superpod,
    size_gb300_superpod,
    size_superpod_storage_tier,
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

    print("=== Chapter 9.6 Lab: DGX SuperPOD Concepts: Scalable Units, Fabrics & Tiers ===")

    # 1. DGX B200 SuperPOD Scalable Unit & UFM displacement checks (superpod-b200-dc pp. 5, 19)
    b1 = size_b200_superpod(1)
    check(
        "SPB200 p.5/p.19: 1 SU has 31 DGX B200 nodes (248 GPUs, 1 UFM displaced), 8 leaves, 4 spines, 458 kW",
        b1["dgx_b200_nodes"] == 31
        and b1["gpus"] == 248
        and b1["ib_leaf_switches"] == 8
        and b1["ib_spine_switches"] == 4
        and b1["compute_plus_ufm_cables"] == 252
        and b1["spine_leaf_cables"] == 256
        and b1["estimated_power_kw"] == 458,
        f"got {b1}",
    )

    b2 = size_b200_superpod(2)
    check(
        "SPB200 p.19: 2 SUs have 63 DGX B200 nodes (504 GPUs), 16 leaves, 8 spines, 508 compute cables, 512 ISL cables",
        b2["dgx_b200_nodes"] == 63
        and b2["gpus"] == 504
        and b2["ib_leaf_switches"] == 16
        and b2["ib_spine_switches"] == 8
        and b2["compute_plus_ufm_cables"] == 508
        and b2["spine_leaf_cables"] == 512,
    )

    b3 = size_b200_superpod(3)
    check(
        "SPB200 p.19: 3 SUs have 95 DGX B200 nodes (760 GPUs), 24 leaves, 16 spines, 764 compute cables, 768 ISL cables",
        b3["dgx_b200_nodes"] == 95
        and b3["gpus"] == 760
        and b3["ib_leaf_switches"] == 24
        and b3["ib_spine_switches"] == 16,
    )

    b4 = size_b200_superpod(4)
    check(
        "SPB200 p.5/p.19: 4 SUs have 127 DGX B200 nodes (1,016 GPUs), 32 leaves, 16 spines, 1,020 compute cables, 1,024 ISL cables",
        b4["dgx_b200_nodes"] == 127
        and b4["gpus"] == 1016
        and b4["ib_leaf_switches"] == 32
        and b4["ib_spine_switches"] == 16
        and b4["compute_plus_ufm_cables"] == 1020
        and b4["spine_leaf_cables"] == 1024,
    )

    try:
        size_b200_superpod(5)
        check("Rejects unsupported SU count in B200 table", False)
    except ValueError:
        check("Rejects unsupported SU count in B200 table", True)

    # 2. DGX GB300 SuperPOD Scalable Unit & 2-Layer Switch Scaling checks (superpod-gb300-ra Tables 3 & 4)
    g1 = size_gb300_superpod(1)
    check(
        "SPGB300 p.5/p.13: 1 GB300 SU has 8 NVL72 racks, 576 GPUs, 1.2 MW TDP, 8 IB leaves, 4 SN5600 compute leaves",
        g1["racks"] == 8
        and g1["gpus"] == 576
        and g1["tdp_mw"] == 1.2
        and g1["ib_leaf_total"] == 8
        and g1["eth_compute_leaves"] == 4,
    )

    g2 = size_gb300_superpod(2)
    check(
        "SPGB300 Table 3 & 4: 2 SUs (1,152 GPUs) use 16 IB leaves, 8 IB spines, 4 Eth spines, 8 Eth compute leaves, 64x400GbE storage",
        g2["gpus"] == 1152
        and g2["ib_leaf_total"] == 16
        and g2["ib_spine_total"] == 8
        and g2["eth_spines"] == 4
        and g2["max_storage_ports"] == "64x400GbE",
    )

    g4 = size_gb300_superpod(4)
    check(
        "SPGB300 Table 3 & 4: 4 SUs (2,304 GPUs) use 32 IB leaves, 18 IB spines, 8 Eth spines, 16 Eth compute leaves, 128x400GbE storage",
        g4["gpus"] == 2304
        and g4["ib_leaf_total"] == 32
        and g4["ib_spine_total"] == 18
        and g4["eth_spines"] == 8
        and g4["max_storage_ports"] == "128x400GbE",
    )

    g8 = size_gb300_superpod(8)
    check(
        "SPGB300 Table 3 & 4: 8 SUs (4,608 GPUs) use 64 IB leaves, 36 IB spines, 12 Eth spines, 4 Eth storage leaves, 256x400GbE storage",
        g8["gpus"] == 4608
        and g8["ib_leaf_total"] == 64
        and g8["ib_spine_total"] == 36
        and g8["eth_spines"] == 12
        and g8["eth_storage_leaves"] == 4,
    )

    g16 = size_gb300_superpod(16)
    check(
        "SPGB300 Table 3 & 4: 16 SUs (128 racks, 9,216 GPUs) use 128 IB leaves, 72 IB spines, 24 Eth spines, 8 storage leaves, 1024x400GbE",
        g16["racks"] == 128
        and g16["gpus"] == 9216
        and g16["ib_leaf_total"] == 128
        and g16["ib_spine_total"] == 72
        and g16["eth_spines"] == 24
        and g16["eth_storage_leaves"] == 8
        and g16["max_storage_ports"] == "1024x400GbE",
    )

    # 3. Five Network Segments across Four Physical Fabrics checks (superpod-gb300-ra p. 18)
    check(
        "SPGB300 p.18: SuperPOD defines 5 logical network segments carried across 4 physical fabrics",
        len(FIVE_NETWORK_SEGMENTS) == 5 and len(FOUR_PHYSICAL_FABRICS) == 4,
    )

    # 4. Standard vs Enhanced Storage Tier checks (superpod-gb300-ra Table 5 p. 31)
    st_1 = size_superpod_storage_tier(1, "Standard")
    check(
        "SPGB300 Table 5: 1 SU Standard storage tier is 90 GB/s read and 45 GB/s write (2:1 ratio)",
        st_1["aggregate_read_gbps"] == 90.0
        and st_1["aggregate_write_gbps"] == 45.0
        and st_1["read_to_write_ratio"] == 2.0,
    )

    st_4 = size_superpod_storage_tier(4, "Standard")
    check(
        "SPGB300 Table 5: 4 SU Standard storage tier is 360 GB/s read and 180 GB/s write",
        st_4["aggregate_read_gbps"] == 360.0 and st_4["aggregate_write_gbps"] == 180.0,
    )

    en_1 = size_superpod_storage_tier(1, "Enhanced")
    check(
        "SPGB300 Table 5: 1 SU Enhanced storage tier is 280 GB/s read and 140 GB/s write",
        en_1["aggregate_read_gbps"] == 280.0 and en_1["aggregate_write_gbps"] == 140.0,
    )

    en_4 = size_superpod_storage_tier(4, "Enhanced")
    check(
        "SPGB300 Table 5: 4 SU Enhanced storage tier is 1,120 GB/s read and 560 GB/s write",
        en_4["aggregate_read_gbps"] == 1120.0 and en_4["aggregate_write_gbps"] == 560.0,
    )

    try:
        size_superpod_storage_tier(1, "Ultra")
        check("Rejects unknown storage tier name", False)
    except ValueError:
        check("Rejects unknown storage tier name", True)

    # 5. V21 Ch 4 Mixed-Precision AdamW Checkpoint Sizing checks
    ckpt_70b = calculate_adamw_checkpoint_footprint(
        params_billions=70.0,
        num_gpus=64,
        gpus_per_node=8,
        shared_storage_write_gbps=10.0,
        local_nvme_write_gbps_per_node=15.0,
    )
    check(
        "V21 Ch4: 70B AdamW checkpoint (14 B/param) == 980.0 GB; active training state (16 B/param) == 1,120.0 GB",
        ckpt_70b["checkpoint_total_gb"] == 980.0
        and ckpt_70b["training_state_total_gb"] == 1120.0,
        f"got {ckpt_70b}",
    )
    check(
        "V21 Ch4: 70B FSDP/ZeRO-3 shard across 64 GPUs == 15.31 GB/GPU and 122.48 GB per 8-GPU node",
        ckpt_70b["per_gpu_shard_gb"] == 15.31 and ckpt_70b["per_node_shard_gb"] == 122.48,
        f"got {ckpt_70b}",
    )
    check(
        "V21 Ch4: Local NVMe staging takes 8.17 s (at 15 GB/s/node) vs 98.0 s direct to 10 GB/s NAS",
        ckpt_70b["local_nvme_stage_sec"] == 8.17 and ckpt_70b["shared_storage_write_sec"] == 98.0,
        f"got {ckpt_70b}",
    )

    # 6. SuperPOD Design Rule Auditor checks (SPB200 & SPGB300)
    clean_pod = {
        "datacenter_tier": 3,
        "is_partial_su": True,
        "full_su_switches_and_isl_provisioned": True,
        "roce_storage_bonded_with_inband": False,
        "infiniband_uses_patch_panels": False,
        "unrelated_it_gear_in_dgx_racks": False,
    }
    check(
        "Compliant SuperPOD design passes all reference architecture rules",
        audit_superpod_design_rules(clean_pod)["compliant"] is True,
    )

    bad_tier = dict(clean_pod, datacenter_tier=2)
    check(
        "SPGB300 p.5: Flags data center below Tier 3 / Rated 3 / Class 3",
        any("datacenter_below_tier3" in v for v in audit_superpod_design_rules(bad_tier)["violations"]),
    )

    bad_partial = dict(clean_pod, is_partial_su=True, full_su_switches_and_isl_provisioned=False)
    check(
        "SPGB300 p.18: Flags partial-SU deployment that omits full-SU leaf switches and leaf-spine cables",
        any("partial_su_fabric_underprovisioned" in v for v in audit_superpod_design_rules(bad_partial)["violations"]),
    )

    bad_bond = dict(clean_pod, roce_storage_bonded_with_inband=True)
    check(
        "SPGB300 p.24: Flags bonding RoCEv2 storage traffic with In-Band management traffic",
        any("roce_bonded_with_inband" in v for v in audit_superpod_design_rules(bad_bond)["violations"]),
    )

    bad_patch = dict(clean_pod, infiniband_uses_patch_panels=True)
    check(
        "SPB200 p.23 FAQ #2: Flags using patch panels to extend InfiniBand cable runs",
        any("infiniband_patch_panel_violation" in v for v in audit_superpod_design_rules(bad_patch)["violations"]),
    )

    bad_cohab = dict(clean_pod, unrelated_it_gear_in_dgx_racks=True)
    check(
        "SPB200 p.23 FAQ #5: Flags placing unrelated IT equipment in DGX racks or cooling gaps",
        any("unrelated_equipment_cohabitation" in v for v in audit_superpod_design_rules(bad_cohab)["violations"]),
    )

    # 7. Additional numerical & boundary checks
    check(
        "SPB200 cable formula: N_nodes * 8 compute ports + 4 UFM ports == compute_plus_ufm_cables across 1..4 SUs",
        all(
            size_b200_superpod(su)["dgx_b200_nodes"] * 8 + 4
            == size_b200_superpod(su)["compute_plus_ufm_cables"]
            for su in (1, 2, 3, 4)
        ),
    )
    check(
        "SPB200 spine-leaf cable formula: N_su * 256 == spine_leaf_cables across 1..4 SUs",
        all(
            su * 256 == size_b200_superpod(su)["spine_leaf_cables"]
            for su in (1, 2, 3, 4)
        ),
    )
    check(
        "SPGB300 16 SUs (9,216 GPUs) total thermal design power == 19.2 MW",
        g16["tdp_mw"] == 19.2,
    )
    try:
        size_gb300_superpod(3)
        check("Rejects non-standard SU count (3) in GB300 table", False)
    except ValueError:
        check("Rejects non-standard SU count (3) in GB300 table", True)

    try:
        calculate_adamw_checkpoint_footprint(0.0, 64)
        check("Rejects non-positive params_billions in checkpoint calculator", False)
    except ValueError:
        check("Rejects non-positive params_billions in checkpoint calculator", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
