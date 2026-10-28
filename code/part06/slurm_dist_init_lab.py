#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.12: Multi-node training on Slurm: PMIx, torchrun, NCCL environment, binding."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slurm_dist_init import dist_env, expand_hostlist

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def megatron_checkpoint_gb(params_billions: float = 8.03, num_shards: int = 4, shard_gb: float = 27.0) -> dict[str, float]:
    """Compute theoretical (bf16 weights + fp32 Adam states) vs actual .distcp checkpoint footprint (DAI Ch. 8)."""
    weights_gb = round(params_billions * 2.0, 2)
    adam_gb = round(params_billions * 8.0, 2)
    theo_gb = round(weights_gb + adam_gb, 2)
    disk_gb = round(num_shards * shard_gb, 2)
    return {"weights_gb": weights_gb, "adam_gb": adam_gb, "theoretical_gb": theo_gb, "disk_gb": disk_gb}


def nccl_diag_metrics(size_mb: float, allreduce_iters: int, allreduce_elapsed_s: float, p2p_iters: int, p2p_elapsed_s: float) -> tuple[float, float]:
    """Compute DAI Ch. 8 diagnose_nccl() AllReduce bandwidth (GB/s) and P2P one-way latency (us)."""
    bw_gbps = round((size_mb * 2.0 * allreduce_iters) / allreduce_elapsed_s, 1)
    lat_us = round((p2p_elapsed_s / (2.0 * p2p_iters)) * 1e6, 1)
    return bw_gbps, lat_us


def main() -> None:
    # 1. Verify expand_hostlist and dist_env (SLURM_JOB_ID=4242 -> MASTER_PORT=14242)
    hosts = expand_hostlist("gpu[01-03,07],cpu1,x[9-10]")
    fake_env = {
        "SLURM_JOB_ID": "4242",
        "SLURM_JOB_NODELIST": "gpu[01-03,07]",
        "SLURM_PROCID": "2",
        "SLURM_LOCALID": "0",
        "SLURM_NTASKS": "4",
    }
    de = dist_env(fake_env)
    check(
        "expand_hostlist expands bracket ranges and dist_env derives MASTER_ADDR=gpu01, MASTER_PORT=14242",
        hosts == ["gpu01", "gpu02", "gpu03", "gpu07", "cpu1", "x9", "x10"]
        and de == {
            "RANK": "2",
            "LOCAL_RANK": "0",
            "WORLD_SIZE": "4",
            "MASTER_ADDR": "gpu01",
            "MASTER_PORT": "14242",
        },
    )

    # 2. Verify DAI Ch. 8 Megatron-LM 8.03B checkpoint footprint (16.06 + 64.24 = 80.30 GB, 4x27G = 108 GB) and ASP Ch. 4 timings
    ckpt = megatron_checkpoint_gb(8.03, 4, 27.0)
    gloo_ms = round((400.0 / 2000.0) * 1000.0, 2)  # 400 MB at 2 GB/s = 200.0 ms
    nccl_ms = round((400.0 / 100000.0) * 1000.0, 2)  # 400 MB at 100 GB/s = 4.0 ms
    init_loop_ms = 48.0 + 0.5  # 48.5 ms
    check(
        "Megatron 8.03B checkpoint math (16.06+64.24=80.30 GB vs 108.0 GB .distcp) & ASP Ch. 4 gloo (200 ms) vs nccl (4 ms)",
        ckpt["weights_gb"] == 16.06
        and ckpt["adam_gb"] == 64.24
        and ckpt["theoretical_gb"] == 80.3
        and ckpt["disk_gb"] == 108.0
        and gloo_ms == 200.0
        and nccl_ms == 4.0
        and init_loop_ms == 48.5,
    )

    # 3. Verify DAI Ch. 8 diagnose_nccl() bandwidth and point-to-point latency formulas
    bw, lat = nccl_diag_metrics(size_mb=100.0, allreduce_iters=10, allreduce_elapsed_s=20.0, p2p_iters=100, p2p_elapsed_s=0.004)
    check(
        "diagnose_nccl() computes (100*2*10)/20.0 = 100.0 GB/s AllReduce BW and (0.004/200)*1e6 = 20.0 us P2P latency",
        bw == 100.0 and lat == 20.0,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
