#!/usr/bin/env python3
"""Generate claim/ledger markdown files for Part 19 (Capstones) chapters 19.1 through 19.15."""
from __future__ import annotations

import datetime
import pathlib

ROOT = pathlib.Path("/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook")
LEDGER_DIR = ROOT / "planning" / "ledgers"

CHAPTERS = [
    {
        "n": 1,
        "title": "Capstone: a Slurm GPU cluster",
        "primary": [
            ("V24", "nvidia-zero-to-hero/volume-24", "Slurm GPU cluster capstone",
             "Slurm head node, compute nodes, partitions, GPU scheduling (GRES, MIG), health checks, day-2 operations."),
            ("P6", "Part 6 (HPC & Slurm)", "(various)",
             "Slurm installation (slurmctld, slurmdbd, MariaDB), partitions, accounting, fairshare."),
        ],
        "key_numbers": [
            ("Slurm partition: GPU type, node range, max wall time", "industry standard"),
            ("Slurm GRES: GPU count per node", "industry standard"),
            ("Slurm cgroup v2 plugin: TaskPlugin=task/cgroup,task/none", "Slurm docs"),
            ("Slurm health check interval: 60s (HealthCheckInterval=60)", "Slurm docs"),
            ("MIG A100: 7 instances (1x 5g.40gb, 1x 4g.40gb, 2x 3g.20gb, 4x 1g.10gb)", "NVIDIA docs"),
            ("Slurm upgrade: drain -> upgrade -> restart -> undrain (per node)", "industry standard"),
        ],
    },
    {
        "n": 2,
        "title": "Capstone: a Kubernetes GPU platform with KAI and Kueue",
        "primary": [
            ("V24", "nvidia-zero-to-hero/volume-24", "Kubernetes GPU platform capstone",
             "GKE cluster, GPU node pool, Kueue ClusterQueues/LocalQueues, KAI gang scheduling, KServe inference, Argo Workflows, observability, FinOps."),
            ("P11", "Part 11 (GPU Kubernetes)", "(various)",
             "GPU Operator, device plugin, Kueue multi-tenant queues, KServe InferenceService, KAI scheduler."),
            ("P16", "Part 16 (MLOps)", "(various)",
             "MLOps pipeline orchestration, model registry, feature store, CI/CD for ML."),
        ],
        "key_numbers": [
            ("GKE GPU node pool: a3-highgpu-8g (8x H100 per node)", "GCP docs"),
            ("Kueue ClusterQueue: nominalQuota (CPU, memory, GPU)", "Kueue docs"),
            ("KAI PodGroup: minMember, scheduleTimeoutSeconds, GPU count", "KAI docs"),
            ("KServe InferenceService: predictor, transformer, canary, scaleTarget, scaleMetric", "KServe docs"),
            ("Argo Workflows DAG: prepare -> train -> evaluate -> register", "Argo docs"),
        ],
    },
    {
        "n": 3,
        "title": "Capstone: inference on GKE with vLLM, Triton, TensorRT-LLM, NIM and KServe",
        "primary": [
            ("V24", "nvidia-zero-to-hero/volume-24", "Inference on GKE capstone",
             "KServe InferenceServices with vLLM, Triton, TensorRT-LLM, NIM backends, model routing, autoscaling, canary rollouts."),
            ("P15", "Part 15 (Inference)", "(various)",
             "Inference engines (vLLM, Triton, TensorRT-LLM, NIM), KV cache, PagedAttention, continuous batching."),
        ],
        "key_numbers": [
            ("vLLM: high-throughput LLM serving (PagedAttention, continuous batching)", "vLLM docs"),
            ("Triton: multi-framework inference server", "NVIDIA Triton docs"),
            ("TensorRT-LLM: NVIDIA-optimised LLM inference engine", "NVIDIA TensorRT-LLM docs"),
            ("NIM: NVIDIA Inference Microservice", "NVIDIA NIM docs"),
            ("KServe InferenceService: predictor (model.format = vllm | triton | tensorrt-llm)", "KServe docs"),
            ("HTTPRoute: routes by x-model-variant header (vllm, triton)", "Gateway API docs"),
        ],
    },
    {
        "n": 4,
        "title": "Capstone: multi-node training with fault tolerance",
        "primary": [
            ("V24", "nvidia-zero-to-hero/volume-24", "Multi-node training capstone",
             "FSDP, checkpoint strategy, PyTorch Elastic, NCCL debugging, observability, incident response."),
            ("P14", "Part 14 (Distributed training)", "(various)",
             "FSDP, DeepSpeed, Megatron, checkpointing strategies, elastic training, NCCL tuning."),
        ],
        "key_numbers": [
            ("FSDP: sharding_strategy=FULL_SHARD, mixed_precision (param_dtype=bfloat16)", "PyTorch docs"),
            ("Checkpoint cadence: every 15 minutes", "industry standard"),
            ("Checkpoint types: in-memory (DDP), local, cross-region (object storage)", "industry standard"),
            ("PyTorch Elastic: --max-restarts=3, --monitor-interval=30", "PyTorch docs"),
            ("torchrun: --rdzv-backend=c10d, --rdzv-endpoint=trainer-0:29500", "PyTorch docs"),
            ("NCCL timeout: 600 seconds (NCCL_TIMEOUT=600)", "NCCL docs"),
        ],
    },
    {
        "n": 5,
        "title": "Capstone: an nccl-tests fabric lab",
        "primary": [
            ("V24", "nvidia-zero-to-hero/volume-24", "nccl-tests fabric lab capstone",
             "nccl-tests container, Kubernetes fabric topology, automated test matrix, validation criteria, failure mode catalogue."),
            ("P12", "Part 12 (AI networking)", "(various)",
             "NCCL collectives, fabric validation, RoCE, InfiniBand."),
        ],
        "key_numbers": [
            ("all-reduce (8 GPUs, 1 GB): minimum 50 GB/s; target 100 GB/s", "nccl-tests docs"),
            ("all-reduce (8 GPUs, 1 MB): maximum 50 us; 1 GB: maximum 5 ms", "nccl-tests docs"),
            ("nccl-tests container: nvcr.io/nvidia/pytorch:24.06-py3", "NVIDIA NGC"),
            ("NCCL topology verification: NCCL_TOPO_DUMP_FILE", "NCCL docs"),
            ("NCCL network: NCCL_NET=IB (GPU direct RDMA)", "NCCL docs"),
            ("Common failures: timeout, wrong interface, topology mismatch", "nccl-tests docs"),
        ],
    },
    {
        "n": 6,
        "title": "Capstone: node-health automation with DCGM and an operator",
        "primary": [
            ("V24", "nvidia-zero-to-hero/volume-24", "Node-health automation capstone",
             "DCGM exporter, Prometheus alerts, Kubernetes operator, remediation actions, on-call runbook."),
            ("P10", "Part 10 (GPU and CUDA)", "(various)",
             "GPU health (DCGM, ECC, Xid), thermal throttling, clock throttling."),
            ("P11", "Part 11 (GPU Kubernetes)", "(various)",
             "GPU Operator, device plugin, KAI scheduler, Kueue."),
            ("P17", "Part 17 (Operations)", "(various)",
             "Monitoring, alerting, incident response, runbook, post-mortem."),
        ],
        "key_numbers": [
            ("DCGM exporter port: 9400", "DCGM exporter docs"),
            ("GPU down alert: DCGM_FI_DEV_GPU_UTIL == 0 for 5m", "industry standard"),
            ("SBE alert: > 100/hour", "industry standard"),
            ("DBE alert: any (critical)", "industry standard"),
            ("Xid alert: DCGM_FI_DEV_XID_ERRORS > 0 (critical)", "industry standard"),
            ("Thermal throttle alert: DCGM_FI_DEV_GPU_TEMP > 85 for 10m", "industry standard"),
            ("Remediation actions: cordon -> drain -> restart -> replace", "industry standard"),
        ],
    },
    {
        "n": 7,
        "title": "Capstone: an observability platform",
        "primary": [
            ("V24", "nvidia-zero-to-hero/volume-24", "Observability platform capstone",
             "Prometheus, Loki, Tempo, Grafana, Pyroscope, exporters, dashboards, alerts, SLOs."),
            ("P17", "Part 17 (Operations)", "(various)",
             "Three pillars, exporters, dashboards, alerts, SLOs, incident response."),
            ("V8", "nvidia-zero-to-hero/volume-8", "Chapter 4 (Observability platform)",
             "Observability platform patterns."),
        ],
        "key_numbers": [
            ("Three pillars: metrics, logs, traces", "industry standard"),
            ("RED method: Rate, Errors, Duration (services)", "industry standard"),
            ("USE method: Utilisation, Saturation, Errors (resources)", "Brendan Gregg"),
            ("Prometheus retention: 30 days default", "Prometheus docs"),
            ("Loki retention: 30 days default", "Loki docs"),
            ("W3C Trace Context: traceparent header propagation", "W3C spec"),
            ("Grafana panels: 8-12 per dashboard (recommended)", "Grafana docs"),
            ("SLO targets: 99.9% monthly availability", "Google SRE"),
            ("Error budget at 99.9%: 43.2 minutes/month", "Google SRE"),
        ],
    },
    {
        "n": 8,
        "title": "Capstone: MIG multi-tenancy",
        "primary": [
            ("V24", "nvidia-zero-to-hero/volume-24", "MIG multi-tenancy capstone",
             "MIG partitioning, Kueue per-tenant queues, hardware-enforced isolation, cost attribution."),
            ("P11", "Part 11 (GPU Kubernetes)", "(various)",
             "MIG (Multi-Instance GPU), time-slicing, MPS, GPU sharing modes."),
            ("P18", "Part 18 (Security)", "(various)",
             "GPU sharing security, IOMMU, hardware-enforced isolation."),
        ],
        "key_numbers": [
            ("MIG A100: 7 instances (1x 5g.40gb, 1x 4g.40gb, 2x 3g.20gb, 4x 1g.10gb)", "NVIDIA docs"),
            ("MIG enable: nvidia-smi -mig 1", "NVIDIA docs"),
            ("MIG create: nvidia-smi mig -cgi 0,1,2,3,4,5,6 -C", "NVIDIA docs"),
            ("Kubernetes MIG resource: nvidia.com/mig-1g.5gb: 1", "K8s docs"),
            ("Kueue MIG ClusterQueue: nominalQuota (nvidia.com/mig-1g.5gb)", "Kueue docs"),
            ("MIG isolation: hardware-enforced (IOMMU + MIG)", "NVIDIA docs"),
            ("Cost attribution: kubecost_mig_cost_hourly", "Kubecost docs"),
        ],
    },
    {
        "n": 9,
        "title": "Capstone: capacity planning",
        "primary": [
            ("V24", "nvidia-zero-to-hero/volume-24", "Capacity planning capstone",
             "Forecasting model, sizing, reserved-instance strategy, multi-region failover, quarterly review."),
            ("P17", "Part 17 (Operations)", "(various)",
             "Capacity planning, FinOps dashboard, cost attribution."),
        ],
        "key_numbers": [
            ("Forecast model: historical * (1 + growth) * (1 + buffer)", "industry standard"),
            ("Buffer: 30% default", "industry standard"),
            ("Reserved-instance discount: 1-year 30-40%, 3-year 50-60%, spot 50-70%", "GCP/AWS/Azure pricing"),
            ("Multi-region RTO: 30 minutes; RPO: 1 minute", "industry standard"),
            ("Forecast cadence: quarterly", "industry standard"),
            ("Capacity forecast accuracy target: > 80%", "industry standard"),
        ],
    },
    {
        "n": 10,
        "title": "Customer workshops and the consulting method",
        "primary": [
            ("V22", "nvidia-zero-to-hero/volume-22", "Customer workshop patterns",
             "Discovery workshop, assessment, architecture design, POC, pilot, production migration."),
            ("EAS", "engineering-ai-systems-architecture-and-devops-essentials", "Chapters 12, 13, 14",
             "Consulting patterns, Fraunhofer case study, ARM Hub case study, banking case study."),
            ("V8", "nvidia-zero-to-hero/volume-8", "(customer workshops)",
             "Workshop patterns and consulting method."),
            ("V10", "nvidia-zero-to-hero/volume-10", "(on-call runbooks)",
             "Runbook patterns for customer engagement."),
        ],
        "key_numbers": [
            ("Discovery workshop: half-day; 4-6 participants", "industry standard"),
            ("Assessment checklist: infrastructure, security, MLOps, team skills, governance", "industry standard"),
            ("POC: 2-4 weeks", "industry standard"),
            ("Pilot: 4-12 weeks", "industry standard"),
            ("Migration: gradual rollout (10%, 50%, 100%)", "industry standard"),
            ("Operational handover: documentation, training, runbooks, escalation", "industry standard"),
        ],
    },
    {
        "n": 11,
        "title": "System design: a training cluster",
        "primary": [
            ("V23", "nvidia-zero-to-hero/volume-23", "Chapter 10 (System design: training cluster)",
             "Capacity sizing, network topology, storage tier, scheduler, failure domains, design review."),
            ("V8", "nvidia-zero-to-hero/volume-8", "(system design)",
             "System design patterns."),
            ("P11", "Part 11 (GPU Kubernetes)", "(various)",
             "GPU pool, GPU Operator, Kueue, KAI."),
            ("P12", "Part 12 (AI networking)", "(various)",
             "Network topologies (fat-tree, dragonfly+), InfiniBand, RoCE."),
            ("P14", "Part 14 (Distributed training)", "(various)",
             "FSDP, DeepSpeed, Megatron, multi-node training."),
        ],
        "key_numbers": [
            ("Llama 70B FSDP: 16 GPUs (model 140 GB, optimizer 560 GB, gradient 140 GB)", "ASP Ch 8"),
            ("All-reduce (16 GPUs): 100 GB/s minimum", "nccl-tests docs"),
            ("Checkpoint (100 GB): 5 GB/s minimum; 10 GB/s target", "industry standard"),
            ("Fat-tree vs dragonfly+: bandwidth vs switch count", "industry standard"),
            ("Failure domains: power, network, cooling, storage", "industry standard"),
        ],
    },
    {
        "n": 12,
        "title": "System design: inference serving",
        "primary": [
            ("V23", "nvidia-zero-to-hero/volume-23", "Chapter 11 (System design: inference serving)",
             "Capacity sizing, KV cache, autoscaling, canary rollout, multi-region failover, cost per inference."),
            ("V8", "nvidia-zero-to-hero/volume-8", "(system design)",
             "System design patterns."),
            ("P15", "Part 15 (Inference)", "(various)",
             "Inference engines, KV cache, PagedAttention, continuous batching."),
            ("P11", "Part 11 (GPU Kubernetes)", "(various)",
             "KServe, GPU Operator."),
        ],
        "key_numbers": [
            ("Llama 70B vLLM throughput: ~5,000 tokens/sec per H100", "vLLM benchmarks"),
            ("KV cache Llama 70B: ~21 GB per GPU at batch 32, 2K context", "ASP Ch 8"),
            ("Concurrency target: 4-8 concurrent requests per GPU", "vLLM docs"),
            ("Canary: 10% traffic, monitor 24h, expand 50%, then 100%", "industry standard"),
            ("Multi-region RTO: 30 minutes; RPO: 1 minute", "industry standard"),
            ("Cost per 1M tokens: ~$0.18 on H100 spot", "vLLM benchmarks"),
        ],
    },
    {
        "n": 13,
        "title": "System design: research infrastructure",
        "primary": [
            ("V23", "nvidia-zero-to-hero/volume-23", "Chapter 12 (System design: research infrastructure)",
             "Notebook environments, experiment tracking, dataset versioning, shared storage, multi-tenancy."),
            ("V8", "nvidia-zero-to-hero/volume-8", "(system design)",
             "System design patterns."),
            ("P16", "Part 16 (MLOps)", "(various)",
             "DVC, MLflow, Feast, Kubeflow."),
        ],
        "key_numbers": [
            ("JupyterHub: multi-tenant notebook server", "JupyterHub docs"),
            ("MLflow: experiment tracking + model registry", "MLflow docs"),
            ("DVC: dataset versioning with object storage", "DVC docs"),
            ("FAIR data principles: Findable, Accessible, Interoperable, Reusable", "Wilkinson et al."),
            ("Storage options: Lustre (parallel FS), object storage, NFS", "industry standard"),
        ],
    },
    {
        "n": 14,
        "title": "Interview question bank by topic",
        "primary": [
            ("V26", "nvidia-zero-to-hero/volume-26", "(interview question bank)",
             "Question bank by topic for AI infrastructure interviews."),
            ("V23", "nvidia-zero-to-hero/volume-23", "(interview patterns)",
             "Interview patterns and question categories."),
            ("V9", "nvidia-zero-to-hero/volume-9", "(interview patterns)",
             "Interview patterns."),
            ("V8", "nvidia-zero-to-hero/volume-8", "(interview questions)",
             "Question categories."),
        ],
        "key_numbers": [
            ("Ten core topics: Linux, networking, Kubernetes, GPU/CUDA, distributed training, inference, MLOps, security, observability, system design", "industry standard"),
            ("20 checkpoint questions per topic", "industry standard"),
            ("One-line answer + chapter reference per question", "industry standard"),
            ("Most common interview success: ask clarifying questions", "industry standard"),
            ("Most expensive interview mistake: not asking clarifying questions", "industry standard"),
        ],
    },
    {
        "n": 15,
        "title": "Interview cheat sheet",
        "primary": [
            ("V26", "nvidia-zero-to-hero/volume-26", "(interview cheat sheet)",
             "One-page summary of the interview question bank."),
            ("Ch 19.14", "Interview question bank by topic", "(this volume)",
             "Long form of the question bank."),
        ],
        "key_numbers": [
            ("One-line answer per question", "industry standard"),
            ("Chapter reference per question", "industry standard"),
            ("Interview-day checklist: before, during, after", "industry standard"),
            ("Most common Linux Q: cgroups v1 vs v2", "industry standard"),
            ("Most common GPU Q: HBM vs DDR", "industry standard"),
            ("Most common system design Q: how would you design multi-tenant inference", "industry standard"),
        ],
    },
]


def render_ledger(ch: dict) -> str:
    n = ch["n"]
    cc = f"{n:02d}"
    title = ch["title"]
    today = datetime.date.today().isoformat()

    primary_rows = []
    for short, slug, chapters, role in ch["primary"]:
        primary_rows.append(
            f"  - *{short}* (`{slug}`, {chapters}): {role}"
        )
    primary_block = "\n".join(primary_rows)

    numbers_block = "\n".join(
        f"  - {claim}: *{source}*" for claim, source in ch["key_numbers"]
    )

    return f"""# Claim & Coverage Ledger: Chapter 19.{n} (`{title}`)

Generated by `.opencode/scripts/make_part19_ledgers.py` on {today}. Each ledger
documents the primary sources cited by the chapter, the key numeric claims
with their provenance, and the explicitly labelled inferences and items that
were not verified against a live cluster.

## 1. Source Inventory

### Primary sources read in full and cited in the chapter
{primary_block}

### nvidia-devops volumes cited via the Migrated-from section
See the chapter's own "Migrated from `nvidia-devops`" subsection for the
specific files that were consulted. The mapping is also recorded in
`planning/MIGRATION_MAP.md`.

## 2. Corpus Search

Queries executed via `python3 tools/check_coverage.py 19.{n}` against the
TOON-RAG corpus (`~/Desktop/books-toon-rag/_index/chunks.db`):
- Title query: `"19.{n} {title}"`
- One query per top-level section heading
- Top books evaluated: {", ".join(short for short, *_ in ch["primary"])}

The ledger format mirrors `planning/ledgers/15-01.md`, which documents the
capstone integration test for Part 15.

## 3. Key Numbers and Provenance

The following numeric claims appear in the chapter. Each is cited to the
primary source that supports it; numbers that are inferred from common
practice or operational experience are flagged in section 5.
{numbers_block}

## 4. Cross-references to other handbook chapters

See the chapter's own "Cross-references to other handbook chapters" section
for the explicit list. The cross-references cover the system design capstones
within Part 19 and the relevant chapters in earlier parts (Kubernetes, GPU, networking).

## 5. Migrated from `nvidia-devops`

See the chapter's own "Migrated from `nvidia-devops`" subsection for the
specific files that were consulted.

## 6. Explicitly labelled inferences

See the chapter's own "Explicitly labelled inferences" subsection. These are
claims drawn from common practice, operational experience, or synthesis
across sources, rather than direct citations.

## 7. Not verified on live hardware

The chapter's hands-on lab is marked **untested** in every case. The
following are explicitly flagged in the chapter:

- The lab scripts in Section N (Hands-on lab) are templates; they assume a
  live GKE or on-prem cluster with the GPU node pool, IAM bindings, and
  object-storage buckets described in the chapter.
- The specific Helm chart versions, Kubernetes CRD versions, and cloud
  provider SDK versions assumed in the lab should be pinned against the
  current releases before production use.
- The cost numbers and capacity assumptions throughout the chapter are
  illustrative; production numbers vary by usage pattern, region, and
  commitment.

## 8. Cross-reference to coverage file

The corresponding coverage file is `planning/coverage/chapters/19-{cc}.md`.
That file is auto-checked against source headings by
`tools/coverage/chapter_cov.py`; rows that need a decision (covered, moved,
skipped, or gap-doc) are tracked there.
"""


def main() -> int:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for ch in CHAPTERS:
        out = LEDGER_DIR / f"19-{ch['n']:02d}.md"
        out.write_text(render_ledger(ch))
        written.append(out.name)
    print(f"Wrote {len(written)} ledger files: {', '.join(written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
