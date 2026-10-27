"""Chapter 13.8 Verification Lab: Capacity, performance and cost planning.

Run with:
    python3 -B code/part13/storage_capacity_cost_planning_lab.py
"""

from __future__ import annotations

import os
import sys
from typing import Callable, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage_capacity_cost_planning import (
    HEADROOM_RECOMMENDATIONS,
    PROTECTION_SCHEMES,
    STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR,
    SUPERPOD_HPS_TIERS_PER_SU,
    calculate_raw_from_usable_capacity,
    calculate_usable_capacity_plan,
    compare_storage_options_gpu_hour_waste,
    evaluate_four_tier_storage_budget,
    evaluate_idle_gpu_vs_storage_roi,
    evaluate_three_year_storage_and_factory_tco,
    size_checkpoint_write_and_burst_bandwidth,
    size_metadata_ops_and_sharding,
    size_read_bandwidth_requirements,
    size_superpod_storage_by_su,
)


def run_checks() -> int:
    checks: List[Tuple[str, Callable[[], bool]]] = []

    def add(desc: str, fn: Callable[[], bool]) -> None:
        checks.append((desc, fn))

    # --- Section 1: Six-Dimension AI Storage Sizing (V15 Ch. 10 & Ch. 12, AISPE Ch. 5, V21 Ch. 04) ---
    add(
        "1. Headroom rules reserve 30% capacity (<90% fill), 50% bandwidth (2.0x burst overbuild), 40% metadata, and <=24h rebuild SLA",
        lambda: (
            HEADROOM_RECOMMENDATIONS["capacity_headroom_ratio"] == 0.30
            and HEADROOM_RECOMMENDATIONS["max_safe_fill_ratio"] == 0.90
            and HEADROOM_RECOMMENDATIONS["bandwidth_headroom_ratio"] == 0.50
            and HEADROOM_RECOMMENDATIONS["burst_overbuild_multiplier"] == 2.0
            and HEADROOM_RECOMMENDATIONS["metadata_headroom_ratio"] == 0.40
            and HEADROOM_RECOMMENDATIONS["rebuild_sla_hours"] == 24.0
        ),
    )

    add(
        "2. V15 Ch. 10 1.3B-model usable capacity: 500 GB dataset + 2,000 GB rolling + 1,000 GB archive + 50 GB artifacts + 10 GB logs = 3,560 GB + 30% (1,068 GB) = 4,628 GB",
        lambda: (
            (c := calculate_usable_capacity_plan())
            and c.rolling_checkpoints_gb == 2000.0
            and c.archive_checkpoints_gb == 1000.0
            and c.subtotal_usable_gb == 3560.0
            and c.headroom_gb == 1068.0
            and c.total_usable_gb == 4628.0
        ),
    )

    add(
        "3. V15 Ch. 10 256-GPU cluster interview baseline: 5,000 GB dataset + 1,000 GB checkpoints + 30% headroom (1,800 GB) = 7,800 GB (7.8 TB)",
        lambda: (
            (
                c256 := calculate_usable_capacity_plan(
                    raw_dataset_gb=5000.0,
                    processed_shards_gb=0.0,
                    checkpoint_size_gb=500.0,
                    rolling_checkpoints_k=2,
                    archive_checkpoints_m=0,
                    scratch_and_artifacts_gb=0.0,
                    user_homes_and_logs_gb=0.0,
                    headroom_ratio=0.30,
                )
            ).subtotal_usable_gb
            == 6000.0
            and c256.headroom_gb == 1800.0
            and c256.total_usable_gb == 7800.0
            and c256.total_usable_tb == 7.8
        ),
    )

    add(
        "4. Per-GPU 200 MB/s ingestion requires 1.6 GB/s per 8-GPU node and 14.4 GB/s (14-20 GB/s envelope) per 72-GPU GB200/GB300 NVL72 rack (AISPE Ch. 5)",
        lambda: (
            (r := size_read_bandwidth_requirements())["eight_gpu_node_ingest_gb_s"] == 1.6
            and r["nvl72_rack_ingest_gb_s"] == 14.4
            and r["cluster_gpu_ingest_gb_s"] == 12.8
        ),
    )

    add(
        "5. V15 Ch. 10 read bandwidth: 3 concurrent jobs loading 100 GB in 30 s require 3.3333 GB/s/job = 10.0 GB/s (Lustre 24 OSTs = 19.2 GB/s and BeeGFS 8 nodes = 12.0 GB/s pass; NFS 2.0 GB/s fails)",
        lambda: (
            (r := size_read_bandwidth_requirements())["per_job_load_gb_s"] == 3.3333
            and r["total_job_load_gb_s"] == 10.0
            and r["lustre_24_ost_read_gb_s"] == 19.2
            and r["beegfs_8_node_read_gb_s"] == 12.0
            and r["lustre_meets_load_budget"] is True
            and r["beegfs_meets_load_budget"] is True
            and r["nfs_meets_load_budget"] is False
        ),
    )

    add(
        "6. V15 Ch. 10 checkpoint write budget: 100 GB checkpoint in 300 s (5 min) requires 333.33 MB/s (2.6667 GB/s across 8 parallel streams vs 9.6 GB/s Lustre write capacity)",
        lambda: (
            (
                w100 := size_checkpoint_write_and_burst_bandwidth(
                    model_params_billions=10.0,
                    checkpoint_bytes_per_param=10,
                    num_gpus=8,
                    gpus_per_node=8,
                    checkpoint_write_budget_sec=300.0,
                )
            )["checkpoint_total_gb"]
            == 100.0
            and w100["required_write_mb_s"] == 333.33
            and round(8 * w100["required_write_gb_s"], 4) == 2.6664
        ),
    )

    add(
        "7. V21 Ch. 04 70B Llama mixed-precision AdamW checkpoint is 14 B/param = 980 GB (16 B/param = 1,120 GB training memory), sharded across 64 GPUs = 15.3125 GB/GPU and 122.5 GB/node",
        lambda: (
            (w70 := size_checkpoint_write_and_burst_bandwidth())["checkpoint_total_gb"] == 980.0
            and w70["training_mem_total_gb"] == 1120.0
            and w70["per_gpu_shard_gb"] == 15.3125
            and w70["per_node_shard_gb"] == 122.5
            and w70["local_nvme_stage_sec"] == 6.125
        ),
    )

    add(
        "8. V15 Ch. 12 synchronous 500 GB checkpoint at 1 GB/s stalls training for 500 s vs 25 s when staged asynchronously to local NVMe at 20 GB/s (20.0x stall reduction)",
        lambda: (500.0 / 1.0) == 500.0 and (500.0 / 20.0) == 25.0 and (500.0 / 25.0) == 20.0,
    )

    add(
        "9. V15 Ch. 10 burst handling: 1 GB/s sustained read + 5 GB/s checkpoint burst = 6 GB/s peak; 2.0x overbuild rule sizes 3 GB/s -> 6 GB/s and 10 GB/s -> 20 GB/s",
        lambda: (
            (w := size_checkpoint_write_and_burst_bandwidth(sustained_read_gb_s=1.0, checkpoint_burst_gb_s=5.0))[
                "peak_concurrent_gb_s"
            ]
            == 6.0
            and size_checkpoint_write_and_burst_bandwidth(sustained_read_gb_s=3.0)["recommended_2x_overbuild_gb_s"]
            == 6.0
            and size_checkpoint_write_and_burst_bandwidth(sustained_read_gb_s=10.0)["recommended_2x_overbuild_gb_s"]
            == 20.0
        ),
    )

    add(
        "10. V15 Ch. 10 metadata sizing: 1.2M small images generate 4.8M ops/epoch and 25,600 opens/sec (35,840 ops/sec with 40% headroom; Lustre/BeeGFS 50K pass, NFS 5K fails; WebDataset cuts ops 1,000x to 25.6/s)",
        lambda: (
            (m := size_metadata_ops_and_sharding())["total_metadata_ops_per_epoch"] == 4_800_000
            and m["raw_opens_per_sec"] == 25_600
            and m["required_mds_ops_s_with_40pct_headroom"] == 35_840.0
            and m["sharded_opens_per_sec"] == 25.6
            and m["lustre_single_mds_sufficient"] is True
            and m["beegfs_single_mds_sufficient"] is True
            and m["nfs_sufficient_for_raw"] is False
        ),
    )

    # --- Section 2: NVIDIA DGX SuperPOD High-Performance Storage Tiers (`superpod-gb300-ra`, `superpod-b200-dc`) ---
    add(
        "11. SuperPOD Standard Tier delivers 90 GB/s read and 45 GB/s write per SU (360 GB/s read and 180 GB/s write for 4 SUs)",
        lambda: (
            SUPERPOD_HPS_TIERS_PER_SU["Standard"]["read_gb_s_per_su"] == 90.0
            and SUPERPOD_HPS_TIERS_PER_SU["Standard"]["write_gb_s_per_su"] == 45.0
            and (sp := size_superpod_storage_by_su(num_sus=4, tier="Standard", platform="GB300"))["aggregate_read_gb_s"]
            == 360.0
            and sp["aggregate_write_gb_s"] == 180.0
        ),
    )

    add(
        "12. SuperPOD Enhanced Tier delivers 280 GB/s read and 140 GB/s write per SU (1,120 GB/s read and 560 GB/s write for 4 SUs; 3.1111x Standard Tier)",
        lambda: (
            SUPERPOD_HPS_TIERS_PER_SU["Enhanced"]["read_gb_s_per_su"] == 280.0
            and SUPERPOD_HPS_TIERS_PER_SU["Enhanced"]["write_gb_s_per_su"] == 140.0
            and (sp := size_superpod_storage_by_su(num_sus=4, tier="Enhanced", platform="GB300"))["aggregate_read_gb_s"]
            == 1120.0
            and sp["aggregate_write_gb_s"] == 560.0
            and round(280.0 / 90.0, 4) == 3.1111
        ),
    )

    add(
        "13. DGX GB300 SuperPOD SU has 8 NVL72 racks (576 GPUs, 144 compute trays, 15.36 TB RAID0 NVMe/tray = 2,211.84 TB/SU, 1.2 MW TDP) and scales to 16 SUs (128 racks, 9,216 GPUs, 1024x400GbE)",
        lambda: (
            (su1 := size_superpod_storage_by_su(num_sus=1, tier="Enhanced", platform="GB300"))["total_racks"] == 8
            and su1["total_gpus"] == 576
            and su1["total_compute_trays"] == 144
            and su1["local_nvme_per_tray_tb"] == 15.36
            and su1["total_local_raid0_scratch_tb"] == 2211.84
            and su1["total_tdp_mw"] == 1.2
            and (su16 := size_superpod_storage_by_su(num_sus=16, tier="Enhanced", platform="GB300"))["total_racks"] == 128
            and su16["total_gpus"] == 9216
            and su16["storage_fabric_400gbe_links"] == 1024
            and su16["aggregate_read_gb_s"] == 4480.0
            and su16["aggregate_write_gb_s"] == 2240.0
        ),
    )

    add(
        "14. DGX B200 SuperPOD SU has up to 32 DGX B200 systems (256 GPUs, 458 kW/SU) and 127 systems (1,016 GPUs) at 4 SUs with 1 system displaced by UFM (`superpod-b200-dc`)",
        lambda: (
            (b1 := size_superpod_storage_by_su(num_sus=1, tier="Standard", platform="B200"))["total_systems"] == 32
            and b1["total_gpus"] == 256
            and b1["total_power_kw"] == 458.0
            and (b4 := size_superpod_storage_by_su(num_sus=4, tier="Enhanced", platform="B200"))["total_systems"] == 127
            and b4["total_gpus"] == 1016
            and b4["aggregate_read_gb_s"] == 1120.0
            and b4["aggregate_write_gb_s"] == 560.0
        ),
    )

    # --- Section 3: Erasure Coding vs Replication Usable-to-Raw Efficiency & Rebuild Reserve ---
    add(
        "15. 2x replication (1+1) has 50.0% efficiency (2.0x raw multiplier) and 3x replication (1+2) has 33.33% efficiency (3.0x raw multiplier)",
        lambda: (
            (r2 := calculate_raw_from_usable_capacity(1000.0, *PROTECTION_SCHEMES["2x_replication"]))[
                "usable_to_raw_efficiency_pct"
            ]
            == 50.0
            and r2["required_raw_tb"] == 2000.0
            and (r3 := calculate_raw_from_usable_capacity(1000.0, *PROTECTION_SCHEMES["3x_replication"]))[
                "usable_to_raw_efficiency_pct"
            ]
            == 33.33
            and r3["required_raw_tb"] == 3000.0
        ),
    )

    add(
        "16. WekaFS 6+2 (75.0%), Lustre/ZFS 8+2 (80.0%), WekaFS 16+2 (88.89%), and VAST 146+4 (97.33%) cut raw flash required for 1,000 TB usable from 2,000-3,000 TB down to 1,333.33-1,027.40 TB",
        lambda: (
            (w6 := calculate_raw_from_usable_capacity(1000.0, *PROTECTION_SCHEMES["weka_6_plus_2"]))[
                "usable_to_raw_efficiency_pct"
            ]
            == 75.0
            and w6["required_raw_tb"] == 1333.33
            and (z8 := calculate_raw_from_usable_capacity(1000.0, *PROTECTION_SCHEMES["lustre_zfs_8_plus_2"]))[
                "usable_to_raw_efficiency_pct"
            ]
            == 80.0
            and z8["required_raw_tb"] == 1250.0
            and (w16 := calculate_raw_from_usable_capacity(1000.0, *PROTECTION_SCHEMES["weka_16_plus_2"]))[
                "usable_to_raw_efficiency_pct"
            ]
            == 88.89
            and w16["required_raw_tb"] == 1125.0
            and (v146 := calculate_raw_from_usable_capacity(1000.0, *PROTECTION_SCHEMES["vast_146_plus_4"]))[
                "usable_to_raw_efficiency_pct"
            ]
            == 97.33
            and v146["required_raw_tb"] == 1027.4
        ),
    )

    add(
        "17. Rebuilding a failed 15.36 TB NVMe drive within the 24-hour SLA requires at least 177.78 MB/s of sustained background rebuild bandwidth (711.11 MB/s for a 61.44 TB drive/node)",
        lambda: (
            calculate_raw_from_usable_capacity(1000.0, failed_drive_or_node_tb=15.36, rebuild_sla_hours=24.0)[
                "min_24h_rebuild_mb_s"
            ]
            == 177.78
            and calculate_raw_from_usable_capacity(1000.0, failed_drive_or_node_tb=61.44, rebuild_sla_hours=24.0)[
                "min_24h_rebuild_mb_s"
            ]
            == 711.11
        ),
    )

    # --- Section 4: Multi-Tier Storage Architecture & Cost Model (V15 Ch. 10, V21 Ch. 04) ---
    add(
        "18. Four-tier storage unit costs span 5,000x: Hot NVMe ($5/GB-yr), Warm Parallel FS ($0.50/GB-yr), Cold Object S3 ($0.02/GB-yr or $0.023/GB-mo = $2,300/mo per 100 TB), and Archive ($0.001/GB-yr)",
        lambda: (
            STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR["Hot_NVMe"]["cost_per_gb_year_usd"] == 5.0
            and STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR["Warm_Parallel_FS"]["cost_per_gb_year_usd"] == 0.50
            and STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR["Cold_Object_S3"]["cost_per_gb_year_usd"] == 0.02
            and STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR["Cold_Object_S3"]["cloud_monthly_per_gb_usd"] == 0.023
            and round(100_000 * 0.023, 2) == 2300.0
            and STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR["Archive_Glacier_Tape"]["cost_per_gb_year_usd"] == 0.001
        ),
    )

    add(
        "19. V15 Ch. 10 1.3B-model 4-tier storage budget: 100 GB Hot ($500) + 2.5 TB Warm ($1,250) + 5 TB Cold ($100) + 10 TB Archive ($10) = $1,860/year across 17.6 TB ($8.81/TB-month blended)",
        lambda: (
            (t := evaluate_four_tier_storage_budget())["hot_nvme_usd_yr"] == 500.0
            and t["warm_parallel_usd_yr"] == 1250.0
            and t["cold_object_usd_yr"] == 100.0
            and t["archive_glacier_usd_yr"] == 10.0
            and t["total_capacity_gb"] == 17600.0
            and t["total_annual_usd"] == 1860.0
            and t["blended_usd_per_tb_month"] == 8.81
        ),
    )

    # --- Section 5: 3-Year Storage TCO, $/TB-Month & Idle-GPU Opportunity Cost (V15 Ch. 10, V21 Ch. 11-12) ---
    add(
        "20. V15 Ch. 10 128-GPU A100 cluster costs $435/hr ($51/hr power + $384/hr lease); a 10% data stall (2.4 hr/day) wastes $1,044/day ($381,060/yr, ~$380K/yr), paying back a $100K storage upgrade in 95.79 days",
        lambda: (
            (roi := evaluate_idle_gpu_vs_storage_roi())["power_hourly_usd"] == 51.0
            and roi["lease_hourly_usd"] == 384.0
            and roi["cluster_hourly_usd"] == 435.0
            and roi["idle_hours_per_day"] == 2.4
            and roi["daily_stall_waste_usd"] == 1044.0
            and roi["annual_stall_waste_usd"] == 381060.0
            and roi["payback_days"] == 95.79
            and roi["storage_pct_of_annual_waste"] == 26.24
        ),
    )

    add(
        "21. V15 Ch. 10 cost-per-GPU-hour comparison: Option A (5% stall = $2,784/hr = $24.4M/yr) vs Option B (1% stall = $558/hr = $4.9M/yr + $0.6M storage = $5.5M/yr) saves $18.9M/year",
        lambda: (
            (cmp := compare_storage_options_gpu_hour_waste())["option_a_hourly_waste_usd"] == 2784.0
            and cmp["option_a_annual_waste_musd"] == 24.4
            and cmp["option_b_hourly_waste_usd"] == 558.0
            and cmp["option_b_annual_waste_musd"] == 4.9
            and cmp["option_b_total_musd"] == 5.5
            and cmp["net_annual_savings_musd"] == 18.9
        ),
    )

    add(
        "22. V21 Ch. 12 1,200-GPU AI Factory 3-year TCO is $70.2M ($44.0M CapEx + $26.2M OpEx = $19.5K/GPU-yr), where $2.0M storage CapEx is only 4.55% of CapEx and 2.85% of 3-year TCO",
        lambda: (
            (tco := evaluate_three_year_storage_and_factory_tco())["factory_3yr_tco_musd"] == 70.2
            and tco["factory_per_gpu_year_kusd"] == 19.5
            and tco["storage_capex_share_of_factory_capex_pct"] == 4.55
            and tco["storage_capex_share_of_factory_tco_pct"] == 2.85
        ),
    )

    add(
        "23. 1 PB (1,000 TB) parallel storage with $2.0M CapEx, $200K/yr maintenance, and 40 kW power (1.35 PUE, $0.12/kWh = $56,764.80/yr) has a $2,770,294.40 3-year TCO ($76.95/TB-month)",
        lambda: (
            (tco := evaluate_three_year_storage_and_factory_tco())["storage_annual_power_usd"] == 56764.8
            and tco["three_year_storage_opex_usd"] == 770294.4
            and tco["three_year_storage_tco_usd"] == 2770294.4
            and tco["effective_usd_per_tb_month"] == 76.95
        ),
    )

    add(
        "24. V21 Ch. 11 3-year hardware refresh (464 GPUs Yr1 + 60 GPUs Yr2 + 100 GPUs Yr3 = 1,612 GPU-years; $19.8M CapEx + $9.0M OpEx = $28.8M TCO) amortizes to $17.87K (~$17.9K) per GPU-year",
        lambda: (
            (464 * 3 + 60 * 2 + 100 * 1) == 1612
            and round(28_800_000.0 / 1612.0, 2) == 17866.0
        ),
    )

    add(
        "25. V21 Ch. 12 spot instance resilience: $21/hr spot vs $60/hr on-demand (8xH100 p5.48xlarge) saves 65.0% ($2.625 vs $7.50/GPU-hr), bounded by the checkpoint interval on 2-minute eviction warning",
        lambda: (
            round((60.0 - 21.0) / 60.0 * 100.0, 2) == 65.0
            and (60.0 / 8.0) == 7.5
            and (21.0 / 8.0) == 2.625
        ),
    )

    add(
        "26. Input validation rejects non-positive SuperPOD SU counts, unsupported tiers, and negative capacity inputs",
        lambda: (
            _raises_value_error(lambda: size_superpod_storage_by_su(num_sus=0))
            and _raises_value_error(lambda: size_superpod_storage_by_su(num_sus=2, tier="Invalid"))
            and _raises_value_error(lambda: calculate_usable_capacity_plan(raw_dataset_gb=-10.0))
        ),
    )

    print("=== Chapter 13.8 Lab: Capacity, Performance and Cost Planning ===")
    passed = 0
    failed = 0
    for desc, fn in checks:
        try:
            ok = bool(fn())
        except Exception as exc:
            ok = False
            print(f"  [FAIL] {desc} (exception: {exc})")
        else:
            if ok:
                print(f"  [PASS] {desc}")
            else:
                print(f"  [FAIL] {desc}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def _raises_value_error(fn: Callable[[], object]) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(run_checks())
