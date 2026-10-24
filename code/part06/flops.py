"""Back-of-envelope peak (Rpeak-style) and efficiency calculator."""
def rpeak_cpu(nodes, sockets, cores, ghz, flops_per_cycle):
    """GFLOP/s peak = nodes * sockets * cores * GHz * FLOPs/cycle/core."""
    return nodes * sockets * cores * ghz * flops_per_cycle

def gpu_cluster_peak_pflops(nodes, gpus_per_node, tflops_per_gpu):
    return nodes * gpus_per_node * tflops_per_gpu / 1000.0

def hpl_efficiency(rmax, rpeak):
    return rmax / rpeak

if __name__ == "__main__":
    # 2 sockets x 64 cores x 2.4 GHz, AVX-512 with 2 FMA units: 2*2*8 = 32 FP64 FLOPs/cycle/core
    g = rpeak_cpu(nodes=100, sockets=2, cores=64, ghz=2.4, flops_per_cycle=32)
    print(f"CPU cluster Rpeak: {g/1000:.1f} TFLOP/s")
    # 8 GPUs per node at an assumed 60 TFLOP/s FP64 tensor each (illustrative)
    print(f"GPU cluster Rpeak: {gpu_cluster_peak_pflops(100, 8, 60):.1f} PFLOP/s")
    print(f"HPL efficiency if Rmax=38 PF: {hpl_efficiency(38, 48):.0%}")
    # AI view: dense BF16 at an assumed 1000 TFLOP/s per GPU, 40% MFU
    peak = gpu_cluster_peak_pflops(100, 8, 1000)
    print(f"AI peak (BF16 dense, illustrative): {peak:.0f} PFLOP/s; at 40% MFU: {peak*0.4:.0f} PFLOP/s")
