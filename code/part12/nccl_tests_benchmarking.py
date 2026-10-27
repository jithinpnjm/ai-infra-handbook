#!/usr/bin/env python3
"""Chapter 12.17: nccl-tests and fabric benchmarking.

Deterministic models and parsers for:
1. Three-tier fabric validation hierarchy:
   - Tier 1 (`nvbandwidth`): PCIe Gen5 x16 (64.0 GB/s raw, 50-60 GB/s copy) vs
     downtrained x8 (25-30 GB/s) and NVLink 4 (900.0 GB/s) / NVLink 5 (1,800.0 GB/s).
   - Tier 2 (`perftest` `ib_write_bw` / `ib_write_lat` / `ib_send_lat`): 400G NDR
     (50.0 GB/s line rate, ~390.0 Gbps = 48.75 GB/s healthy RDMA vs ~195.0 Gbps
     2x-lane downtrain) and GPUDirect RDMA (`--use_cuda`, `PIX`) vs host bounce (`SYS`).
   - Tier 3 (`nccl-tests`): `all_reduce_perf`, `reduce_scatter_perf`,
     `all_gather_perf`, `alltoall_perf`, `broadcast_perf`, `reduce_perf`.
2. Exact `algbw` and `busbw` conversion formulas:
   - algbw = S / t
   - AllReduce: busbw = algbw * 2 * (n - 1) / n
   - ReduceScatter / AllGather / AllToAll: busbw = algbw * (n - 1) / n
   - Broadcast / Reduce: busbw = algbw * 1.0
3. `all_reduce_perf` CLI sweep generator (`-b`, `-e`, `-f`, `-g`, `-w`, `-n`, `-c`)
   and output table parser (validating `#wrong == 0`, out-of-place vs in-place,
   and single-node vs multi-node acceptance gates).
4. Binary-search straggler node bisection across N nodes in ceil(log2(N)) + 1 steps
   and per-rail (`mlx5_0..mlx5_7`) isolation.
5. Distributed training & inference benchmarking metrics from DAI Ch. 10 & ASP Ch. 4:
   - Scaling efficiency (`throughput_N / (throughput_1 * N)`), fleet waste cost,
     communication overhead growth (`155 ms -> 33 ms`, `0% -> 55%`), and Amdahl's Law.
   - LLM inference latency decomposition (`e2e_latency = TTFT + (output_tokens - 1) * ITL`),
     cold-start vs warm decode multipliers, and percentile SLA evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Dict, List, Sequence, Tuple


class FabricBenchmarkError(ValueError):
    """Raised when benchmark parameters or parsed outputs are invalid."""


@dataclass(frozen=True)
class NCCLTestRow:
    """One parsed row from an `nccl-tests` benchmark output table."""

    size_bytes: int
    count_elements: int
    dtype: str
    redop: str
    root: int
    out_of_place_time_us: float
    out_of_place_algbw_gbps: float
    out_of_place_busbw_gbps: float
    out_of_place_wrong: int
    in_place_time_us: float
    in_place_algbw_gbps: float
    in_place_busbw_gbps: float
    in_place_wrong: int


BUSBW_COLLECTIVES = {
    "all_reduce": "2*(n-1)/n",
    "reduce_scatter": "(n-1)/n",
    "all_gather": "(n-1)/n",
    "alltoall": "(n-1)/n",
    "broadcast": "1",
    "reduce": "1",
}


def compute_busbw_factor(collective: str, num_ranks: int) -> float:
    """Return the exact NCCL `busbw / algbw` multiplier for `collective` on `num_ranks`."""
    key = collective.strip().lower().replace("-", "_").replace("_perf", "")
    if key not in BUSBW_COLLECTIVES:
        raise FabricBenchmarkError(f"Unsupported collective: {collective!r}")
    if num_ranks < 1:
        raise FabricBenchmarkError("num_ranks must be >= 1")
    if num_ranks == 1:
        return 0.0
    if key == "all_reduce":
        return 2.0 * (num_ranks - 1) / num_ranks
    if key in ("reduce_scatter", "all_gather", "alltoall"):
        return (num_ranks - 1) / num_ranks
    return 1.0


def compute_algbw_and_busbw(
    collective: str,
    size_bytes: int,
    time_us: float,
    num_ranks: int,
) -> Dict[str, float]:
    """Compute `algbw` (GB/s) and `busbw` (GB/s) matching `nccl-tests` conventions.

    In `nccl-tests`:
      algbw (GB/s) = size_bytes / (time_us * 1e3) = (size_bytes / 1e9) / (time_us / 1e6)
      busbw (GB/s) = algbw * factor(collective, num_ranks)
    """
    if size_bytes <= 0:
        raise FabricBenchmarkError("size_bytes must be > 0")
    if time_us <= 0.0:
        raise FabricBenchmarkError("time_us must be > 0")
    factor = compute_busbw_factor(collective, num_ranks)
    time_sec = time_us * 1e-6
    algbw_gbps = round((size_bytes / time_sec) / 1e9, 2)
    busbw_gbps = round(algbw_gbps * factor, 2)
    return {
        "size_bytes": float(size_bytes),
        "time_us": round(time_us, 4),
        "num_ranks": float(num_ranks),
        "busbw_factor": round(factor, 6),
        "algbw_gbps": algbw_gbps,
        "busbw_gbps": busbw_gbps,
        "per_rank_bytes": round(size_bytes * factor, 2),
    }


def generate_nccl_tests_sweep(
    min_bytes: int = 8_388_608,
    max_bytes: int = 1_073_741_824,
    step_factor: int = 2,
    gpus_per_proc: int = 1,
    num_procs: int = 8,
    warmup_iters: int = 5,
    measure_iters: int = 20,
    dtype_bytes: int = 4,
) -> Dict[str, object]:
    """Model the message-size sweep of `nccl-tests` (`-b`, `-e`, `-f`, `-g`, `-w`, `-n`)."""
    if min_bytes <= 0 or max_bytes < min_bytes:
        raise FabricBenchmarkError("Invalid min_bytes / max_bytes range")
    if step_factor < 2:
        raise FabricBenchmarkError("step_factor (-f) must be >= 2")
    if gpus_per_proc < 1 or num_procs < 1:
        raise FabricBenchmarkError("gpus_per_proc and num_procs must be >= 1")

    sizes: List[int] = []
    cur = min_bytes
    while cur <= max_bytes:
        sizes.append(cur)
        cur *= step_factor

    total_ranks = gpus_per_proc * num_procs
    # Each step executes warmup_iters + measure_iters for out-of-place AND in-place (2 modes)
    collectives_per_size = 2 * (warmup_iters + measure_iters)
    return {
        "total_ranks": total_ranks,
        "num_sizes": len(sizes),
        "sizes_bytes": sizes,
        "element_counts": [s // dtype_bytes for s in sizes],
        "collectives_per_size": collectives_per_size,
        "total_collective_launches": len(sizes) * collectives_per_size,
        "all_reduce_busbw_factor": round(compute_busbw_factor("all_reduce", total_ranks), 6),
    }


def parse_nccl_tests_table(
    raw_output: str,
    collective: str = "all_reduce",
    num_ranks: int = 8,
    tolerance_gbps: float = 0.08,
) -> Dict[str, object]:
    """Parse `nccl-tests` tabular output (either single-mode 9-col or dual-mode 13-col).

    Validates `#wrong == 0` on every row and checks that `busbw == algbw * factor`.
    """
    rows: List[NCCLTestRow] = []
    factor = compute_busbw_factor(collective, num_ranks)
    formula_mismatches = 0
    total_wrong = 0

    for line in raw_output.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        toks = s.split()
        if not toks[0].isdigit():
            continue
        if len(toks) == 13:
            row = NCCLTestRow(
                size_bytes=int(toks[0]),
                count_elements=int(toks[1]),
                dtype=toks[2],
                redop=toks[3],
                root=int(toks[4]),
                out_of_place_time_us=float(toks[5]),
                out_of_place_algbw_gbps=float(toks[6]),
                out_of_place_busbw_gbps=float(toks[7]),
                out_of_place_wrong=int(toks[8]),
                in_place_time_us=float(toks[9]),
                in_place_algbw_gbps=float(toks[10]),
                in_place_busbw_gbps=float(toks[11]),
                in_place_wrong=int(toks[12]),
            )
        elif len(toks) == 8:
            # 8-column abbreviated summary (size, count, type, redop, time, algbw, busbw, #wrong)
            t_us = float(toks[4])
            alg = float(toks[5])
            bus = float(toks[6])
            w = int(toks[7])
            row = NCCLTestRow(
                size_bytes=int(toks[0]),
                count_elements=int(toks[1]),
                dtype=toks[2],
                redop=toks[3],
                root=-1,
                out_of_place_time_us=t_us,
                out_of_place_algbw_gbps=alg,
                out_of_place_busbw_gbps=bus,
                out_of_place_wrong=w,
                in_place_time_us=t_us,
                in_place_algbw_gbps=alg,
                in_place_busbw_gbps=bus,
                in_place_wrong=w,
            )
        else:
            continue

        rows.append(row)
        total_wrong += row.out_of_place_wrong + row.in_place_wrong
        expected_oop_bus = row.out_of_place_algbw_gbps * factor
        expected_ip_bus = row.in_place_algbw_gbps * factor
        if (
            abs(row.out_of_place_busbw_gbps - expected_oop_bus) > tolerance_gbps
            or abs(row.in_place_busbw_gbps - expected_ip_bus) > tolerance_gbps
        ):
            formula_mismatches += 1

    if not rows:
        raise FabricBenchmarkError("No valid benchmark rows found in raw_output")

    avg_busbw = sum(
        0.5 * (r.out_of_place_busbw_gbps + r.in_place_busbw_gbps) for r in rows
    ) / len(rows)
    peak_busbw = max(
        max(r.out_of_place_busbw_gbps, r.in_place_busbw_gbps) for r in rows
    )
    return {
        "num_rows": len(rows),
        "rows": rows,
        "total_wrong": total_wrong,
        "correctness_pass": total_wrong == 0,
        "formula_mismatches": formula_mismatches,
        "avg_busbw_gbps": round(avg_busbw, 2),
        "peak_busbw_gbps": round(peak_busbw, 2),
    }


def attribute_three_tier_bottleneck(
    nvbandwidth_DtoH_gbps: float,
    ib_write_bw_host_gbps: float,
    ib_write_bw_cuda_gbps: float,
    nccl_single_node_busbw_gbps: float,
    nccl_multi_node_busbw_gbps: float,
    app_effective_busbw_gbps: float,
    expected_pcie_gen5_gbps: float = 55.0,
    expected_ib_ndr400_gbps: float = 390.0,
    expected_single_node_nvlink_gbps: float = 95.0,
) -> Dict[str, object]:
    """Classify the root-cause layer using the 3-tier hardware-to-collective hierarchy.

    Follows Volume 07 Ch. 10 & Lab 03, Volume 08 Lab 02, and Volume 05 Lab 02:
    - Tier 1 (`nvbandwidth`): < 35 GB/s on PCIe Gen5 x16 -> PCIe link downtrained (e.g., x16 -> x8, 25-30 GB/s).
    - Tier 2a (`ib_write_bw` host): < 250 Gbps on 400G NDR -> physical link downtrain / cable / optics (~195 Gbps for 2x lanes).
    - Tier 2b (`ib_write_bw --use_cuda`): host RDMA fast (~390 Gbps) but CUDA RDMA slow -> GPUDirect RDMA (`nvidia_peermem` / ACS / `SYS` cross-NUMA) broken.
    - Tier 3a (`nccl-tests` single-node): < 80% of local baseline -> intra-node P2P / Fabric Manager / `NCCL_P2P_DISABLE=1`.
    - Tier 3b (`nccl-tests` multi-node): < 80% of multi-node baseline -> inter-node transport fallback (`NET/Socket`), rail misbinding, or fabric congestion.
    - Application layer: `nccl-tests` fast at 512M-1G, but PyTorch DDP slow -> tiny message sizes (e.g., 256 KB fragments), fix `bucket_cap_mb` (25 MB -> 50 MB).
    """
    if nvbandwidth_DtoH_gbps < 0.65 * expected_pcie_gen5_gbps:
        layer = "Tier 1: Intra-node PCIe / Motherboard"
        cause = "PCIe link downtrained (e.g., Gen5 x16 -> x8 at 25-30 GB/s); check lspci -vv LnkSta and nvidia-smi -q -d PCI"
    elif ib_write_bw_host_gbps < 0.70 * expected_ib_ndr400_gbps:
        layer = "Tier 2a: Physical RDMA Link / Optics"
        cause = "InfiniBand/RoCE link speed or lane width degraded (e.g., 4x -> 2x at ~195 Gbps); check ibstat, mlxlink, and symbol_error counters"
    elif ib_write_bw_cuda_gbps < 0.65 * ib_write_bw_host_gbps:
        layer = "Tier 2b: GPUDirect RDMA / PCIe Locality"
        cause = "Host RDMA is healthy (~390 Gbps) but GPU-buffer RDMA falls back through host bounce buffer; check lsmod nvidia_peermem, PCIe ACS, and PIX vs SYS NUMA locality"
    elif nccl_single_node_busbw_gbps < 0.80 * expected_single_node_nvlink_gbps:
        layer = "Tier 3a: Single-Node NCCL Collectives"
        cause = "Intra-node collective degraded below 80% baseline; check nvidia-fabricmanager, NVLink status, and ensure NCCL_P2P_DISABLE=0 and NCCL_SHM_DISABLE=0"
    elif nccl_multi_node_busbw_gbps < 0.80 * nccl_single_node_busbw_gbps:
        layer = "Tier 3b: Multi-Node NCCL Collectives"
        cause = "Multi-node collective below 80% of single-node baseline (e.g., 58.2 GB/s vs 95.18 GB/s = 61.1%); check NCCL_DEBUG=INFO for NET/Socket fallback, GID index, or rail imbalance"
    elif app_effective_busbw_gbps < 0.70 * nccl_multi_node_busbw_gbps:
        layer = "Tier 4: Framework / Application Bucket Sizing"
        cause = "Hardware and nccl-tests are healthy, but application issues microscopic AllReduce payloads (e.g., 256 KB); increase DDP bucket_cap_mb (default 25 MB -> 50 MB)"
    else:
        layer = "Healthy"
        cause = "All tiers pass baseline thresholds"

    multi_to_single_ratio = (
        nccl_multi_node_busbw_gbps / nccl_single_node_busbw_gbps
        if nccl_single_node_busbw_gbps > 0
        else 0.0
    )
    return {
        "bottleneck_layer": layer,
        "diagnosis": cause,
        "multi_to_single_node_ratio": round(multi_to_single_ratio, 4),
        "multi_node_passes_80pct_gate": multi_to_single_ratio >= 0.80,
    }


def bisect_straggler_node(
    node_names: Sequence[str],
    straggler_index: int,
    healthy_busbw_gbps: float = 360.0,
    degraded_busbw_gbps: float = 65.0,
    threshold_ratio: float = 0.85,
) -> Dict[str, object]:
    """Isolate a single slow node among N nodes using binary-search bisection.

    At each step, split the suspect candidate list into left and right halves.
    If a half has only 1 node, pair it with a known-good reference node so a
    multi-node collective can still execute.
    Total benchmark runs = ceil(log2(N)) + 1 (1 initial full-cluster run + ceil(log2(N)) half-splits),
    or ceil(log2(N)) split steps once the full-cluster run has already flagged degradation.
    """
    n = len(node_names)
    if n < 2:
        raise FabricBenchmarkError("Need at least 2 nodes for multi-node bisection")
    if not (0 <= straggler_index < n):
        raise FabricBenchmarkError("straggler_index out of range")

    straggler_name = node_names[straggler_index]
    threshold_gbps = healthy_busbw_gbps * threshold_ratio

    def run_subset_benchmark(subset: Sequence[str]) -> float:
        return degraded_busbw_gbps if straggler_name in subset else healthy_busbw_gbps

    history: List[Dict[str, object]] = []
    # Step 0: full cluster verification
    full_bw = run_subset_benchmark(node_names)
    history.append(
        {
            "step": 0,
            "tested_nodes": list(node_names),
            "measured_busbw_gbps": full_bw,
            "passed": full_bw >= threshold_gbps,
        }
    )

    candidates = list(node_names)
    known_good_ref = node_names[0] if straggler_index != 0 else node_names[-1]
    split_steps = 0

    while len(candidates) > 1:
        split_steps += 1
        mid = len(candidates) // 2
        left = candidates[:mid]
        right = candidates[mid:]

        test_group = left if len(left) >= 2 else [left[0], known_good_ref]
        bw = run_subset_benchmark(test_group)
        passed = bw >= threshold_gbps
        history.append(
            {
                "step": split_steps,
                "tested_nodes": test_group,
                "measured_busbw_gbps": bw,
                "passed": passed,
            }
        )
        if not passed:
            # Straggler is in left half; right half is now proven healthy
            known_good_ref = right[0]
            candidates = left
        else:
            # Left half is healthy; straggler must be in right half
            known_good_ref = left[0]
            candidates = right

    theoretical_split_steps = math.ceil(math.log2(n))
    return {
        "num_nodes": n,
        "isolated_node": candidates[0],
        "expected_straggler": straggler_name,
        "correct": candidates[0] == straggler_name,
        "split_steps": split_steps,
        "theoretical_log2_steps": theoretical_split_steps,
        "total_runs_including_initial": len(history),
        "linear_pairwise_runs_saved": n - split_steps,
        "history": history,
    }


def evaluate_training_scaling_and_bottlenecks(
    single_gpu_throughput: float = 100.0,
    eight_gpu_throughput: float = 650.0,
    sixty_four_gpu_efficiency: float = 0.52,
    gpu_hourly_cost_usd: float = 4.50,
    run_hours: float = 336.0,
    serial_fraction: float = 0.10,
) -> Dict[str, float]:
    """Compute distributed training scaling efficiency, fleet waste, and Amdahl bounds from DAI Ch. 10."""
    # 8-GPU scaling efficiency: 6.5x / 8 = 81.25%
    eight_gpu_speedup = eight_gpu_throughput / single_gpu_throughput
    eight_gpu_efficiency = eight_gpu_speedup / 8.0
    predicted_16_gpu_speedup = 16.0 * eight_gpu_efficiency

    # 64-GPU fleet waste (DAI Ch. 10: 64 GPUs at 52% scaling efficiency -> 33.28 effective GPUs, ~31 idle)
    effective_gpus_64 = 64.0 * sixty_four_gpu_efficiency
    wasted_gpus_64 = 64.0 - effective_gpus_64
    wasted_gpu_hours = wasted_gpus_64 * run_hours
    wasted_cost_usd = wasted_gpu_hours * gpu_hourly_cost_usd

    # Iteration breakdown (DAI Ch. 10 Fig 10.1: 155 ms on 1 GPU -> 33 ms on 16 GPUs with 55% comm overhead)
    iter_1_gpu_ms = 155.0
    iter_16_gpu_ms = 33.0
    comm_share_16_gpu = 0.55
    comm_time_16_gpu_ms = iter_16_gpu_ms * comm_share_16_gpu
    compute_time_16_gpu_ms = iter_16_gpu_ms * (1.0 - comm_share_16_gpu)
    iter_speedup_16_gpu = iter_1_gpu_ms / iter_16_gpu_ms
    iter_efficiency_16_gpu = iter_speedup_16_gpu / 16.0

    # Epoch duration and 70B H100 MFU (1,000,000 samples at 1,000 samples/sec = 1000s = 16.67 min;
    # 70B BF16 on 8x H100 = 7,912 TFLOPS: 3,200 tok/s -> 1,344 TFLOPS = 16.99% MFU; 9,000 tok/s -> 3,780 TFLOPS = 47.78% MFU)
    epoch_minutes = (1_000_000.0 / 1_000.0) / 60.0
    mfu_before_pct = (6.0 * 70e9 * 3_200.0 / 1e12) / 7_912.0 * 100.0
    mfu_after_pct = (6.0 * 70e9 * 9_000.0 / 1e12) / 7_912.0 * 100.0

    # Amdahl's Law maximum speedup: 1 / (serial_fraction + (1 - serial_fraction)/N)
    amdahl_infinite_max = 1.0 / serial_fraction
    amdahl_64_gpu = 1.0 / (serial_fraction + (1.0 - serial_fraction) / 64.0)
    amdahl_64_efficiency_pct = (amdahl_64_gpu / 64.0) * 100.0

    return {
        "eight_gpu_speedup": round(eight_gpu_speedup, 4),
        "eight_gpu_efficiency_ratio": round(eight_gpu_efficiency, 4),
        "eight_gpu_efficiency_pct": round(eight_gpu_efficiency * 100.0, 2),
        "predicted_16_gpu_speedup": round(predicted_16_gpu_speedup, 1),
        "effective_gpus_64": round(effective_gpus_64, 2),
        "wasted_gpus_64": round(wasted_gpus_64, 2),
        "wasted_gpu_hours": round(wasted_gpu_hours, 2),
        "wasted_cost_usd": round(wasted_cost_usd, 2),
        "epoch_minutes": round(epoch_minutes, 2),
        "mfu_before_pct": round(mfu_before_pct, 2),
        "mfu_after_pct": round(mfu_after_pct, 2),
        "iter_1_gpu_ms": iter_1_gpu_ms,
        "iter_16_gpu_ms": iter_16_gpu_ms,
        "comm_time_16_gpu_ms": round(comm_time_16_gpu_ms, 2),
        "compute_time_16_gpu_ms": round(compute_time_16_gpu_ms, 2),
        "iter_speedup_16_gpu": round(iter_speedup_16_gpu, 2),
        "iter_efficiency_16_gpu_pct": round(iter_efficiency_16_gpu * 100.0, 2),
        "amdahl_infinite_max": round(amdahl_infinite_max, 2),
        "amdahl_64_gpu": round(amdahl_64_gpu, 2),
        "amdahl_64_efficiency_pct": round(amdahl_64_efficiency_pct, 2),
    }


def evaluate_inference_latency_and_percentiles(
    ttft_ms: float,
    itl_ms: float,
    output_tokens: int,
    latencies_ms: Sequence[float],
    sla_p99_ms: float = 200.0,
) -> Dict[str, float]:
    """Compute LLM inference latency metrics (`e2e_latency = TTFT + (output_tokens - 1) * ITL`) and percentiles."""
    if output_tokens < 1:
        raise FabricBenchmarkError("output_tokens must be >= 1")
    if not latencies_ms:
        raise FabricBenchmarkError("latencies_ms must be non-empty")

    decode_ms = (output_tokens - 1) * itl_ms
    e2e_ms = ttft_ms + decode_ms
    ttft_share_pct = (ttft_ms / e2e_ms) * 100.0 if e2e_ms > 0 else 0.0

    sorted_lats = sorted(latencies_ms)
    n = len(sorted_lats)

    def pct(p: float) -> float:
        idx = min(n - 1, max(0, math.ceil((p / 100.0) * n) - 1))
        return float(sorted_lats[idx])

    mean_ms = sum(sorted_lats) / n
    p50_ms = pct(50.0)
    p95_ms = pct(95.0)
    p99_ms = pct(99.0)

    return {
        "ttft_ms": round(ttft_ms, 2),
        "itl_ms": round(itl_ms, 2),
        "output_tokens": float(output_tokens),
        "decode_ms": round(decode_ms, 2),
        "e2e_latency_ms": round(e2e_ms, 2),
        "ttft_share_pct": round(ttft_share_pct, 2),
        "mean_ms": round(mean_ms, 2),
        "p50_ms": round(p50_ms, 2),
        "p95_ms": round(p95_ms, 2),
        "p99_ms": round(p99_ms, 2),
        "p99_to_p50_ratio": round(p99_ms / p50_ms, 2) if p50_ms > 0 else 0.0,
        "passes_p99_sla": 1.0 if p99_ms <= sla_p99_ms else 0.0,
    }
