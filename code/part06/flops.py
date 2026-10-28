#!/usr/bin/env python3
"""Peak FLOPS, vector pipeline cycles, and efficiency calculator for Chapter 6.1."""


def rpeak_cpu(nodes: int, sockets: int, cores: int, ghz: float, flops_per_cycle: int) -> float:
    """Return CPU cluster theoretical peak in GFLOP/s."""
    return float(nodes * sockets * cores * ghz * flops_per_cycle)


def gpu_cluster_peak_pflops(nodes: int, gpus_per_node: int, tflops_per_gpu: float) -> float:
    """Return GPU cluster theoretical peak in PFLOP/s."""
    return float(nodes * gpus_per_node * tflops_per_gpu) / 1000.0


def hpl_efficiency(rmax: float, rpeak: float) -> float:
    """Return measured HPL efficiency fraction (Rmax / Rpeak)."""
    return rmax / rpeak


def vector_pipeline_cycles(num_elements: int, slowest_stage_cycles: int, total_pipeline_cycles: int) -> int:
    """Return total clock cycles K*(N-1)+S for a pipelined vector operation (SCL Ch. 2)."""
    return slowest_stage_cycles * (num_elements - 1) + total_pipeline_cycles


def filter_nodes_missing_ram(
    meminfo_kb_by_node: dict[str, int], expected_kb: int, tolerance_fraction: float = 0.02
) -> list[str]:
    """Return sorted node names whose MemTotal kB falls below expected_kb * (1 - tolerance_fraction) (SCL Ch. 1)."""
    min_acceptable_kb = expected_kb * (1.0 - tolerance_fraction)
    return sorted(node for node, kb in meminfo_kb_by_node.items() if kb < min_acceptable_kb)


if __name__ == "__main__":
    # 2 sockets x 64 cores x 2.4 GHz, AVX-512 with 2 FMA units: 2*2*8 = 32 FP64 FLOPs/cycle/core (983.0 TFLOP/s vs 16 without AVX-512: 491.5 TFLOP/s)
    g = rpeak_cpu(nodes=100, sockets=2, cores=64, ghz=2.4, flops_per_cycle=32)
    g16 = rpeak_cpu(nodes=100, sockets=2, cores=64, ghz=2.4, flops_per_cycle=16)
    print(f"CPU cluster Rpeak: {g/1000:.1f} TFLOP/s (or {g16/1000:.1f} TFLOP/s at 16 FLOPs/cycle)")
    # 8 GPUs per node at an assumed 60 TFLOP/s FP64 tensor each (illustrative)
    print(f"GPU cluster Rpeak: {gpu_cluster_peak_pflops(100, 8, 60):.1f} PFLOP/s")
    print(f"HPL efficiency if Rmax=38 PF: {hpl_efficiency(38, 48):.0%}")
    # AI view: dense BF16 at an assumed 1000 TFLOP/s per GPU, 40% MFU
    peak = gpu_cluster_peak_pflops(100, 8, 1000)
    print(f"AI peak (BF16 dense, illustrative): {peak:.0f} PFLOP/s; at 40% MFU: {peak*0.4:.0f} PFLOP/s")
    # Vector pipeline cycles: N=1000 -> 1004 vs 5000 (4.98x speedup)
    c1000 = vector_pipeline_cycles(1000, 1, 5)
    print(f"Vector pipeline N=1000: {c1000} cycles vs 5000 unpipelined ({5000/c1000:.2f}x)")
