#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.10: Slurm GPU scheduling: GRES, NVML autodetect, MIG and device constraints."""
import subprocess
import sys
from pathlib import Path

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


def simulate_gpu_binding_and_isolation(
    allocated_phys_gpus: list[int],
    ntasks: int,
    constrain_devices: bool = True,
    gpu_bind: str = "per_task:1",
) -> list[dict[str, str]]:
    """Simulate Slurm CUDA_VISIBLE_DEVICES and /dev/nvidia* visibility per task (srun(1) & cgroup.conf(5))."""
    visible_devs = (
        [f"/dev/nvidia{g}" for g in allocated_phys_gpus]
        if constrain_devices
        else [f"/dev/nvidia{g}" for g in range(8)]
    )
    # When ConstrainDevices=yes, CUDA_VISIBLE_DEVICES uses 0-based indices relative to the job's allocation
    job_gpu_ids = list(range(len(allocated_phys_gpus))) if constrain_devices else list(allocated_phys_gpus)
    results = []
    for task_id in range(ntasks):
        if gpu_bind == "none":
            cvd = ",".join(str(x) for x in job_gpu_ids)
        elif gpu_bind.startswith("per_task:"):
            k = int(gpu_bind.split(":")[1])
            start = (task_id * k) % len(job_gpu_ids)
            cvd = ",".join(str(job_gpu_ids[start + i]) for i in range(k))
        elif gpu_bind.startswith("map:"):
            mapping = [int(x) for x in gpu_bind.split(":")[1].split(",")]
            mapped_idx = mapping[task_id % len(mapping)]
            cvd = str(job_gpu_ids[mapped_idx])
        else:
            cvd = ",".join(str(x) for x in job_gpu_ids)
        results.append(
            {
                "task_id": str(task_id),
                "SLURM_JOB_GPUS": ",".join(str(g) for g in allocated_phys_gpus),
                "CUDA_VISIBLE_DEVICES": cvd,
                "cgroup_devices": ",".join(visible_devs),
            }
        )
    return results


def parse_nvidia_smi_csv_and_detect_anomalies(node_csv: dict[str, str]) -> tuple[dict[str, list[dict[str, float]]], list[str]]:
    """Parse nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total CSV and detect anomalies (DAI Ch. 8)."""
    nodes_metrics: dict[str, list[dict[str, float]]] = {}
    anomalies: list[str] = []
    for node, csv_text in node_csv.items():
        gpus = []
        for line in csv_text.strip().splitlines():
            util, mem_used, mem_total = map(float, line.split(", "))
            gpus.append(
                {
                    "utilization": util,
                    "memory_used_gb": round(mem_used / 1024.0, 2),
                    "memory_total_gb": round(mem_total / 1024.0, 2),
                }
            )
        nodes_metrics[node] = gpus
        for i, gpu in enumerate(gpus):
            if gpu["utilization"] < 50:
                anomalies.append(f"{node} GPU {i}: Low utilization ({gpu['utilization']:.0f}%)")
            if gpu["memory_used_gb"] / gpu["memory_total_gb"] > 0.95:
                anomalies.append(f"{node} GPU {i}: High memory usage")
    return nodes_metrics, anomalies


def main() -> None:
    # 1. Verify gpu_env_check.py runs cleanly and reports all 15 environment keys
    script = Path(__file__).resolve().parent / "gpu_env_check.py"
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=True)
    out_lines = proc.stdout.strip().splitlines()
    check(
        "gpu_env_check.py runs cleanly and prints 15 GPU/Slurm environment variables plus nvidia-smi status",
        len(out_lines) >= 16 and "CUDA_VISIBLE_DEVICES=" in proc.stdout and "SLURM_JOB_GPUS=" in proc.stdout,
    )

    # 2. Verify cgroup device isolation (ConstrainDevices=yes) remaps physical GPUs [3, 7] to [0, 1] and binds per task
    isolated = simulate_gpu_binding_and_isolation([3, 7], ntasks=2, constrain_devices=True, gpu_bind="per_task:1")
    unisolated = simulate_gpu_binding_and_isolation([3, 7], ntasks=2, constrain_devices=False, gpu_bind="none")
    check(
        "ConstrainDevices=yes remaps physical GPUs [3,7] to task-relative CUDA_VISIBLE_DEVICES=0 and 1 and fences /dev/nvidia*",
        isolated[0]["CUDA_VISIBLE_DEVICES"] == "0"
        and isolated[1]["CUDA_VISIBLE_DEVICES"] == "1"
        and isolated[0]["cgroup_devices"] == "/dev/nvidia3,/dev/nvidia7"
        and unisolated[0]["CUDA_VISIBLE_DEVICES"] == "3,7"
        and "/dev/nvidia0" in unisolated[0]["cgroup_devices"],
    )

    # 3. Verify DAI Ch. 8 SLURMJobMonitor CSV parser and straggler/OOM anomaly detection (<50% util, >95% memory)
    sample_csv = {
        "gpu01": "94, 65536, 81920\n32, 79872, 81920",
    }
    metrics, anomalies = parse_nvidia_smi_csv_and_detect_anomalies(sample_csv)
    check(
        "SLURMJobMonitor detects straggler (<50% utilization: 32%) and near-OOM (>95% memory: 78.0/80.0 GiB) GPUs",
        metrics["gpu01"][0]["memory_total_gb"] == 80.0
        and metrics["gpu01"][1]["memory_used_gb"] == 78.0
        and anomalies == ["gpu01 GPU 1: Low utilization (32%)", "gpu01 GPU 1: High memory usage"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
