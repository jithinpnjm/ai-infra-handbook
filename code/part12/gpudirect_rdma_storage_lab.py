"""Self-checking verification lab for Chapter 12.19: GPUDirect RDMA & GPUDirect Storage.

Run with:
    python3 -B code/part12/gpudirect_rdma_storage_lab.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpudirect_rdma_storage import (
    CUFILE_EXPECTED_LIFECYCLE,
    NCCL_PATH_DISTANCE,
    audit_cufile_json,
    compare_bounce_buffer_vs_gdr,
    evaluate_gdr_kernel_backend,
    evaluate_nccl_gdr_level,
    parse_lspci_acs_output,
    pcie_gen_bandwidth_gb_s,
     simulate_gdsio_benchmark,
    size_checkpoint_and_metadata,
)


def run_lab() -> int:
    passed = 0
    failed = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name} :: {detail}")

    print("=== Chapter 12.19 Lab: GPUDirect RDMA and GPUDirect Storage ===")

    # 1. Host bounce-buffer vs GPUDirect RDMA (400G NDR = 50 GB/s vs ~50 Gbps = 6.25 GB/s staged)
    cmp_400g = compare_bounce_buffer_vs_gdr(
        payload_gb=10.0,
        nic_rate_gbps=400.0,
        pcie_link_gb_s=64.0,
        host_dram_per_channel_gb_s=12.5,
    )
    check(
        "1. Staged path traverses 2 PCIe hops and 2 DRAM ops per node",
        cmp_400g.staged_pcie_hops_per_node == 2 and cmp_400g.staged_dram_ops_per_node == 2,
        f"got {cmp_400g}",
    )
    check(
        "2. GPUDirect RDMA traverses 1 PCIe switch hop and 0 DRAM ops per node",
        cmp_400g.gdr_pcie_hops_per_node == 1 and cmp_400g.gdr_dram_ops_per_node == 0,
        f"got {cmp_400g}",
    )
    check(
        "3. 400G NIC achieves 50.0 GB/s with GDR vs 6.25 GB/s (50 Gbps) host-staged (8.0x speedup)",
        cmp_400g.gdr_effective_gb_s == 50.0
        and cmp_400g.staged_effective_gb_s == 6.25
        and cmp_400g.speedup_factor == 8.0,
        f"got {cmp_400g}",
    )
    check(
        "4. 10 GB payload generates 20.0 GB PCIe + 20.0 GB DRAM traffic per node when staged vs 10.0 GB PCIe + 0.0 GB DRAM with GDR",
        cmp_400g.staged_pcie_volume_gb_per_node == 20.0
        and cmp_400g.staged_dram_volume_gb_per_node == 20.0
        and cmp_400g.gdr_pcie_volume_gb_per_node == 10.0
        and cmp_400g.gdr_dram_volume_gb_per_node == 0.0,
        f"got {cmp_400g}",
    )

    # 2. PCIe generation bandwidth checks
    gt4, bw4 = pcie_gen_bandwidth_gb_s(4, 16)
    gt5, bw5 = pcie_gen_bandwidth_gb_s(5, 16)
    gt6, bw6 = pcie_gen_bandwidth_gb_s(6, 16)
    check(
        "5. PCIe Gen4 x16 = 16 GT/s (31.51 GB/s) and PCIe Gen5 x16 = 32 GT/s (63.02 GB/s)",
        gt4 == 16.0 and bw4 == 31.51 and gt5 == 32.0 and bw5 == 63.02 and gt6 == 64.0 and bw6 == 121.0,
        f"got Gen4=({gt4},{bw4}), Gen5=({gt5},{bw5}), Gen6=({gt6},{bw6})",
    )

    # 3. Kernel memory registration backends: dma-buf vs nvidia-peermem vs fallback
    el_dmabuf = evaluate_gdr_kernel_backend(
        kernel_major=5,
        kernel_minor=15,
        is_open_gpu_kmod=True,
        rdma_core_version=44,
        peermem_loaded=False,
        large_bar1_enabled=True,
    )
    check(
        "6. Linux kernel 5.15 (>= 5.12) + OpenRM + rdma-core 44 (>= 34) selects dma-buf without nvidia-peermem",
        el_dmabuf.mode == "dma-buf" and el_dmabuf.gdr_supported is True,
        f"got {el_dmabuf}",
    )

    el_peermem = evaluate_gdr_kernel_backend(
        kernel_major=5,
        kernel_minor=4,
        is_open_gpu_kmod=False,
        rdma_core_version=32,
        peermem_loaded=True,
        large_bar1_enabled=True,
    )
    check(
        "7. Proprietary driver on kernel 5.4 with nvidia-peermem loaded selects nvidia-peermem",
        el_peermem.mode == "nvidia-peermem" and el_peermem.gdr_supported is True,
        f"got {el_peermem}",
    )

    el_nobar = evaluate_gdr_kernel_backend(
        kernel_major=6,
        kernel_minor=8,
        is_open_gpu_kmod=True,
        rdma_core_version=50,
        peermem_loaded=True,
        large_bar1_enabled=False,
    )
    check(
        "8. Disabled Large BAR1 / Above 4G Decoding forces host-staging-fallback even when drivers are loaded",
        el_nobar.mode == "host-staging-fallback" and el_nobar.gdr_supported is False,
        f"got {el_nobar}",
    )

    el_nomod = evaluate_gdr_kernel_backend(
        kernel_major=5,
        kernel_minor=15,
        is_open_gpu_kmod=False,
        rdma_core_version=44,
        peermem_loaded=False,
        large_bar1_enabled=True,
    )
    check(
        "9. Proprietary GPU driver without nvidia-peermem cannot use dma-buf and falls back to host staging",
        el_nomod.mode == "host-staging-fallback" and el_nomod.gdr_supported is False,
        f"got {el_nomod}",
    )

    # 4. NCCL_NET_GDR_LEVEL distance ordering and cutoff behavior
    check(
        "10. NCCL path hierarchy orders LOC(0) < PIX(1) < PXB(2) < PHB(3) < NODE(4) < SYS(5)",
        [NCCL_PATH_DISTANCE[k] for k in ("LOC", "PIX", "PXB", "PHB", "NODE", "SYS")] == [0, 1, 2, 3, 4, 5],
        f"got {NCCL_PATH_DISTANCE}",
    )

    d_pix = evaluate_nccl_gdr_level("PIX", gdr_level_cutoff="PXB", acs_enabled=False)
    check(
        "11. PIX path with default PXB cutoff and ACS off enables both GDR Write and GDR Read",
        d_pix.gdr_write_enabled is True
        and d_pix.gdr_read_enabled is True
        and d_pix.effective_path == "PIX",
        f"got {d_pix}",
    )

    d_pxb = evaluate_nccl_gdr_level("PXB", gdr_level_cutoff="PXB", acs_enabled=False)
    check(
        "12. PXB path with PXB cutoff enables both GDR Write and GDR Read",
        d_pxb.gdr_write_enabled is True and d_pxb.gdr_read_enabled is True,
        f"got {d_pxb}",
    )

    d_phb_default = evaluate_nccl_gdr_level("PHB", gdr_level_cutoff="PXB", acs_enabled=False)
    check(
        "13. PHB path exceeds PXB cutoff and disables GDR by default",
        d_phb_default.gdr_write_enabled is False and d_phb_default.gdr_read_enabled is False,
        f"got {d_phb_default}",
    )

    d_phb_raised = evaluate_nccl_gdr_level("PHB", gdr_level_cutoff="PHB", acs_enabled=False)
    check(
        "14. Raising NCCL_NET_GDR_LEVEL=PHB enables GDR Write on PHB but keeps GDR Read off by default",
        d_phb_raised.gdr_write_enabled is True and d_phb_raised.gdr_read_enabled is False,
        f"got {d_phb_raised}",
    )

    d_phb_forced_read = evaluate_nccl_gdr_level(
        "PHB", gdr_level_cutoff="PHB", gdr_read_env=1, acs_enabled=False
    )
    check(
        "15. Setting NCCL_NET_GDR_READ=1 explicitly forces GDR Read on PHB",
        d_phb_forced_read.gdr_write_enabled is True and d_phb_forced_read.gdr_read_enabled is True,
        f"got {d_phb_forced_read}",
    )

    d_sys = evaluate_nccl_gdr_level("SYS", gdr_level_cutoff="PHB", acs_enabled=False)
    check(
        "16. Cross-socket SYS path (UPI/QPI) disables GDR under PHB cutoff",
        d_sys.gdr_write_enabled is False and d_sys.gdr_read_enabled is False,
        f"got {d_sys}",
    )

    # 5. PCIe ACS P2P trap and setpci remediation
    d_acs_trap = evaluate_nccl_gdr_level("PIX", gdr_level_cutoff="PXB", acs_enabled=True)
    check(
        "17. PCIe ACS enabled on a PIX switch redirects traffic to PHB and disables GDR under PXB cutoff",
        d_acs_trap.effective_path == "PHB"
        and d_acs_trap.gdr_write_enabled is False
        and d_acs_trap.gdr_read_enabled is False,
        f"got {d_acs_trap}",
    )

    acs_scan = parse_lspci_acs_output(
        {
            "0000:16:00.0": "ACSCtl: SrcValid+ TransBlk- ReqRedir+ CmpltRedir+ UpstreamFwd+ EgressCtrl- DirectTrans-",
            "0000:64:00.0": "ACSCtl: SrcValid- TransBlk- ReqRedir- CmpltRedir- UpstreamFwd- EgressCtrl- DirectTrans-",
        }
    )
    check(
        "18. ACS parser flags SrcValid+/ReqRedir+/CmpltRedir+ on 0000:16:00.0 and emits setpci ECAP_ACS+0x6.w=0000",
        acs_scan[0].has_blocking_bits is True
        and "SrcValid+" in acs_scan[0].blocking_flags
        and "ReqRedir+" in acs_scan[0].blocking_flags
        and "CmpltRedir+" in acs_scan[0].blocking_flags
        and acs_scan[0].setpci_fix_cmd == "setpci -s 0000:16:00.0 ECAP_ACS+0x6.w=0000",
        f"got {acs_scan[0]}",
    )
    check(
        "19. ACS parser marks 0000:64:00.0 clean when all ACSCtl bits are '-' (disabled)",
        acs_scan[1].has_blocking_bits is False and len(acs_scan[1].blocking_flags) == 0,
        f"got {acs_scan[1]}",
    )

    # 6. GPUDirect Storage (GDS): cuFile lifecycle, gdsio Table 5-1, /etc/cufile.json, & sizing
    check(
        "20. cuFile API lifecycle contains all 10 ordered stages from cuFileDriverOpen to cuFileDriverClose",
        len(CUFILE_EXPECTED_LIFECYCLE) == 10
        and CUFILE_EXPECTED_LIFECYCLE[0] == "cuFileDriverOpen"
        and CUFILE_EXPECTED_LIFECYCLE[2] == "cuFileHandleRegister"
        and CUFILE_EXPECTED_LIFECYCLE[4] == "cuFileBufRegister"
        and CUFILE_EXPECTED_LIFECYCLE[5] == "cuFileRead_or_cuFileWrite"
        and CUFILE_EXPECTED_LIFECYCLE[-1] == "cuFileDriverClose",
        f"got {CUFILE_EXPECTED_LIFECYCLE}",
    )

    before_gds, after_gds = simulate_gdsio_benchmark()
    check(
        "21. gdsio Table 5-1 baseline (-x 2, Storage->CPU) achieves 8.0 GB/s at 1.25 ms latency (1.25 s for 10 GB)",
        before_gds.mode_flag == "-x 2"
        and before_gds.throughput_gb_s == 8.0
        and before_gds.avg_latency_ms == 1.25
        and before_gds.time_for_dataset_s == 1.25,
        f"got {before_gds}",
    )
    check(
        "22. gdsio Table 5-1 GDS path (-x 0, Storage->GPU) achieves 9.6 GB/s (+20.0%) at 1.00 ms (-20.0%)",
        after_gds.mode_flag == "-x 0"
        and after_gds.throughput_gb_s == 9.6
        and after_gds.avg_latency_ms == 1.00
        and after_gds.throughput_gain_pct == 20.0
        and after_gds.latency_reduction_pct == 20.0,
        f"got {after_gds}",
    )

    audit_compat = audit_cufile_json(
        use_poll_mode=True,
        poll_mode_max_size_kb=4,
        max_device_pinned_mem_size_kb=33_554_432,
        allow_compat_mode=True,
        workload_io_size_kb=1024,
    )
    check(
        "23. /etc/cufile.json audit converts 33,554,432 KB to 32.0 GiB and flags allow_compat_mode=true + 4 KB poll cap on 1 MB I/O",
        audit_compat.max_pinned_gpu_mem_gib == 32.0
        and audit_compat.is_strict_zero_copy_test is False
        and audit_compat.poll_mode_effective_for_large_io is False
        and len(audit_compat.warnings) == 2,
        f"got {audit_compat}",
    )

    audit_strict = audit_cufile_json(
        use_poll_mode=False,
        poll_mode_max_size_kb=4,
        max_device_pinned_mem_size_kb=33_554_432,
        allow_compat_mode=False,
        workload_io_size_kb=1024,
    )
    check(
        "24. /etc/cufile.json strict validation mode (allow_compat_mode=false, use_poll_mode=false) emits 0 warnings",
        audit_strict.is_strict_zero_copy_test is True and len(audit_strict.warnings) == 0,
        f"got {audit_strict}",
    )

    sizing = size_checkpoint_and_metadata(
        checkpoint_size_tb=2.0,
        target_window_s=60.0,
        total_small_files=50_000,
        files_per_webdataset_tar=50_000,
    )
    check(
        "25. 2 TB checkpoint in 60 s requires 33.33 GB/s sustained write bandwidth (fits on >= 1x 400G link = 50 GB/s)",
        sizing.required_write_bw_gb_s == 33.33 and sizing.min_400g_links_needed == 1,
        f"got {sizing}",
    )
    check(
        "26. Packing 50,000 tiny 20 KB files into a single 1 GB WebDataset tar cuts metadata stat() syscalls by 50,000x",
        sizing.metadata_stat_reduction_factor == 50_000 and sizing.tar_shard_count == 1,
        f"got {sizing}",
    )

    # 7. Multi-GPU rail aggregate math (8x ConnectX-7 400G NDR + 72-GPU NVL72 ingestion rate)
    eight_rail_gb_s = 8 * (400.0 / 8.0)
    nvl72_ingest_gb_s = 72 * 0.2  # 72 GPUs * 200 MB/s (0.2 GB/s) = 14.4 GB/s
    check(
        "27. 8-GPU rail-optimized HGX node with 8x 400G NICs delivers 400.0 GB/s (3.2 Tbps) aggregate RDMA bandwidth",
        eight_rail_gb_s == 400.0,
        f"got {eight_rail_gb_s}",
    )
    check(
        "28. 72-GPU NVL72 rack at 200 MB/s per GPU requires 14.4 GB/s (14-20 GB/s range) sustained storage ingestion",
        round(nvl72_ingest_gb_s, 2) == 14.4,
        f"got {nvl72_ingest_gb_s}",
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
