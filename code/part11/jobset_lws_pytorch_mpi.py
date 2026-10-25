"""Chapter 11.9 — JobSet, LeaderWorkerSet, PyTorchJob and the MPI Operator.

Deterministic models for:
1. `PyTorchJob` (`kubeflow.org/v1`) rank, `WORLD_SIZE`, `MASTER_ADDR` headless
   DNS (`master-0.<job>.<ns>.svc.cluster.local`), and `MASTER_PORT` synthesis.
2. Kubeflow Trainer v2 (`trainer.kubeflow.org/v1alpha1`, `v2.1.0`) `TrainJob` +
   `ClusterTrainingRuntime` merger into a `JobSet` (`replicatedJobs`), plus
   Full Fine-Tuning vs PEFT LoRA parameter & dataset efficiency comparison
   (`< 1%` parameters tuned on `8B` model, `1%-10%` adapter size, `100-1000`
   examples vs `100,000+` examples).
3. `LeaderWorkerSet` (`LWS`, `leaderworkerset.x-k8s.io/v1`) replica-group sizing
   (`replicas` groups x `size` pods/group = `1` leader + `size-1` workers per
   sharded multi-node LLM inference replica) and group-atomic restart semantics.
4. `MPIJob` (`kubeflow.org/v2beta1`) hostfile generator and `mpirun -np` rank
   calculator (`Worker` `replicas: 2` x `slotsPerWorker: 8` = `-np 16`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


def synthesize_pytorchjob_env(
    job_name: str,
    namespace: str,
    master_replicas: int = 1,
    worker_replicas: int = 3,
    master_port: int = 23456,
) -> List[Dict[str, str]]:
    """Synthesize `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, and `RANK` for PyTorchJob pods."""
    if master_replicas != 1:
        raise ValueError("PyTorchJob requires exactly 1 Master pod (rank 0)")
    world_size = master_replicas + worker_replicas
    master_addr = f"{job_name}-master-0.{job_name}.{namespace}.svc.cluster.local"

    pods: List[Dict[str, str]] = []
    # Rank 0: Master-0
    pods.append(
        {
            "pod_name": f"{job_name}-master-0",
            "role": "master",
            "MASTER_ADDR": master_addr,
            "MASTER_PORT": str(master_port),
            "WORLD_SIZE": str(world_size),
            "RANK": "0",
        }
    )
    for w_idx in range(worker_replicas):
        pods.append(
            {
                "pod_name": f"{job_name}-worker-{w_idx}",
                "role": "worker",
                "MASTER_ADDR": master_addr,
                "MASTER_PORT": str(master_port),
                "WORLD_SIZE": str(world_size),
                "RANK": str(w_idx + 1),
            }
        )
    return pods


@dataclass(frozen=True)
class ClusterTrainingRuntimeSpec:
    """Kubeflow Trainer `ClusterTrainingRuntime` (`trainer.kubeflow.org/v1alpha1`)."""

    name: str = "my-torch-distributed-runtime"
    framework_label: str = "torch"
    default_num_nodes: int = 1
    num_proc_per_node: str = "auto"
    container_image: str = "pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime"


@dataclass(frozen=True)
class TrainJobSubmission:
    """Kubeflow Trainer `TrainJob` created via `TrainerClient.train()`."""

    job_name: str
    runtime_name: str
    num_nodes: int = 8
    cpu_per_node: int = 4
    memory_per_node: str = "64Gi"
    gpus_per_node: int = 1
    serialized_func_embedded: bool = True


def merge_trainjob_with_runtime(
    runtime: ClusterTrainingRuntimeSpec, job: TrainJobSubmission
) -> Dict[str, object]:
    """Simulate Kubeflow Trainer controller merging TrainJob + Runtime into a JobSet."""
    if runtime.name != job.runtime_name:
        raise ValueError("Runtime name mismatch")
    total_gpus = job.num_nodes * job.gpus_per_node
    total_cpus = job.num_nodes * job.cpu_per_node
    return {
        "generated_kind": "JobSet",
        "replicated_job_name": "node",
        "ancestor_label": "trainer.kubeflow.org/trainjob-ancestor-step=trainer",
        "framework": runtime.framework_label,
        "image": runtime.container_image,
        "num_nodes": job.num_nodes,
        "total_gpus": total_gpus,
        "total_cpus": total_cpus,
        "requires_image_rebuild_on_code_change": not job.serialized_func_embedded,
    }


def compare_full_finetuning_vs_lora(
    base_model_params_b: float = 8.0,
    lora_tuned_pct: float = 0.8,
    lora_adapter_size_pct: float = 5.0,
    num_adapters_served: int = 10,
) -> Dict[str, float]:
    """Compare Full Fine-Tuning vs PEFT LoRA (GAK Ch 6: <1% params tuned, 1-10% adapter size)."""
    full_ft_total_model_equiv = float(num_adapters_served)
    # 1 base model + N adapters each of size lora_adapter_size_pct%
    lora_total_model_equiv = 1.0 + num_adapters_served * (lora_adapter_size_pct / 100.0)
    tuned_params_m = base_model_params_b * 1000.0 * (lora_tuned_pct / 100.0)
    return {
        "tuned_params_millions": round(tuned_params_m, 2),
        "is_under_one_pct": 1.0 if lora_tuned_pct < 1.0 else 0.0,
        "full_ft_serving_footprint_models": round(full_ft_total_model_equiv, 2),
        "lora_serving_footprint_models": round(lora_total_model_equiv, 2),
        "memory_savings_ratio": round(
            full_ft_total_model_equiv / lora_total_model_equiv, 2
        ),
    }


def evaluate_leader_worker_set(
    replicas: int = 2,
    size_per_group: int = 4,
    gpus_per_pod: int = 8,
    failed_group_index: int | None = None,
) -> Dict[str, object]:
    """Model `LeaderWorkerSet` (`LWS`) for multi-node sharded LLM inference."""
    leaders_per_group = 1
    workers_per_group = size_per_group - 1
    total_pods = replicas * size_per_group
    gpus_per_replica_group = size_per_group * gpus_per_pod
    total_gpus = replicas * gpus_per_replica_group

    restarted_pods = size_per_group if failed_group_index is not None else 0
    surviving_groups = replicas - (1 if failed_group_index is not None else 0)
    return {
        "replicas": replicas,
        "size_per_group": size_per_group,
        "leaders_per_group": leaders_per_group,
        "workers_per_group": workers_per_group,
        "total_pods": total_pods,
        "gpus_per_replica_group": gpus_per_replica_group,
        "total_gpus": total_gpus,
        "restarted_pods_on_single_pod_failure": restarted_pods,
        "surviving_serving_groups_during_restart": surviving_groups,
    }


def build_mpijob_spec(
    job_name: str,
    worker_replicas: int = 2,
    slots_per_worker: int = 8,
    gpus_per_worker: int = 8,
    clean_pod_policy: str = "Running",
) -> Dict[str, object]:
    """Synthesize Kubeflow `MPIJob` (`kubeflow.org/v2beta1`) hostfile and `mpirun` command."""
    total_np = worker_replicas * slots_per_worker
    hostfile_lines = [
        f"{job_name}-worker-{i} slots={slots_per_worker}"
        for i in range(worker_replicas)
    ]
    mpirun_cmd = [
        "mpirun",
        "-np",
        str(total_np),
        "/opt/nccl-tests/build/all_reduce_perf",
        "-b",
        "8",
        "-e",
        "128M",
        "-f",
        "2",
    ]
    return {
        "launcher_replicas": 1,
        "worker_replicas": worker_replicas,
        "slots_per_worker": slots_per_worker,
        "total_mpi_ranks_np": total_np,
        "total_worker_gpus": worker_replicas * gpus_per_worker,
        "clean_pod_policy": clean_pod_policy,
        "hostfile": "\n".join(hostfile_lines),
        "mpirun_command": mpirun_cmd,
    }
