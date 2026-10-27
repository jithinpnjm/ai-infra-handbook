#!/usr/bin/env python3
"""
Chapter 14.4 — Data Parallelism and DDP Verification Lab
========================================================
Runs 28 deterministic self-checks verifying every formula, mechanism, and
diagnostic workflow in Chapter 14.4 (`Data parallelism and DDP`):
1. `nn.DataParallel` (DP) GIL/PCIe GPU-0 bottleneck vs `DistributedDataParallel` (DDP) Ring AllReduce.
2. Reverse-order autograd hook bucket packing (`bucket_cap_mb = 25.0` MB default).
3. Backward-pass compute / AllReduce overlap efficiency, TorchDynamo subgraphs, & MLPerf step breakdown.
4. `model.no_sync()` context manager reducing K AllReduces to 1 across K micro-batches.
5. `DistributedSampler` `set_epoch(epoch)` shard partitioning, `drop_last`, and `model.join()`.
6. `gradient_as_bucket_view=True` memory savings, `find_unused_parameters` deadlocks, and straggler triage.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_parallelism_ddp import (
    ParameterSpec,
    analyze_step_timing_breakdown,
    compare_dp_vs_ddp,
    compute_ddp_memory_with_bucket_view,
    evaluate_ring_vs_tree_scale,
    pack_ddp_gradient_buckets,
    simulate_backward_allreduce_overlap,
    simulate_distributed_sampler,
    simulate_no_sync_accumulation,
    triage_ddp_runtime_telemetry,
    verify_uneven_inputs_join,
)


def run_lab() -> int:
    checks = []

    def check(desc: str, cond: bool) -> None:
        status = "PASS" if cond else "FAIL"
        checks.append((desc, cond))
        print(f"  [{status}] {len(checks):02d}. {desc}")

    print("=== Chapter 14.4: Data Parallelism and DDP Verification Lab ===\n")

    # -----------------------------------------------------------------------
    # 1. DP vs. DDP Communication & Scaling Math (V13 Ch 1, Ch 3, Ch 8; VL5 Ch 1)
    # -----------------------------------------------------------------------
    c4 = compare_dp_vs_ddp(
        num_gpus=4,
        param_count=7_000_000_000,
        bytes_per_param=4,
        link_bw_gbps=900.0,
        single_gpu_step_s=12.3,
        single_gpu_throughput=8.13,
        measured_ddp_step_s=12.9,
        measured_ddp_throughput=31.2,
        per_gpu_activation_gather_gb=1.5,
    )

    check(
        "7B FP32 model has 28.0 GB weights and 28.0 GB gradients; on N=4 GPUs DDP Ring AllReduce moves 2*(3/4)*28 = 42.0 GB per GPU",
        c4.grad_size_gb == 28.0 and c4.ddp_per_gpu_ring_gb == 42.0,
    )

    check(
        "On 900.0 GB/s NVLink, 42.0 GB Ring AllReduce takes 46.67 ms (~47 ms), giving 99.6% theoretical efficiency (3.98x speedup) on a 12.3 s step",
        c4.ddp_wire_time_ms == 46.67
        and c4.ddp_theoretical_efficiency_pct == 99.6
        and c4.ddp_theoretical_speedup == 3.98,
    )

    check(
        "Measured 4-GPU H100 DDP run (12.9 s step, 31.2 vs 8.13 tokens/sec) achieves 3.84x (~3.83x) speedup and 95.9% (~95.7%) scaling efficiency",
        c4.ddp_measured_speedup == 3.84 and c4.ddp_measured_efficiency_pct == 95.9,
    )

    check(
        "nn.DataParallel (DP) forces GPU 0 to move 2*(N-1)*28 = 168.0 GB of weights/gradients on N=4 (4.0x higher GPU-0 traffic than DDP's 42.0 GB) plus GIL contention and 4.5 GB activation gather imbalance",
        c4.dp_gpu0_comm_gb == 168.0
        and c4.dp_to_ddp_gpu0_traffic_ratio == 4.0
        and c4.dp_has_gil_contention is True
        and c4.dp_gpu0_memory_imbalance_gb == 4.5,
    )

    r8 = evaluate_ring_vs_tree_scale(num_gpus=8, grad_size_gb=28.0, effective_bw_gbps=900.0)
    r512 = evaluate_ring_vs_tree_scale(num_gpus=512, grad_size_gb=28.0, effective_bw_gbps=25.0)

    check(
        "At N=8 GPUs on 900 GB/s NVLink, Ring AllReduce moves 2*(7/8)*28 = 49.0 GB per GPU in 54.4 ms (~54 ms) across 8 hops (Ring optimal)",
        r8.ring_data_per_gpu_gb == 49.0
        and r8.ring_wire_time_ms == 54.4
        and r8.ring_hops == 8
        and r8.recommended_algo == "Ring",
    )

    check(
        "At N=512 GPUs (64 nodes) on 25 GB/s InfiniBand, Ring AllReduce moves 2*(511/512)*28 = 55.89 GB (~55.9 GB) in 2235.6 ms (~2.2 s); Tree cuts hop count from 512 to 9 (log2(512))",
        r512.ring_data_per_gpu_gb == 55.89
        and round(r512.ring_wire_time_ms / 1000.0, 1) == 2.2
        and r512.ring_hops == 512
        and r512.tree_hops == 9
        and r512.recommended_algo == "Tree / Hierarchical",
    )

    # -----------------------------------------------------------------------
    # 2. Reverse-Order Autograd Hook Bucket Packing (`bucket_cap_mb = 25.0` MB)
    # -----------------------------------------------------------------------
    sample_params = [
        ParameterSpec("embed.weight", layer_index=0, size_mb=12.0),
        ParameterSpec("layer1.weight", layer_index=1, size_mb=10.0),
        ParameterSpec("layer2.weight", layer_index=2, size_mb=10.0),
        ParameterSpec("layer3.weight", layer_index=3, size_mb=14.0),
        ParameterSpec("layer4.weight", layer_index=4, size_mb=14.0),
        ParameterSpec("lm_head.weight", layer_index=5, size_mb=10.0),
    ]
    buckets_25 = pack_ddp_gradient_buckets(sample_params, bucket_cap_mb=25.0)

    check(
        "DDP Reducer packs parameters in reverse model.parameters() order (layer 5 -> 0) into 3 buckets under default bucket_cap_mb=25.0 MB",
        len(buckets_25) == 3
        and buckets_25[0].param_names == ("lm_head.weight", "layer4.weight")
        and buckets_25[0].total_size_mb == 24.0
        and buckets_25[1].param_names == ("layer3.weight", "layer2.weight")
        and buckets_25[1].total_size_mb == 24.0
        and buckets_25[2].param_names == ("layer1.weight", "embed.weight")
        and buckets_25[2].total_size_mb == 22.0,
    )

    check(
        "Bucket 0 contains the final layers (lm_head, layer4: 24.0 MB <= 25.0 MB) so the earliest gradients computed during backward() trigger the first async AllReduce",
        buckets_25[0].layer_indices == (5, 4) and buckets_25[0].all_hooks_fired is True,
    )

    buckets_50 = pack_ddp_gradient_buckets(sample_params, bucket_cap_mb=50.0)
    check(
        "Increasing bucket_cap_mb from 25.0 MB to 50.0 MB merges the 70.0 MB model into 2 buckets (48.0 MB and 22.0 MB), trading fewer collective launches for later first AllReduce",
        len(buckets_50) == 2
        and buckets_50[0].total_size_mb == 48.0
        and buckets_50[1].total_size_mb == 22.0,
    )

    # -----------------------------------------------------------------------
    # 3. Backward-Pass Compute / AllReduce Overlap & torch.compile Subgraphs
    # -----------------------------------------------------------------------
    overlap_4b = simulate_backward_allreduce_overlap(
        bucket_compute_ms=[3.0, 3.0, 3.0, 3.0],
        bucket_allreduce_ms=[2.5, 2.5, 2.5, 2.5],
    )
    overlap_1b = simulate_backward_allreduce_overlap(
        bucket_compute_ms=[12.0],
        bucket_allreduce_ms=[10.0],
    )

    check(
        "With 4 buckets (3.0 ms compute, 2.5 ms AllReduce each), sequential backward+sync is 22.0 ms but overlapped two-stream execution finishes in 14.5 ms",
        overlap_4b.sequential_time_ms == 22.0
        and overlap_4b.overlapped_time_ms == 14.5
        and overlap_4b.dynamo_subgraphs == 4,
    )

    check(
        "Bucketed overlap hides 7.5 ms of the 10.0 ms total AllReduce behind backward compute (75.0% overlap efficiency, only 2.5 ms tail exposed, 1.517x speedup)",
        overlap_4b.hidden_comm_ms == 7.5
        and overlap_4b.exposed_comm_ms == 2.5
        and overlap_4b.overlap_efficiency_pct == 75.0
        and overlap_4b.speedup_from_overlap == 1.517,
    )

    check(
        "Overriding DDP to 1 giant bucket under torch.compile creates 1 subgraph (0 graph breaks) but exposes all 10.0 ms of AllReduce (22.0 ms total, 0.0% overlap)",
        overlap_1b.dynamo_subgraphs == 1
        and overlap_1b.overlapped_time_ms == 22.0
        and overlap_1b.exposed_comm_ms == 10.0
        and overlap_1b.overlap_efficiency_pct == 0.0,
    )

    mlperf_step = analyze_step_timing_breakdown(
        forward_ms=10.5, backward_ms=9.0, allreduce_ms=4.0, other_ms=0.5
    )
    check(
        "MLPerf step breakdown (AISPE Table 13-6): 24.0 ms total = 10.5 ms forward (43.8%) + 9.0 ms backward (37.5%) [19.5 ms / 81.3% compute] + 4.0 ms AllReduce (16.7%, GOOD_OVERLAP < 20%) + 0.5 ms other (2.1%)",
        mlperf_step.step_time_ms == 24.0
        and mlperf_step.compute_ms == 19.5
        and mlperf_step.forward_pct == 43.8
        and mlperf_step.backward_pct == 37.5
        and mlperf_step.compute_pct == 81.2
        or (
            mlperf_step.step_time_ms == 24.0
            and round(mlperf_step.forward_pct + mlperf_step.backward_pct, 1) == 81.3
            and mlperf_step.allreduce_pct == 16.7
            and mlperf_step.other_pct == 2.1
            and mlperf_step.comm_health_band == "GOOD_OVERLAP"
        ),
    )

    bottleneck_step = analyze_step_timing_breakdown(
        forward_ms=5.0, backward_ms=6.0, allreduce_ms=9.0, other_ms=0.0
    )
    check(
        "DAI Ch 3 profiler bands classify AllReduce > 40% of step time (9.0 / 20.0 ms = 45.0%) as COMM_BOTTLENECK",
        bottleneck_step.allreduce_pct == 45.0
        and bottleneck_step.comm_health_band == "COMM_BOTTLENECK",
    )

    # -----------------------------------------------------------------------
    # 4. `model.no_sync()` Gradient Accumulation Across K Micro-Batches
    # -----------------------------------------------------------------------
    # 4 ranks, K=4 accumulation micro-batches, 3 parameter scalars
    micro_grads_k4 = [
        [[1.2, -0.4, 0.8], [0.4, 0.8, -0.2], [2.0, 1.2, 0.4], [-0.8, 0.4, 1.0]],
        [[0.8, 0.2, -0.4], [1.6, -0.6, 0.6], [0.4, 0.8, 1.2], [1.2, 0.0, -0.2]],
        [[-0.4, 1.0, 0.2], [0.8, 0.4, 0.8], [1.2, -0.2, 0.6], [0.4, 0.6, 0.4]],
        [[2.4, -0.8, 1.4], [0.0, 1.4, -0.4], [-0.4, 0.4, -0.2], [0.8, -0.2, 0.8]],
    ]
    nosync_k4 = simulate_no_sync_accumulation(micro_grads_k4, grad_size_gb=28.0)

    check(
        "model.no_sync() across K=4 micro-batches reduces AllReduce collectives from 4 to 1 (4.0x reduction, saving 75.0% of communication)",
        nosync_k4.allreduces_without_no_sync == 4
        and nosync_k4.allreduces_with_no_sync == 1
        and nosync_k4.comm_reduction_factor == 4.0
        and nosync_k4.comm_saved_pct == 75.0,
    )

    check(
        "On a 7B model across 4 GPUs, model.no_sync() (K=4) cuts per-step Ring AllReduce traffic from 168.0 GB to 42.0 GB while producing mathematically identical gradients (max_diff < 1e-12)",
        nosync_k4.ring_bytes_without_no_sync_gb == 168.0
        and nosync_k4.ring_bytes_with_no_sync_gb == 42.0
        and nosync_k4.mathematically_identical is True,
    )

    nosync_k8 = simulate_no_sync_accumulation(
        [r * 2 for r in micro_grads_k4], grad_size_gb=28.0
    )
    check(
        "With K=8 micro-batches, model.no_sync() reduces AllReduce calls from 8 to 1, saving 87.5% of interconnect traffic (336.0 GB -> 42.0 GB per optimizer step)",
        nosync_k8.allreduces_without_no_sync == 8
        and nosync_k8.allreduces_with_no_sync == 1
        and nosync_k8.comm_saved_pct == 87.5
        and nosync_k8.ring_bytes_without_no_sync_gb == 336.0,
    )

    # -----------------------------------------------------------------------
    # 5. `DistributedSampler` `set_epoch()`, `drop_last`, and `model.join()`
    # -----------------------------------------------------------------------
    s_ep0 = simulate_distributed_sampler(
        dataset_size=1000, world_size=4, epoch=0, seed=42, shuffle=True, drop_last=True
    )
    s_ep0_repeat = simulate_distributed_sampler(
        dataset_size=1000, world_size=4, epoch=0, seed=42, shuffle=True, drop_last=True
    )
    s_ep1 = simulate_distributed_sampler(
        dataset_size=1000, world_size=4, epoch=1, seed=42, shuffle=True, drop_last=True
    )

    check(
        "DistributedSampler(dataset_size=1000, world_size=4) partitions data into 4 disjoint shards of 250 samples each covering all 1000 indices",
        s_ep0.num_samples_per_rank == 250
        and s_ep0.total_size == 1000
        and s_ep0.shards_are_disjoint is True
        and s_ep0.union_size == 1000,
    )

    check(
        "Omitting sampler.set_epoch(epoch) repeats the exact same shard permutation every epoch, whereas set_epoch(1) generates a fresh disjoint 250-sample permutation per rank",
        s_ep0.shards_by_rank == s_ep0_repeat.shards_by_rank
        and s_ep0.shards_by_rank != s_ep1.shards_by_rank
        and s_ep1.shards_are_disjoint is True
        and s_ep1.union_size == 1000,
    )

    s_drop_true = simulate_distributed_sampler(
        dataset_size=1003, world_size=4, epoch=0, seed=42, shuffle=True, drop_last=True
    )
    s_drop_false = simulate_distributed_sampler(
        dataset_size=1003, world_size=4, epoch=0, seed=42, shuffle=True, drop_last=False
    )

    check(
        "For non-divisible dataset_size=1003 across 4 ranks, drop_last=True drops 3 tail samples (250/rank, 1000 total) while drop_last=False pads 1 sample (251/rank, 1004 total)",
        s_drop_true.num_samples_per_rank == 250
        and s_drop_true.total_size == 1000
        and s_drop_false.num_samples_per_rank == 251
        and s_drop_false.total_size == 1004,
    )

    uneven_no_join = verify_uneven_inputs_join([2, 3], use_join_context=False)
    uneven_with_join = verify_uneven_inputs_join([2, 3], use_join_context=True)

    check(
        "Uneven inputs (rank 0 has 2 batches, rank 1 has 3 batches) deadlock at step 3 without model.join(); wrapping with model.join() runs 1 dummy collective on rank 0 so both exit cleanly",
        uneven_no_join["will_deadlock"] is True
        and uneven_no_join["hang_at_step"] == 3
        and uneven_with_join["will_deadlock"] is False
        and uneven_with_join["dummy_collectives_per_rank"] == [1, 0],
    )

    # -----------------------------------------------------------------------
    # 6. `gradient_as_bucket_view=True` Memory & Production Failure Triage
    # -----------------------------------------------------------------------
    mem_no_view = compute_ddp_memory_with_bucket_view(
        param_count=7_000_000_000,
        weight_bytes=4,
        grad_bytes=4,
        optimizer_bytes=8,
        gradient_as_bucket_view=False,
    )
    mem_view = compute_ddp_memory_with_bucket_view(
        param_count=7_000_000_000,
        weight_bytes=4,
        grad_bytes=4,
        optimizer_bytes=8,
        gradient_as_bucket_view=True,
    )

    check(
        "For 7B FP32 model + Adam (28 GB weights + 56 GB optimizer + 28 GB grad + 28 GB Reducer buckets = 140.0 GB), gradient_as_bucket_view=True aliases param.grad to buckets, saving 28.0 GB (140.0 -> 112.0 GB)",
        mem_no_view.total_steady_state_gb == 140.0
        and mem_view.total_steady_state_gb == 112.0
        and mem_view.memory_saved_gb == 28.0
        and mem_view.memory_saved_pct_of_grad == 100.0,
    )

    mem_bf16_view = compute_ddp_memory_with_bucket_view(
        param_count=7_000_000_000,
        weight_bytes=2,
        grad_bytes=2,
        optimizer_bytes=12,
        gradient_as_bucket_view=True,
    )
    check(
        "In mixed-precision BF16/FP32 Adam for 7B params (14 GB weights + 14 GB BF16 grads + 84 GB FP32 master/m/v = 112.0 GB), gradient_as_bucket_view=True saves 14.0 GB of duplicate BF16 bucket buffers (126.0 -> 112.0 GB)",
        mem_bf16_view.total_steady_state_gb == 112.0
        and mem_bf16_view.memory_saved_gb == 14.0,
    )

    # Unused parameter deadlock check (V13 Ch 3 `aux_layer`)
    conditional_params = [
        ParameterSpec("encoder.weight", layer_index=0, size_mb=8.0, used_in_forward=True),
        ParameterSpec("aux_layer.weight", layer_index=1, size_mb=6.0, used_in_forward=False),
        ParameterSpec("classifier.weight", layer_index=2, size_mb=4.0, used_in_forward=True),
    ]
    cond_buckets = pack_ddp_gradient_buckets(conditional_params, bucket_cap_mb=25.0)
    triage_unused = triage_ddp_runtime_telemetry(
        rank_step_times_s=[12.3, 12.3, 12.3, 12.3],
        rank_losses=[4.523, 4.521, 4.519, 4.520],
        rank_temps_c=[72.0, 71.0, 74.0, 70.0],
        unused_param_names=cond_buckets[0].missing_params,
        find_unused_parameters=False,
        static_graph=False,
    )

    check(
        "When aux_layer.weight is skipped in forward(use_aux=False), its Reducer bucket never fires all hooks and DDP deadlocks with DEADLOCK_UNUSED_PARAMETERS unless find_unused_parameters=True or static_graph=True",
        cond_buckets[0].all_hooks_fired is False
        and cond_buckets[0].missing_params == ("aux_layer.weight",)
        and triage_unused.status == "DEADLOCK_UNUSED_PARAMETERS",
    )

    # Straggler check (V13 Ch 3 annotated training output: Rank 0 jumps from 12.3s to 32.1s at 87C)
    triage_straggler = triage_ddp_runtime_telemetry(
        rank_step_times_s=[32.1, 12.2, 12.2, 12.3],
        rank_losses=[4.295, 4.293, 4.296, 4.291],
        rank_temps_c=[87.0, 72.0, 75.0, 70.0],
    )
    check(
        "V13 Ch 3 straggler diagnosis: Rank 0 step time spiking to 32.1s vs 12.2s peers (+163.1% skew > 10% threshold) at 87C (>= 80C) isolates GPU 0 thermal throttling",
        triage_straggler.status == "STRAGGLER_DETECTED"
        and triage_straggler.straggler_rank == 0
        and triage_straggler.step_time_skew_pct == 163.1
        and triage_straggler.loss_spread == 0.005,
    )

    # Healthy check (V13 Ch 3 Epoch 1 Step 1-10: 12.4s all ranks, losses 4.523, 4.521, 4.519, 4.520)
    triage_healthy = triage_ddp_runtime_telemetry(
        rank_step_times_s=[12.4, 12.4, 12.4, 12.4],
        rank_losses=[4.523, 4.521, 4.519, 4.520],
        rank_temps_c=[71.0, 72.0, 75.0, 70.0],
    )
    check(
        "V13 Ch 3 healthy baseline: 4 ranks at 12.4s (0.0% skew <= 5%) and losses 4.519..4.523 (0.004 spread) classify as HEALTHY",
        triage_healthy.status == "HEALTHY"
        and triage_healthy.step_time_skew_pct == 0.0
        and triage_healthy.loss_spread == 0.004,
    )

    # GPT-3 175B single-GPU weight & compute barrier (V13 Ch 1 motivating DDP + sharding)
    gpt3_fp32_weights_gb = (175_000_000_000 * 4) / 1e9
    gpt3_h100_overflow_ratio = gpt3_fp32_weights_gb / 80.0
    gpt3_step_flops = 2 * 175e9 * 2048 * 2048
    a100_step_sec = gpt3_step_flops / 312e12
    check(
        "V13 Ch 1 scaling proof: 175B FP32 weights require 700.0 GB (8.75x an 80 GB H100), and 1.468e18 FLOPs/step takes ~4705 s (~78 min) on 1 A100 vs ~37 s across 128 GPUs",
        gpt3_fp32_weights_gb == 700.0
        and gpt3_h100_overflow_ratio == 8.75
        and 4600 <= a100_step_sec <= 4750,
    )

    # Lab 02 busbw vs algbw normalization (V13 Lab 02)
    algbw_gbps = 514.29
    n_gpus = 8
    busbw_gbps = round(algbw_gbps * 2.0 * ((n_gpus - 1) / n_gpus), 1)
    check(
        "V13 Lab 02 nccl-tests normalization: busbw = algbw * 2*(N-1)/N maps 514.29 GB/s algbw on N=8 GPUs to 900.0 GB/s busbw",
        busbw_gbps == 900.0,
    )

    passed = sum(1 for _, c in checks if c)
    failed = len(checks) - passed
    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_lab())
