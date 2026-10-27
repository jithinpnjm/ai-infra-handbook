"""Self-checking verification lab for Chapter 13.3: GPUDirect Storage architecture.

Run with:
    python3 -B code/part13/gpudirect_storage_arch_lab.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpudirect_storage_arch import (
    BLACKWELL_DECOMPRESSION_FORMATS,
    BLACKWELL_DECOMP_PEAK_GB_S,
    CUFILE_SEVEN_STEP_API,
    CUFILE_TEN_STAGE_FLOW,
    GDSIO_TRANSFER_MODES,
    compare_model_weight_fetch,
    evaluate_deepseek_3fs_vs_ceph,
    evaluate_gdsio_table_5_1,
    evaluate_gpu_io_wait_speedup,
    evaluate_lab03_decision,
    lint_cufile_json,
    resolve_gds_execution_path,
    simulate_blackwell_gds_decompression,
    validate_cufile_lifecycle,
    validate_o_direct_alignment,
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

    print("=== Chapter 13.3 Lab: GPUDirect Storage Architecture ===")

    # 1. cuFile 7-step core API lifecycle & 10-stage OS/CUDA flow
    ok_7, msg_7 = validate_cufile_lifecycle(CUFILE_SEVEN_STEP_API)
    check(
        "1. cuFile 7-step API lifecycle validates cuFileDriverOpen -> cuFileHandleRegister -> cuFileBufRegister -> cuFileRead/Write -> Deregister -> Close",
        ok_7 is True and len(CUFILE_SEVEN_STEP_API) == 7,
        f"got ok={ok_7}, msg={msg_7}",
    )

    bad_seq = list(CUFILE_SEVEN_STEP_API)
    bad_seq[1], bad_seq[2] = bad_seq[2], bad_seq[1]
    ok_bad, msg_bad = validate_cufile_lifecycle(bad_seq)
    check(
        "2. Swapping cuFileHandleRegister and cuFileBufRegister is flagged as an invalid lifecycle order",
        ok_bad is False and "Step 2 mismatch" in msg_bad,
        f"got ok={ok_bad}, msg={msg_bad}",
    )

    check(
        "3. Full 10-stage OS+CUDA cuFile flow includes open_O_DIRECT and cudaMalloc around the 7 cuFile calls",
        len(CUFILE_TEN_STAGE_FLOW) == 10
        and CUFILE_TEN_STAGE_FLOW[1] == "open_O_DIRECT"
        and CUFILE_TEN_STAGE_FLOW[3] == "cudaMalloc",
        f"got {CUFILE_TEN_STAGE_FLOW}",
    )

    # 2. CPU bounce vs GDS model-weight fetch (100 MB @ 3000 MB/s vs 6000 MB/s) & Lab 03 trials
    fetch_cmp = compare_model_weight_fetch(
        payload_mb=100.0,
        storage_read_latency_us=100.0,
        cpu_gpu_copy_bw_mb_s=3000.0,
        gds_dma_bw_mb_s=6000.0,
    )
    check(
        "4. 100 MB fetch via CPU bounce @ 3000 MB/s takes 33.33 ms (~33 ms) copy + 100 us storage latency with 2 PCIe traversals",
        fetch_cmp.traditional_copy_ms == 33.33
        and fetch_cmp.traditional_total_ms == 33.43
        and fetch_cmp.pcie_traversals_traditional == 2,
        f"got {fetch_cmp}",
    )
    check(
        "5. 100 MB fetch via GDS direct DMA @ 6000 MB/s takes 16.67 ms (~16 ms) + 100 us storage latency (2.0x copy speedup, 1 PCIe hop)",
        fetch_cmp.gds_dma_ms == 16.67
        and fetch_cmp.speedup_ratio == 2.0
        and fetch_cmp.pcie_traversals_gds == 1,
        f"got {fetch_cmp}",
    )

    lab03_dec = evaluate_lab03_decision(
        cpu_trial_times_s=(0.265, 0.250, 0.248, 0.247, 0.246),
        buffer_size_mb=100.0,
        gds_avg_throughput_mb_s=960.0,
        deploy_threshold_pct=20.0,
    )
    check(
        "6. Volume 15 Lab 03 5-trial CPU bounce baseline averages 0.251 s (398 MB/s) and recommends DEPLOY GDS when improvement > 20%",
        lab03_dec["cpu_avg_time_s"] == 0.251
        and lab03_dec["cpu_avg_throughput_mb_s"] == 398.0
        and lab03_dec["deploy_gds"] is True
        and lab03_dec["recommendation"] == "DEPLOY GDS",
        f"got {lab03_dec}",
    )

    # 3. BAR1 / nvidia-fs P2P DMA eligibility vs POSIX compatibility fallback
    p2p_ok = resolve_gds_execution_path(
        nvidia_fs_loaded=True,
        filesystem_type="wekafs",
        is_fuse_mount=False,
        o_direct_enabled=True,
        uses_cufile_api=True,
        pcie_topology="PIX",
        alignment_ok=True,
        allow_compat_mode=False,
        bar1_free_kb=33_554_432,
        requested_buf_kb=102_400,
    )
    check(
        "7. PIX topology + nvidia-fs + O_DIRECT + aligned buffer executes gds-p2p-dma (nvidia-fs stats increment, no __memcpy_avx2)",
        p2p_ok.selected_path == "gds-p2p-dma"
        and p2p_ok.nvidia_fs_stats_increment is True
        and p2p_ok.cpu_memcpy_avx2_active is False
        and p2p_ok.bar1_pinned_kb == 102_400,
        f"got {p2p_ok}",
    )

    phb_deg = resolve_gds_execution_path(
        nvidia_fs_loaded=True,
        filesystem_type="lustre",
        is_fuse_mount=False,
        o_direct_enabled=True,
        uses_cufile_api=True,
        pcie_topology="PHB",
        alignment_ok=True,
        allow_compat_mode=False,
        bar1_free_kb=33_554_432,
        requested_buf_kb=102_400,
    )
    check(
        "8. PHB root-complex topology degrades GDS to gds-root-complex-degraded even when nvidia-fs is active",
        phb_deg.selected_path == "gds-root-complex-degraded"
        and phb_deg.nvidia_fs_stats_increment is True,
        f"got {phb_deg}",
    )

    no_cufile = resolve_gds_execution_path(
        nvidia_fs_loaded=True,
        filesystem_type="wekafs",
        is_fuse_mount=False,
        o_direct_enabled=True,
        uses_cufile_api=False,
        pcie_topology="PIX",
        alignment_ok=True,
        allow_compat_mode=False,
        bar1_free_kb=33_554_432,
        requested_buf_kb=102_400,
    )
    check(
        "9. Application calling torch.load(map_location='cpu') without cuFile falls back to CPU (__memcpy_avx2 active, nvidia-fs stats 0)",
        no_cufile.selected_path == "compat-posix-fallback"
        and no_cufile.nvidia_fs_stats_increment is False
        and no_cufile.cpu_memcpy_avx2_active is True,
        f"got {no_cufile}",
    )

    fuse_compat = resolve_gds_execution_path(
        nvidia_fs_loaded=True,
        filesystem_type="fuse",
        is_fuse_mount=True,
        o_direct_enabled=True,
        uses_cufile_api=True,
        pcie_topology="PIX",
        alignment_ok=True,
        allow_compat_mode=True,
        bar1_free_kb=33_554_432,
        requested_buf_kb=102_400,
    )
    check(
        "10. FUSE user-space mount cannot use GDS and silently falls back to POSIX when allow_compat_mode=true",
        fuse_compat.selected_path == "compat-posix-fallback"
        and fuse_compat.nvidia_fs_stats_increment is False
        and "FUSE" in fuse_compat.reason,
        f"got {fuse_compat}",
    )

    strict_reject = resolve_gds_execution_path(
        nvidia_fs_loaded=False,
        filesystem_type="nvme-of",
        is_fuse_mount=False,
        o_direct_enabled=True,
        uses_cufile_api=True,
        pcie_topology="PIX",
        alignment_ok=True,
        allow_compat_mode=False,
        bar1_free_kb=33_554_432,
        requested_buf_kb=102_400,
    )
    check(
        "11. Missing nvidia-fs.ko with allow_compat_mode=false fails loudly (error-io-rejected) instead of silently bouncing",
        strict_reject.selected_path == "error-io-rejected"
        and strict_reject.nvidia_fs_stats_increment is False
        and strict_reject.cpu_memcpy_avx2_active is False,
        f"got {strict_reject}",
    )

    bar1_exhausted = resolve_gds_execution_path(
        nvidia_fs_loaded=True,
        filesystem_type="vast",
        is_fuse_mount=False,
        o_direct_enabled=True,
        uses_cufile_api=True,
        pcie_topology="PIX",
        alignment_ok=True,
        allow_compat_mode=True,
        bar1_free_kb=1024,
        requested_buf_kb=65_536,
    )
    check(
        "12. Exhausting max_device_pinned_mem_size_kb BAR1 quota triggers POSIX compatibility fallback when allow_compat_mode=true",
        bar1_exhausted.selected_path == "compat-posix-fallback"
        and "BAR1" in bar1_exhausted.reason,
        f"got {bar1_exhausted}",
    )

    # 4. 4 KiB O_DIRECT & 8 KiB Lustre alignment validator
    align_4k_ok = validate_o_direct_alignment(
        file_offset_bytes=4096 * 128,
        transfer_size_bytes=1024 * 1024,
        gpu_buffer_addr=0x7F00_0010_0000,
        required_alignment_bytes=4096,
    )
    check(
        "13. 4 KiB (4096 B) aligned file offset (512 KiB), transfer size (1 MiB), and GPU buffer address pass O_DIRECT validation",
        align_4k_ok.all_aligned is True and align_4k_ok.bounce_penalty_if_unaligned is False,
        f"got {align_4k_ok}",
    )

    align_bad = validate_o_direct_alignment(
        file_offset_bytes=4100,
        transfer_size_bytes=1_000_000,
        gpu_buffer_addr=0x7F00_0010_0100,
        required_alignment_bytes=4096,
    )
    check(
        "14. Unaligned offset (4100 B), size (1,000,000 B), and GPU buffer (+0x100) fail 4 KiB check and compute realigned bounds (4096 B, 1003520 B)",
        align_bad.all_aligned is False
        and align_bad.offset_aligned is False
        and align_bad.size_aligned is False
        and align_bad.buffer_aligned is False
        and align_bad.realigned_offset_bytes == 4096
        and align_bad.realigned_size_bytes == 1_003_520,
        f"got {align_bad}",
    )

    align_lustre_8k = validate_o_direct_alignment(
        file_offset_bytes=4096,
        transfer_size_bytes=8192,
        gpu_buffer_addr=0x7F00_0010_0000,
        required_alignment_bytes=8192,
    )
    check(
        "15. 4 KiB offset fails strict 8 KiB (8192 B) Lustre alignment check and realigns offset down to 0",
        align_lustre_8k.all_aligned is False
        and align_lustre_8k.offset_aligned is False
        and align_lustre_8k.realigned_offset_bytes == 0
        and align_lustre_8k.realigned_size_bytes == 16_384,
        f"got {align_lustre_8k}",
    )

    # 5. gdsio transfer modes (-x 0..6) & Table 5-1 throughput / latency / CPU efficiency math
    check(
        "16. gdsio defines all 7 transfer modes -x 0 through -x 6 (-x 0/5/6 use GDS; -x 1/2/3/4 use CPU bounce)",
        len(GDSIO_TRANSFER_MODES) == 7
        and GDSIO_TRANSFER_MODES[0]["uses_gds"] is True
        and GDSIO_TRANSFER_MODES[2]["uses_gds"] is False
        and GDSIO_TRANSFER_MODES[5]["uses_gds"] is True
        and GDSIO_TRANSFER_MODES[6]["uses_gds"] is True,
        f"got {GDSIO_TRANSFER_MODES}",
    )

    t51 = evaluate_gdsio_table_5_1()
    check(
        "17. gdsio Table 5-1 baseline (-x 2, Storage->CPU->GPU) measures 8.0 GB/s at 1.25 ms average latency and 85% CPU utilization",
        t51.cpu_mode_flag == "-x 2"
        and t51.cpu_throughput_gb_s == 8.0
        and t51.cpu_latency_ms == 1.25
        and t51.cpu_utilization_before_pct == 85.0,
        f"got {t51}",
    )
    check(
        "18. gdsio Table 5-1 GDS path (-x 0, Storage->GPU) measures 9.6 GB/s (+20.0%) at 1.00 ms (-20.0%) and 25% CPU utilization",
        t51.gds_mode_flag == "-x 0"
        and t51.gds_throughput_gb_s == 9.6
        and t51.throughput_improvement_pct == 20.0
        and t51.gds_latency_ms == 1.00
        and t51.latency_reduction_pct == 20.0
        and t51.cpu_utilization_after_pct == 25.0,
        f"got {t51}",
    )
    check(
        "19. GDS reduces CPU utilization by 60.0 percentage points (85% -> 25%) and boosts GB/s per CPU% by 4.08x (0.0941 -> 0.3840)",
        t51.cpu_utilization_saved_pct_points == 60.0
        and t51.gb_per_sec_per_cpu_pct_before == 0.0941
        and t51.gb_per_sec_per_cpu_pct_after == 0.3840
        and t51.cpu_efficiency_multiplier == 4.08,
        f"got {t51}",
    )
    check(
        "20. VAST Data GDS benchmarks report +20.0% read throughput on Ampere A100 and +30.0%+ on Hopper H100",
        t51.vast_a100_gain_pct == 20.0 and t51.vast_h100_gain_pct == 30.0,
        f"got A100={t51.vast_a100_gain_pct}, H100={t51.vast_h100_gain_pct}",
    )

    # 6. /etc/cufile.json linter
    lint_lax = lint_cufile_json(
        {
            "profile": {"nvtx": False, "cufile_stats": 0},
            "properties": {
                "max_device_pinned_mem_size_kb": 33_554_432,
                "use_poll_mode": True,
                "poll_mode_max_size_kb": 4,
                "allow_compat_mode": True,
            },
            "fs": {"generic": {"posix_unaligned_kb": True}},
        },
        expected_io_size_kb=1024,
    )
    check(
        "21. /etc/cufile.json linter flags allow_compat_mode=true, poll_mode_max_size_kb=4 on 1 MiB I/O, and posix_unaligned_kb=true",
        lint_lax.valid_for_strict_gds_verification is False
        and lint_lax.max_pinned_mem_gib == 32.0
        and lint_lax.poll_triggers_for_io_kb is False
        and lint_lax.nsys_tracepoints_enabled is False
        and len(lint_lax.issues) == 3,
        f"got {lint_lax}",
    )

    lint_hardened = lint_cufile_json(
        {
            "profile": {"nvtx": True, "cufile_stats": 3},
            "properties": {
                "max_device_pinned_mem_size_kb": 33_554_432,
                "use_poll_mode": False,
                "poll_mode_max_size_kb": 4,
                "allow_compat_mode": False,
            },
            "fs": {"generic": {"posix_unaligned_kb": False}},
        },
        expected_io_size_kb=1024,
    )
    check(
        "22. Hardened /etc/cufile.json (allow_compat_mode=false, nvtx=true, cufile_stats=3) passes strict verification with 0 issues",
        lint_hardened.valid_for_strict_gds_verification is True
        and lint_hardened.nsys_tracepoints_enabled is True
        and len(lint_hardened.issues) == 0,
        f"got {lint_hardened}",
    )

    # 7. Blackwell Hardware Decompression Engine (800 GB/s) & DeepSeek 3FS math
    check(
        "23. Blackwell Hardware Decompression Engine supports LZ4, Snappy, and Deflate at up to 800.0 GB/s",
        BLACKWELL_DECOMPRESSION_FORMATS == ("LZ4", "Snappy", "Deflate")
        and BLACKWELL_DECOMP_PEAK_GB_S == 800.0,
        f"got {BLACKWELL_DECOMPRESSION_FORMATS} @ {BLACKWELL_DECOMP_PEAK_GB_S}",
    )

    bw_lz4 = simulate_blackwell_gds_decompression(
        compression_format="LZ4",
        uncompressed_batch_gb=4.0,
        compression_ratio=2.5,
        storage_gds_bw_gb_s=50.0,
        hw_decomp_engine_bw_gb_s=800.0,
    )
    check(
        "24. 4.0 GB batch compressed 2.5x (1.6 GB on disk) reads in 32.0 ms via 50 GB/s GDS + 5.0 ms @ 800 GB/s Decompression Engine = 37.0 ms (2.16x speedup vs 80.0 ms uncompressed)",
        bw_lz4.compressed_storage_read_gb == 1.6
        and bw_lz4.uncompressed_gds_read_time_ms == 80.0
        and bw_lz4.compressed_gds_read_time_ms == 32.0
        and bw_lz4.hw_decompression_time_ms == 5.0
        and bw_lz4.pipelined_total_time_ms == 37.0
        and bw_lz4.effective_uncompressed_throughput_gb_s == 108.11
        and bw_lz4.end_to_end_speedup == 2.16,
        f"got {bw_lz4}",
    )

    three_fs = evaluate_deepseek_3fs_vs_ceph()
    check(
        "25. DeepSeek 3FS (68 nodes, 680 x 16 TB NVMe = 10,880 TB) delivers 6.6 TB/s + 1.4 TB/s bg (8.0 TB/s combined, up to 7.3 TB/s peak), 6.0x faster than Ceph (1.1 TB/s)",
        three_fs["total_nvme_drives"] == 680
        and three_fs["raw_capacity_tb"] == 10_880
        and three_fs["three_fs_fg_tb_s"] == 6.6
        and three_fs["three_fs_bg_tb_s"] == 1.4
        and three_fs["three_fs_combined_tb_s"] == 8.0
        and three_fs["three_fs_peak_tb_s"] == 7.3
        and three_fs["speedup_over_ceph"] == 6.0,
        f"got {three_fs}",
    )

    io_wait = evaluate_gpu_io_wait_speedup(0.30, 0.05)
    check(
        "26. Reducing GPU I/O wait from 30.0% to 5.0% cuts I/O stall time by 6.0x and increases active compute share by 35.71%",
        io_wait["initial_wait_pct"] == 30.0
        and io_wait["tuned_wait_pct"] == 5.0
        and io_wait["wait_reduction_factor"] == 6.0
        and io_wait["step_throughput_gain_pct"] == 35.71,
        f"got {io_wait}",
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
