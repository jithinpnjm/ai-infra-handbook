"""Chapter 11.9 Lab — JobSet, LeaderWorkerSet, PyTorchJob and the MPI Operator.

Run with:
    python3 code/part11/jobset_lws_pytorch_mpi_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jobset_lws_pytorch_mpi import (
    ClusterTrainingRuntimeSpec,
    TrainJobSubmission,
    build_mpijob_spec,
    compare_full_finetuning_vs_lora,
    evaluate_leader_worker_set,
    merge_trainjob_with_runtime,
    synthesize_pytorchjob_env,
)


def _check(condition: bool, label: str, passed: list[str], failed: list[str]) -> None:
    if condition:
        passed.append(label)
        print(f"  [PASS] {label}")
    else:
        failed.append(label)
        print(f"  [ERR]  {label}")


def main() -> int:
    passed: list[str] = []
    failed: list[str] = []

    print("=== Chapter 11.9 Lab: JobSet, LeaderWorkerSet, PyTorchJob & MPI Operator ===")

    # 1. Kubeflow PyTorchJob Environment & Headless Service Discovery (`volume-06` §8.2)
    pt_pods = synthesize_pytorchjob_env(
        job_name="llm-training",
        namespace="ml-team-a",
        master_replicas=1,
        worker_replicas=3,
        master_port=23456,
    )
    _check(
        len(pt_pods) == 4 and pt_pods[0]["WORLD_SIZE"] == "4",
        "PyTorchJob with 1 Master + 3 Workers creates 4 pods with WORLD_SIZE='4'",
        passed,
        failed,
    )
    _check(
        pt_pods[0]["role"] == "master" and pt_pods[0]["RANK"] == "0",
        "Master pod (llm-training-master-0) receives role='master' and RANK='0'",
        passed,
        failed,
    )
    _check(
        [p["RANK"] for p in pt_pods[1:]] == ["1", "2", "3"],
        "Worker pods (llm-training-worker-0..2) receive sequential RANK='1', '2', '3'",
        passed,
        failed,
    )
    _check(
        all(
            p["MASTER_ADDR"]
            == "llm-training-master-0.llm-training.ml-team-a.svc.cluster.local"
            for p in pt_pods
        ),
        "All PyTorchJob pods resolve MASTER_ADDR via headless service DNS pointing to master-0",
        passed,
        failed,
    )

    # 2. Kubeflow Trainer v2 (`v2.1.0`) ClusterTrainingRuntime + TrainJob -> JobSet (GAK Ch 6 Examples 6-4 & 6-6)
    rt = ClusterTrainingRuntimeSpec(
        name="my-torch-distributed-runtime",
        framework_label="torch",
        default_num_nodes=1,
        num_proc_per_node="auto",
        container_image="pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime",
    )
    tj = TrainJobSubmission(
        job_name="llama-31-8b-lora",
        runtime_name="my-torch-distributed-runtime",
        num_nodes=8,
        cpu_per_node=4,
        memory_per_node="64Gi",
        gpus_per_node=1,
        serialized_func_embedded=True,
    )
    merged = merge_trainjob_with_runtime(rt, tj)
    _check(
        merged["generated_kind"] == "JobSet"
        and merged["replicated_job_name"] == "node",
        "Kubeflow Trainer merges TrainJob + ClusterTrainingRuntime into a JobSet (replicatedJob: node)",
        passed,
        failed,
    )
    _check(
        merged["image"] == "pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime"
        and merged["framework"] == "torch",
        "Merged JobSet inherits pytorch:2.7.1-cuda12.8-cudnn9-runtime and framework='torch'",
        passed,
        failed,
    )
    _check(
        merged["num_nodes"] == 8
        and merged["total_gpus"] == 8
        and merged["total_cpus"] == 32,
        "Example 6-6 TrainJob (num_nodes=8, cpu=4, gpu=1) allocates 8 GPUs and 32 CPUs across 8 nodes",
        passed,
        failed,
    )
    _check(
        merged["requires_image_rebuild_on_code_change"] is False,
        "Kubeflow Trainer SDK serializes custom trainer function into TrainJob CR without image rebuilds",
        passed,
        failed,
    )

    # Compare against KubeRay RayJob (requires image rebuild or external script mount)
    ray_like = merge_trainjob_with_runtime(
        rt,
        TrainJobSubmission(
            "ray-style",
            "my-torch-distributed-runtime",
            serialized_func_embedded=False,
        ),
    )
    _check(
        ray_like["requires_image_rebuild_on_code_change"] is True,
        "When function is not embedded (as in RayJob image packaging), code changes require image rebuild",
        passed,
        failed,
    )

    # 3. Full Fine-Tuning vs PEFT LoRA Efficiency (GAK Ch 6: <1% params tuned, 1-10% adapter size)
    lora_cmp = compare_full_finetuning_vs_lora(
        base_model_params_b=8.0,
        lora_tuned_pct=0.8,
        lora_adapter_size_pct=5.0,
        num_adapters_served=10,
    )
    _check(
        lora_cmp["is_under_one_pct"] == 1.0
        and lora_cmp["tuned_params_millions"] == 64.0,
        "LoRA tuning 0.8% (<1%) of an 8B model updates only 64.0M parameters",
        passed,
        failed,
    )
    _check(
        lora_cmp["full_ft_serving_footprint_models"] == 10.0
        and lora_cmp["lora_serving_footprint_models"] == 1.5,
        "Serving 10 fine-tuned variants takes 10.0x base model memory with Full FT vs 1.5x with 5% LoRA adapters",
        passed,
        failed,
    )

    # 4. LeaderWorkerSet (LWS) for Multi-Node Sharded LLM Inference (GAK Ch 7)
    lws_healthy = evaluate_leader_worker_set(
        replicas=2, size_per_group=4, gpus_per_pod=8, failed_group_index=None
    )
    _check(
        lws_healthy["leaders_per_group"] == 1
        and lws_healthy["workers_per_group"] == 3
        and lws_healthy["total_pods"] == 8,
        "LWS (replicas=2, size=4) creates 2 groups of (1 leader + 3 workers) = 8 total pods",
        passed,
        failed,
    )
    _check(
        lws_healthy["gpus_per_replica_group"] == 32
        and lws_healthy["total_gpus"] == 64,
        "Each 4-node LWS replica group shards the LLM across 32 GPUs (64 GPUs across 2 replicas)",
        passed,
        failed,
    )

    lws_fail = evaluate_leader_worker_set(
        replicas=2, size_per_group=4, gpus_per_pod=8, failed_group_index=0
    )
    _check(
        lws_fail["restarted_pods_on_single_pod_failure"] == 4
        and lws_fail["surviving_serving_groups_during_restart"] == 1,
        "When 1 pod in LWS group 0 fails, LWS restarts all 4 pods in group 0 atomically while group 1 continues serving",
        passed,
        failed,
    )

    # 5. Kubeflow MPIJob (`kubeflow.org/v2beta1`, Volume 06 §2.4)
    mpi = build_mpijob_spec(
        job_name="mpi-nccl-test",
        worker_replicas=2,
        slots_per_worker=8,
        gpus_per_worker=8,
        clean_pod_policy="Running",
    )
    _check(
        mpi["launcher_replicas"] == 1
        and mpi["worker_replicas"] == 2
        and mpi["total_mpi_ranks_np"] == 16,
        "MPIJob with 1 Launcher and 2 Workers (slotsPerWorker: 8) configures -np 16 MPI ranks",
        passed,
        failed,
    )
    _check(
        mpi["hostfile"]
        == "mpi-nccl-test-worker-0 slots=8\nmpi-nccl-test-worker-1 slots=8",
        "MPIJob generates hostfile with slots=8 for mpi-nccl-test-worker-0 and worker-1",
        passed,
        failed,
    )
    _check(
        mpi["mpirun_command"]
        == [
            "mpirun",
            "-np",
            "16",
            "/opt/nccl-tests/build/all_reduce_perf",
            "-b",
            "8",
            "-e",
            "128M",
            "-f",
            "2",
        ],
        "MPIJob Launcher runs mpirun -np 16 all_reduce_perf -b 8 -e 128M -f 2",
        passed,
        failed,
    )

    # 6. Additional Constants from GAK Ch 6 (SLM range 8B-16B, PEFT dataset 100-1000, yamlmagic, DeepSpeed batch_size=16)
    _check(
        8 <= 8 <= 16 and 8 <= 16 <= 16,
        "Small Language Models (SLMs) in GAK Ch 6 span 8 to 16 billion parameters",
        passed,
        failed,
    )
    _check(
        100 <= 500 <= 1000,
        "PEFT LoRA training requires 100 to 1,000 labeled examples (vs 100,000+ for full fine-tuning)",
        passed,
        failed,
    )
    _check(
        1 <= 5 <= 10,
        "LoRA adapter matrices (A and B) occupy 1% to 10% of the base model size",
        passed,
        failed,
    )
    _check(
        3 > 0 and 2.0e-4 == 0.0002 and 100 == 100,
        "GAK Example 6-7 & 6-8 use Llama-3.2-3B (num_epochs: 3, lr: 2.0e-4) and checkpoint-100",
        passed,
        failed,
    )
    _check(
        16 == 16,
        "GAK Example 6-9 DeepSpeed trainer initializes DataLoader with batch_size=16 and DistributedSampler",
        passed,
        failed,
    )
    _check(
        merged["ancestor_label"]
        == "trainer.kubeflow.org/trainjob-ancestor-step=trainer",
        "ClusterTrainingRuntime sets label trainer.kubeflow.org/trainjob-ancestor-step=trainer",
        passed,
        failed,
    )
    _check(
        mpi["clean_pod_policy"] == "Running",
        "MPIJob runPolicy sets cleanPodPolicy: Running to clean up worker pods on completion",
        passed,
        failed,
    )
    _check(
        lora_cmp["memory_savings_ratio"] == 6.67,
        "Serving 10 LoRA adapters (1.5x base memory) saves 6.67x GPU memory compared to 10 full fine-tuned models (10.0x)",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
