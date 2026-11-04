---
id: "c16-04"
title: "16.4 Pipeline orchestration: Kubeflow Pipelines, Argo, Flyte, Airflow"
sidebar_label: "16.4 Pipeline orchestration"
sidebar_position: 4
description: "Pipeline orchestration for ML: Argo Workflows, Kubeflow Pipelines, Flyte, Airflow. DAG execution models, retries, caching, artefact passing, GPU pool integration, secret and IAM management, and the operational pattern that ties the orchestrator to the tracker, registry, and feature store."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 16.4 Pipeline orchestration: Kubeflow Pipelines, Argo, Flyte, Airflow

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | GCP / GKE |
| Part | Part 16: MLOps and LLMOps tools and platforms |
| Primary sources | *Designing Machine Learning Systems* (`designing-machine-learning-systems`, Chapter 10); *Machine Learning Platform Engineering* (`machine-learning-platform-engineering`, Chapters 1, 5, 6); *Practical MLOps* (`practical-mlops`, Chapter 5); Argo, Kubeflow, Flyte and Airflow official documentation |
| Cross-references | Chapter 16.1 (MLOps foundations); Chapter 16.2 (Experiment tracking); Chapter 16.3 (Data pipelines and feature stores); Chapter 11.16 (KAI gang scheduling) |
| Coverage file | `planning/coverage/chapters/16-04.md` |
| Claim & number ledger | `planning/ledgers/16-04.md` |

## Why this matters for AI infrastructure

The previous chapters defined what an ML pipeline is. This chapter is about the system that actually runs it. An orchestrator is the runtime that schedules the DAG, retries failed stages, caches skipped stages, surfaces run records, and feeds the tracker and the registry. On a Kubernetes cluster, the orchestrator is the difference between a notebook that runs once and a pipeline that runs every night at 2 a.m. without paging anyone.

If you operate a GPU cluster for AI, you operate an orchestrator. The orchestrator is what schedules the training jobs, the data pipelines, the model-build pipelines, the feature materialisations, and the retraining triggers. It is also what runs the validation suite, the promotion gate, the canary deployment, and the rollback. It is on the critical path for almost every MLOps workflow; when the orchestrator is slow or down, every pipeline is slow or down.

```text
Why the orchestrator is on the critical path (DMLS Ch 10; MLPE Ch 5):
- A typical mature MLOps platform runs dozens to hundreds of DAGs per day across
  teams (training, retraining, feature materialisation, evaluation, deployment).
- Each DAG has between 5 and 50 stages; each stage has its own resource request,
  retry policy, and SLA. The orchestrator's job is to keep all of them on schedule.
- The orchestrator's metadata database (Postgres) is the audit trail for every
  pipeline run. A metadata database that is slow or wiped is the same failure as
  losing the audit log.
```

Three operational realities make this chapter a platform-team concern rather than a data-science-only concern:

1. **The orchestrator owns the GPU quota.** Every training job that the orchestrator schedules is a Kubernetes pod that requests GPU resources. The orchestrator's queue is the gate between a data scientist's `kubectl apply` and the GPU nodes. The platform team owns the queue and the quota.
2. **The orchestrator is a stateful service.** The Postgres backend, the artifact store, the IAM model and the SLO are platform-team decisions. The orchestrator's metadata is the audit trail for every ML pipeline run; its loss is the same as losing the Git history.
3. **The orchestrator is the entry point for retries and backfills.** When a stage fails, the orchestrator decides whether to retry, fail-fast, or fall back. When a feature store is rebuilt, the orchestrator decides which downstream stages to invalidate and re-run. The platform team owns the policy.

**Before a training job runs on your cluster, the orchestrator that schedules it must be a production service with an SLO. An orchestrator that is best-effort is an orchestrator that pages you at 2 a.m.**

## Prerequisites and outcomes

### Prerequisites

- Chapter 16.1 (the lifecycle and the four pillars).
- Chapter 16.2 (experiment tracking and registry).
- Chapter 16.3 (data pipelines and feature stores).
- Chapter 5 (Kubernetes) for the cluster primitives the orchestrator depends on.
- Familiarity with YAML, container images, and basic CI/CD concepts.

### Outcomes

After completing this chapter you will be able to:

1. Compare Argo Workflows, Kubeflow Pipelines, Flyte and Airflow on execution model, artefact handling, caching, retry semantics, IAM and ecosystem fit.
2. Build a DAG that runs training, evaluation, validation, promotion, and materialisation stages with explicit dependencies and resource requests.
3. Wire a stage to GPU node pools with the right queue, priority and topology binding, and understand why default Kubernetes scheduling is not enough for gang-scheduled multi-GPU jobs.
4. Pass artefacts between stages (content hashes, model URIs, dataset ids, feature table ids) without leaking them through the cluster's file system.
5. Implement retry policies, caching, conditional branches and parameter sweeps.
6. Operate the orchestrator on GKE with a Postgres backend, object-store artefacts, IAM, secrets, and observability.

---

## 1. The four orchestrators and how they differ

### 1.0 The orchestrator as the surface where Kaizen happens

*Practical MLOps* Chapter 5 introduces AutoML and KaizenML under the framing of continuous improvement. The orchestrator is the surface where that philosophy becomes structural. Every pipeline run is a hypothesis; the orchestrator is the system that records the hypothesis, runs the experiment, and feeds the result back into the next iteration.

The Kaizen discipline says three things about an orchestrator:

1. **Every step is recorded.** The orchestrator's metadata store is the audit log of every improvement that the team has made.
2. **Every step is reproducible.** The orchestrator's artefact store is the source of truth for every artefact that the team has produced.
3. **Every step is reversible.** The orchestrator's deployment layer (Argo Rollouts, KServe canary) is the rollback path that makes a bad improvement recoverable in minutes, not hours.

An orchestrator that satisfies the three conditions is the structural mechanism that turns "be more disciplined" into "the discipline is the system". An orchestrator that fails any of the three is a notebook with extra steps.

### 1.1 A unified mental model

The four orchestrators in production today look different on the surface but share the same conceptual model.

```mermaid
flowchart LR
    subgraph DAG["DAG definition (YAML or Python)"]
        D1[Stage A]
        D2[Stage B]
        D3[Stage C]
        D4[Stage D]
    end

    subgraph Scheduler["Scheduler and queue"]
        S1[Pick stage<br/>respect dependencies]
        S2[Allocate resources<br/>GPU pool, namespace]
        S3[Launch pod]
    end

    subgraph Runtime["Runtime (Kubernetes pod)"]
        R1[Container image]
        R2[Inputs from prior stage]
        R3[Outputs (artefacts)]
    end

    subgraph Metadata["Metadata store"]
        M1[Run record]
        M2[Stage status]
        M3[Lineage]
    end

    D1 --> S1
    D2 --> S1
    D3 --> S1
    D4 --> S1
    S1 --> S2 --> S3
    S3 --> R1
    R2 --> R1
    R1 --> R3
    R3 --> M1
    R2 --> M2
    R3 --> M3
```

Every orchestrator has four components: a DAG definition language, a scheduler that respects dependencies and resources, a runtime that runs each stage as a container, and a metadata store that records runs and lineage. The differences are in the language (YAML vs Python), the scheduler (Kubernetes-native vs custom), the runtime (container vs task), and the metadata store (Postgres vs separate service).

### 1.2 Argo Workflows

Argo Workflows is a Kubernetes-native orchestrator. DAGs are defined in YAML; each stage is a Kubernetes pod; the metadata store is a Postgres database inside the cluster. Argo is the lightest of the four for teams that already run Kubernetes; it has no Python abstraction layer and no hidden services.

```yaml
# code/part16/argo_dag.yaml (shape only)
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: training-pipeline-
spec:
  entrypoint: pipeline
  arguments:
    parameters:
      - {name: dataset-id, value: "churn-v3"}
      - {name: seed, value: "42"}
  templates:
    - name: pipeline
      dag:
        tasks:
          - name: prepare
            template: prepare
            arguments:
              parameters: [{name: dataset-id, value: "{{workflow.parameters.dataset-id}}"}]
          - name: train
            template: train
            dependencies: [prepare]
            arguments:
              parameters: [{name: dataset-id, value: "{{workflow.parameters.dataset-id}}"},
                           {name: seed, value: "{{workflow.parameters.seed}}"}]
          - name: evaluate
            template: evaluate
            dependencies: [train]
          - name: register
            template: register
            dependencies: [evaluate]
```

*Designing Machine Learning Systems* Chapter 10 makes Argo the default for Kubernetes-native MLOps. *Machine Learning Platform Engineering* Chapter 5 introduces Argo Workflows as the orchestrator that runs the DAG declared in `dvc.yaml`.

### 1.3 Kubeflow Pipelines

Kubeflow Pipelines (KFP) is the orchestrator that ships with the Kubeflow Kubernetes-native ML platform. DAGs are defined in Python using the KFP SDK; each stage is compiled to an Argo Workflow under the hood and submitted to the cluster. KFP adds a UI for run inspection, a metadata store for artefacts, and a typed input/output system that catches schema mismatches at compile time.

```python
# code/part16/kfp_pipeline.py (shape only)
import kfp
from kfp import dsl

@dsl.component(
    base_image="python:3.11",
    packages_to_install=["pandas", "scikit-learn"],
)
def prepare_op(dataset_id: str, output_path: dsl.OutputPath()):
    import pandas as pd
    df = pd.read_parquet(f"data/{dataset_id}.parquet")
    df.to_parquet(output_path)

@dsl.component(
    base_image="nvidia/cuda:12.2.0-runtime-ubuntu22.04",
    packages_to_install=["pandas", "scikit-learn", "mlflow"],
)
def train_op(input_path: dsl.InputPath(), seed: int) -> str:
    import mlflow, pandas as pd
    from sklearn.ensemble import GradientBoostingClassifier
    df = pd.read_parquet(input_path)
    mlflow.set_experiment("churn")
    with mlflow.start_run() as run:
        mlflow.log_param("seed", seed)
        model = GradientBoostingClassifier(random_state=seed)
        model.fit(df.drop("churned", axis=1), df["churned"])
    return run.info.run_id

@dsl.pipeline(name="Churn Training Pipeline")
def training_pipeline(dataset_id: str = "churn-v3", seed: int = 42):
    p = prepare_op(dataset_id=dataset_id)
    t = train_op(input_path=p.output, seed=seed)

if __name__ == "__main__":
    kfp.compiler.Compiler().compile(training_pipeline, "pipeline.yaml")
    kfp.Client().create_run_from_pipeline_package("pipeline.yaml")
```

The typed input/output system catches a class of bugs at compile time that YAML DAGs catch only at runtime. *Machine Learning Platform Engineering* Chapter 6 walks through KFP as the orchestrator that ships with a metadata-aware UI.

### 1.4 Flyte

Flyte is the orchestrator that originated at Lyft. It treats each stage as a typed task; the inputs and outputs are declared with type annotations; the runtime enforces the types and the dependency graph. Flyte has the strongest type system of the four and the strongest support for conditional execution and dynamic workflows.

```python
# code/part16/flyte_pipeline.py (shape only)
from flytekit import task, workflow

@task(requests=Resources(cpu="2", mem="4Gi"))
def prepare(dataset_id: str) -> str:
    import pandas as pd
    df = pd.read_parquet(f"data/{dataset_id}.parquet")
    df.to_parquet("/tmp/clean.parquet")
    return "/tmp/clean.parquet"

@task(requests=Resources(cpu="4", mem="16Gi", gpu="1"))
def train(clean_path: str, seed: int) -> str:
    import mlflow, pandas as pd
    from sklearn.ensemble import GradientBoostingClassifier
    df = pd.read_parquet(clean_path)
    mlflow.set_experiment("churn")
    with mlflow.start_run() as run:
        mlflow.log_param("seed", seed)
        model = GradientBoostingClassifier(random_state=seed)
        model.fit(df.drop("churned", axis=1), df["churned"])
    return run.info.run_id

@workflow
def training_pipeline(dataset_id: str = "churn-v3", seed: int = 42) -> str:
    p = prepare(dataset_id=dataset_id)
    t = train(clean_path=p, seed=seed)
    return t
```

Flyte's type system and its first-class support for `pandas.DataFrame`, `numpy.ndarray`, and structured types make it the strongest fit for data-engineering-heavy ML pipelines. *Practical MLOps* Chapter 5 walks through Flyte as the orchestrator that originated in production at Lyft and has grown into an open-source project under the Linux Foundation.

### 1.5 Airflow

Airflow is the oldest of the four and the most widely adopted outside Kubernetes-native teams. DAGs are defined in Python; each task is a unit of work that can be a Kubernetes pod, a Spark job, a database query, or an HTTP call; the metadata store is a Postgres or MySQL database. Airflow's strength is its ecosystem of operators and the size of its community; its weakness is that its Kubernetes integration is layered on top of the original scheduler rather than native to it.

```python
# code/part16/airflow_dag.py (shape only)
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime, timedelta

with DAG(
    dag_id="churn_training",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@weekly",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
) as dag:
    prepare = KubernetesPodOperator(
        name="prepare",
        image="python:3.11",
        cmds=["python", "prepare.py"],
        arguments=["--dataset-id", "churn-v3"],
    )
    train = KubernetesPodOperator(
        name="train",
        image="nvidia/cuda:12.2.0-runtime-ubuntu22.04",
        cmds=["python", "train.py"],
        arguments=["--dataset-id", "churn-v3", "--seed", "42"],
    )
    prepare >> train
```

*Designing Machine Learning Systems* Chapter 10 walks through Airflow as the orchestrator that data engineering teams adopt when they already run Airflow for non-ML workloads. The cost is that Airflow does not speak Kubernetes natively; the benefit is that the same operator pattern runs Spark, BigQuery, Snowflake, and HTTP tasks alongside the Kubernetes pod.

### 1.6 Comparison

| Dimension | Argo Workflows | Kubeflow Pipelines | Flyte | Airflow |
|---|---|---|---|---|
| Definition language | YAML | Python SDK | Python SDK (typed) | Python SDK |
| Runtime | Kubernetes pod | Kubernetes pod (under Argo) | Kubernetes pod | Kubernetes pod via operator |
| Metadata store | Postgres | MLMD (Protobuf + MySQL/Postgres) | Postgres | Postgres/MySQL |
| Caching | Pod-level cache | Step-level cache | Task-level cache (content-hash) | None (built-in) |
| Retry | Pod retries | Step retries | Task retries | Task retries |
| Conditional execution | Yes (when, if) | Yes (conditions) | Yes (dynamic workflows) | Yes (branch, short-circuit) |
| GPU support | Native (resource requests) | Native (resource requests, GPU pool operand) | Native (Resources(gpu=1)) | Via KubernetesPodOperator |
| UI | Argo UI | KFP UI (rich) | Flyte UI (FlyteConsole) | Airflow UI |
| IAM | Kubernetes RBAC + service accounts | Kubernetes RBAC + service accounts | Kubernetes RBAC + service accounts | Kubernetes RBAC + service accounts |
| Best fit | Kubernetes-native teams; DAGs with simple dependencies | Teams already on Kubeflow; need typed artefacts and a rich UI | Data-engineering-heavy ML; strong type system; dynamic workflows | Teams already on Airflow for non-ML workloads; large ecosystem |

The choice between them is rarely about features. It is about which team will operate it, which ecosystem is already in the cluster, and how much Python abstraction the team can absorb.

---

## 2. Building a DAG that actually runs

### 2.1 The shape of a production pipeline

A production ML pipeline has eight stages; each stage has an artifact, a gate, and a resource request.

| Stage | Artifact | Gate | Resource request |
|---|---|---|---|
| Ingest | Raw snapshot | Schema check; row count | Small CPU node |
| Transform | Cleaned snapshot | Null-rate check; join-key check | Small to medium CPU node |
| Feature engineering | Feature table | Distribution check; leakage check | Medium CPU or small GPU (for embeddings) |
| Validate data | Validation report | All expectations pass | Small CPU node |
| Train | Run record + model artifact | Run record has all required tags | GPU pool (gang scheduled for multi-GPU) |
| Evaluate | Evaluation report | Baseline beat; segment metrics | GPU pool (inference, not training) |
| Promote | Registry entry | Promotion gate passes | Small CPU node |
| Deploy | Live model in serving | Canary error budget OK | Small CPU node (deploys via KServe/Argo Rollouts) |

The DAG is a sequence of these stages with explicit dependencies. The pipeline is a YAML or Python file in Git; the run is a Workflow object in the cluster.

### 2.2 The resource request is the contract

A stage that asks for `nvidia.com/gpu: 8` is making a contract with the scheduler. The contract is "I need eight GPUs in the same NUMA domain, with NVLink between them, and I need them all at once". The default Kubernetes scheduler cannot guarantee all-or-nothing; that is what gang scheduling (Chapter 11.16) is for.

```yaml
# code/part16/gpu_resource_request.yaml (shape only)
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: multi-gpu-train-
spec:
  entrypoint: train
  templates:
    - name: train
      container:
        image: my-training-image:v1
        command: [python, train.py]
        args: ["--num-gpus", "8"]
        resources:
          requests:
            cpu: "32"
            memory: "256Gi"
            nvidia.com/gpu: "8"
          limits:
            nvidia.com/gpu: "8"
      schedulerName: kai-scheduler  # or volcano, kueue
      podSpecPatch: |
        - op: add
          path: /spec/schedulingGates
          value:
            - name: gang-scheduling
```

The pattern is the same in KFP, Flyte and Airflow's `KubernetesPodOperator`: declare the resource request, declare the scheduler name, and let the gang-scheduling plugin (KAI, Volcano or Kueue) hold the GPUs until all eight are available.

### 2.3 Artefact passing without the file system

A pipeline that passes data through the cluster's file system is a pipeline that scales linearly with the cluster's I/O subsystem, not with the cluster's compute. The four orchestrators all have an artefact store; use it.

```text
Artefact passing patterns (DMLS Ch 10; MLPE Ch 5):
- Argo: Argo Artifacts (S3-backed) or a sidecar that uploads to object storage
- KFP: dsl.Artifact with an underlying KFP metadata store
- Flyte: typed outputs that are automatically uploaded to the configured blob store
- Airflow: XCom for small values (kilobytes), object storage for large values
```

The rule is the same regardless of orchestrator. A stage's output is a pointer to an object in the artefact store, not the bytes themselves. The next stage reads the pointer, resolves it to a content hash, verifies the hash, and downloads the bytes only when needed.

### 2.4 Caching is the cheapest optimisation

A stage that has not changed inputs should not re-run. The four orchestrators implement this differently.

| Orchestrator | Cache key | Cache scope |
|---|---|---|
| Argo | Pod-level cache by container image + command + args | Same workflow definition |
| KFP | Step-level cache by component + params + inputs | Same pipeline version |
| Flyte | Task-level cache by input content hash | Same task definition |
| Airflow | None by default; operators can implement their own | Per operator |

Flyte's content-hash cache is the strongest. A task whose inputs have not changed since the last run is skipped entirely; the cached output is reused. The cost is a small amount of storage for cached outputs and a dependency on the cache key being deterministic.

The pattern in practice: feature engineering stages are cached aggressively (the inputs are versioned and immutable); training stages are rarely cached (the inputs change, the seeds change, the code changes); evaluation stages are cached when the training output is unchanged.

### 2.5 Retries and backoff

A stage that fails should retry. The pattern is:

- **Retry on transient errors.** Network blips, image pull rate limits, scheduler races. Three retries with exponential backoff.
- **Fail-fast on logic errors.** Schema mismatch, code bug, missing data. No retry; page the on-call.
- **Retry with cleanup on resource errors.** OOM, GPU NCCL timeout. One retry after the resource pressure clears.

```yaml
# Argo retry example
- name: train
  template: train
  retries:
    limit: 3
    backoff:
      duration: "1m"
      factor: 2
      maxDuration: "10m"
  retryStrategy: "OnError"
```

The pattern is the same in the other orchestrators. The discipline is the same: transient errors get retries, logic errors get pages, resource errors get one retry after pressure clears.

---

## 3. GPU pool integration and gang scheduling

### 3.1 Why default Kubernetes scheduling is not enough

A training job that requests eight GPUs needs all eight at once. The default Kubernetes scheduler allocates pods one at a time; it does not know that the eight pods of a multi-GPU job are a single unit. The result is the classic "two pods got GPUs, six are pending, the cluster is wedged" failure.

The fix is a gang scheduler. Three are in production use today.

| Scheduler | Strength | Ecosystem |
|---|---|---|
| **Volcano** | Mature; supports gang, queue, fairshare, priority | Strong in Asia-Pacific; integrated with Kueue |
| **Kueue** | Queue-based; works with Volcano or scheduler plugins | Strong on GKE; native to Kubernetes |
| **KAI Scheduler** | NVIDIA-native; gang, topology, GPU fractions, MIG | NVIDIA GPU platforms; see Chapter 11.16 |

*Designing Machine Learning Systems* Chapter 10 makes the point that any of the three is correct; the choice is ecosystem and operational fit. *Machine Learning Platform Engineering* Chapter 5 adds the observation that the scheduler must support the GPU pool's topology (NVLink domains, rack affinity) for multi-node training.

### 3.2 A Volcano PodGroup example

```yaml
# code/part16/podgroup.yaml (shape only)
apiVersion: scheduling.volcano.sh/v1beta1
kind: PodGroup
metadata:
  name: train-gang
spec:
  minMember: 8
  minResources:
    cpu: "32"
    memory: "256Gi"
    nvidia.com/gpu: "8"
  queue: gpu-pool
  priorityClassName: high
```

The PodGroup is the unit of gang scheduling. The scheduler holds all eight pods until the group can be satisfied; the pods start together; they fail together if any pod fails.

### 3.3 The KAI Scheduler alternative

KAI Scheduler (Chapter 11.16) is the NVIDIA-native alternative to Volcano. The scheduler understands GPU topology, MIG slices, and GPU fractions; it can gang-schedule a job that requests mixed resources (for example, one H100 SXM5 with four MIG slices, plus a CPU-bound data loader). The configuration shape is similar:

```yaml
# code/part16/kai_podgroup.yaml (shape only)
apiVersion: scheduling.run.ai/v2
kind: PodGroup
metadata:
  name: train-gang
spec:
  minMember: 8
  resources:
    gpu:
      count: 8
      type: h100-sxm5-80gb
    cpu:
      count: 32
    memory:
      count: 256Gi
  queue: gpu-pool
  priority: 100
```

The choice between Volcano and KAI is operational. Volcano is mature and broadly adopted; KAI is the right fit on NVIDIA stacks with rich GPU topology requirements.

---

## 4. Integration with the tracker, registry, and feature store

### 4.1 The orchestrator as the glue

The orchestrator is the system that calls the tracker, the registry, and the feature store at the right time. The shape of the integration is the same regardless of orchestrator.

```mermaid
flowchart LR
    subgraph Orchestrator["Orchestrator DAG"]
        S1[Ingest]
        S2[Transform]
        S3[Train]
        S4[Evaluate]
        S5[Promote]
        S6[Deploy]
    end

    subgraph SideServices["Side services"]
        FS[Feature store]
        TR[Tracker (MLflow / W&B)]
        RE[Registry]
        AR[Artifact store (GCS)]
    end

    S1 --> AR
    S2 --> AR
    S3 --> AR
    S3 --> TR
    S4 --> TR
    S5 --> RE
    S6 --> RE
    S3 --> FS
    S5 --> FS
```

The arrows from the orchestrator to the side services are the integration points. Each arrow carries an artifact with an id; each arrow is a stage in the DAG. The orchestrator does not own the data; it owns the order.

### 4.2 Run records from the orchestrator

Every orchestrator produces a run record; the run record feeds the tracker (Chapter 16.2). The pattern is to open a tracker run at the start of the DAG and close it at the end; the orchestrator's metadata becomes a tag in the tracker.

```python
# Flyte example: tag the run record with the Flyte execution id
@task
def train(clean_path: str, seed: int, flyte_execution_id: str) -> str:
    import mlflow
    mlflow.set_experiment("churn")
    with mlflow.start_run() as run:
        mlflow.set_tag("flyte_execution_id", flyte_execution_id)
        # ... train ...
    return run.info.run_id
```

The double-tagging (Flyte execution id in the tracker, tracker run id in the Flyte metadata) is what lets an operator navigate from one system to the other.

### 4.3 Secrets and IAM

The orchestrator runs stages as Kubernetes pods. The pods need secrets (object storage credentials, registry credentials, database credentials) and IAM (the service account that the pod runs as). The pattern is the same regardless of orchestrator.

```yaml
# Argo pod-level secrets
- name: train
  template: train
  container:
    image: my-training-image:v1
    env:
      - name: GCS_BUCKET
        value: gs://my-bucket
      - name: GOOGLE_APPLICATION_CREDENTIALS
        value: /var/secrets/google/key.json
    volumeMounts:
      - name: gcp-key
        mountPath: /var/secrets/google
        readOnly: true
  volumes:
    - name: gcp-key
      secret:
        secretName: gcp-key
```

Secrets are read from Vault or Secret Manager via External Secrets Operator; rotation is automatic. The service account is declared per-stage (or per-DAG); the platform team owns the service account's IAM bindings.

---

## 5. Operating the orchestrator on GKE

### 5.1 The components

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| Argo Workflows controller | Kubernetes Deployment | Postgres for workflow metadata | Workflow submit p99 < 5 s |
| KFP backend | Kubernetes Deployment | MLMD on MySQL/Postgres | Pipeline submit p99 < 10 s |
| Flyte propeller | Kubernetes Deployment | Postgres + blob store | Task scheduling p99 < 2 s |
| Airflow scheduler | Kubernetes Deployment | Postgres | DAG parse p99 < 30 s |
| Object store (artefacts) | Direct from worker pods | GCS bucket | p99 put < 5 s |
| Secrets | External Secrets Operator | Vault or Secret Manager | p99 secret fetch < 500 ms |
| IAM | Kubernetes RBAC + GCP IAM | n/a | n/a |

### 5.2 IAM and multi-tenancy

The orchestrator is multi-tenant by default. The pattern is one namespace per team, one service account per pipeline, and one Argo Workflow or KFP pipeline per DAG.

```yaml
# Argo multi-tenancy
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: churn-training
  namespace: team-data-science
spec:
  serviceAccountName: pipeline-runner-data-science
  entrypoint: pipeline
  templates:
    - name: pipeline
      dag:
        tasks:
          - name: train
            template: train
```

The service account's IAM bindings determine what the DAG can read and write. The namespace's resource quotas determine how much GPU the DAG can request. The platform team owns both.

### 5.3 Observability of the orchestrator

The orchestrator is a production service. It has metrics, logs and alerts.

| Metric | Why it matters | Alert |
|---|---|---|
| Workflow submit latency p99 | Hot path for every pipeline | > 10 s |
| Stage duration p99 | Catch slow stages before they miss SLA | > 2x baseline for 3 runs |
| Stage failure rate | Catch a single bad upstream change | > 0 for 5 minutes |
| Postgres connection pool utilisation | Catch a sizing bottleneck | > 80 percent |
| Stuck workflows | Catch a DAG that is not progressing | > 0 for 30 minutes |
| Backlog (workflows pending) | Catch a queue that is too long | > 100 pending |

The stuck-workflow metric is the most important. A DAG that has been "running" for 6 hours with no stage progress is a DAG that has lost a pod or is stuck waiting for a quota. The alert fires on duration, not on stage count.

**Run the orchestrator as a production service. Give stages SLOs. Page on stuck workflows. The orchestrator is the audit trail; if it is broken, the audit trail is gone.**

---

## 6. How it fails

Six failure modes recur. Each has a name, a symptom, a diagnosis and a fix.

### 6.1 "Two pods got GPUs, six are pending"

**Symptom:** A multi-GPU training job is stuck. `kubectl describe pod` shows two pods scheduled; six are pending. The cluster has free GPUs but they are on different nodes.

**Diagnosis:** The default Kubernetes scheduler scheduled the first two pods greedily. It does not know that the job needs all eight at once.

**Fix:** Adopt a gang scheduler (Volcano, KAI, or Kueue with gang-scheduling plugin). Wrap the pods in a PodGroup with `minMember: 8`. The scheduler holds all pods until the group can be satisfied.

### 6.2 "The DAG ran but the data is from yesterday"

**Symptom:** The pipeline ran successfully. The training stage produced a model that trained on yesterday's data. The serving system is reading today's data. The offline metrics do not match production behaviour.

**Diagnosis:** The pipeline's freshness check (Chapter 16.3) is missing or disabled. The DAG accepted a stale snapshot.

**Fix:** Add a freshness check as the first stage of the DAG. The stage reads the metadata DB, verifies the snapshot is newer than the SLO, and fails the DAG if not. Wire the check to a Prometheus alert so the on-call sees the violation.

### 6.3 "The orchestrator's Postgres is full"

**Symptom:** Workflows start failing with `database error`. The Postgres disk is at 100 percent. The cluster's `kubectl` commands are slow.

**Diagnosis:** The metadata database has not been vacuumed. Old workflow records are bloating the table.

**Fix:** Enable Postgres autovacuum aggressively for the orchestrator's tables. Add a retention policy: completed workflows older than 90 days are archived to object storage. Add a disk-usage alert at 70 percent.

### 6.4 "The artefact upload times out"

**Symptom:** A stage that produces a large artefact (for example, a 50 GB model checkpoint) times out on upload. The DAG fails.

**Diagnosis:** The artefact is being uploaded through the orchestrator's pod-to-pod channel, not directly to object storage. The upload is bounded by the pod's network bandwidth.

**Fix:** Use the orchestrator's artefact store directly. Argo Artifacts, KFP Artifacts, Flyte's blob store, and Airflow's object-store hooks all bypass the pod-to-pod channel. For very large artefacts (more than 100 GB), use a presigned URL and upload from the worker pod directly to the bucket.

### 6.5 "The pipeline is running on the wrong GPU pool"

**Symptom:** A multi-node training job is scheduled on nodes that are not NVLink-connected. NCCL init fails; the job retries until it times out.

**Diagnosis:** The orchestrator's scheduler is the default Kubernetes scheduler. It does not understand the GPU topology.

**Fix:** Adopt a topology-aware scheduler (KAI Scheduler or Volcano with the topology plugin). Declare the NVLink domain in the pod spec; the scheduler will land all pods in the same domain.

### 6.6 "The DAG fails on a missing IAM role"

**Symptom:** The training stage fails with `Permission denied` on a GCS bucket. The error message names a missing role.

**Diagnosis:** The service account's IAM bindings are out of date. The bucket was created after the service account.

**Fix:** Adopt IaC (Terraform or Pulumi) for both the buckets and the IAM bindings. The platform team owns the Terraform that declares both. A bucket created without its IAM binding fails the IaC plan.

---

## 7. Hands-on lab

This lab stands up Argo Workflows on GKE, runs a multi-stage training DAG, and verifies that the integration with the tracker and registry from previous chapters works end-to-end. The lab is **untested** in this repository.

### 7.1 Prerequisites

- Chapters 16.1, 16.2 and 16.3 labs completed (MLflow + DVC + Feast on GKE).
- An Argo Workflows installation on GKE (Helm chart available).
- A Volcano or KAI Scheduler installation (or a stub that accepts the PodGroup).

### 7.2 Step 1: install Argo Workflows

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm install argo-workflows argo/argo-workflows \
  --namespace argo --create-namespace \
  --set controller.serviceType=ClusterIP
# expected: argo-workflows controller and workflow-controller pods in Running state
```

### 7.3 Step 2: install Volcano (or use an existing gang scheduler)

```bash
helm repo add volcano-sh https://volcano-sh.github.io/helm-charts
helm install volcano volcano-sh/volcano \
  --namespace volcano-system --create-namespace
# expected: volcano-scheduler pods in Running state
```

### 7.4 Step 3: submit a multi-stage DAG

```bash
argo submit -n mlops code/part16/training_dag.yaml \
  --entrypoint pipeline \
  --parameter dataset-id=churn-v3 \
  --parameter seed=42
# expected: a workflow run with stages prepare -> train -> evaluate -> promote
argo list -n mlops
argo get -n mlops @latest
```

### 7.5 Step 4: verify the gang scheduling

```bash
argo submit -n mlops code/part16/multi_gpu_dag.yaml
kubectl describe podgroup train-gang -n mlops
# expected: minMember=8, phase=Running, all 8 pods scheduled on the same NVLink domain
```

### 7.6 Step 5: verify the integration with the tracker and registry

```bash
# Open MLflow and confirm the run record has tags flyte_execution_id or argo_workflow_name
curl -s http://localhost:5000/api/2.0/mlflow/runs/search \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids":["1"],"filter_string":"tags.argo_workflow_name != \"\""}' \
  | jq '.runs[].info.run_id'
# expected: at least one run with the argo_workflow_name tag
```

### 7.7 Step 6: observe the orchestrator's metrics

```bash
kubectl -n argo port-forward svc/argo-workflows-metrics 9090:9090 &
curl -s http://localhost:9090/metrics | grep argo_workflow_duration
# expected: histogram metrics for workflow duration; alert thresholds from Section 5.3
```

### 7.8 What to record

After the lab, you should be able to answer five questions in five seconds each:

1. What orchestrator is the cluster running?
2. What is the namespace and service account for the team's pipelines?
3. What is the freshness check that the DAG runs first?
4. Where do the DAG's artefacts land (object store URI, lifecycle policy)?
5. What is the gang scheduler that the multi-GPU DAG uses?

If any of these takes more than 30 seconds to answer, the orchestrator is not yet a production service. The lab is **untested** against a live GKE cluster.

---

## Exercises

1. **Add a freshness check as the first stage.** Write an Argo template that reads the latest snapshot timestamp from the metadata DB and fails the workflow if the snapshot is older than the freshness SLO. *Solution sketch:* an Argo `http` template that calls the metadata DB; an exit code that fails the stage.
2. **Add a per-team resource quota.** Declare a `ResourceQuota` and a `LimitRange` in the team's namespace; verify that the orchestrator's scheduler respects the quota. *Solution sketch:* `kubectl apply -f resource_quota.yaml`; submit a DAG that exceeds the quota and expect it to be queued, not scheduled.
3. **Add content-hash caching to a stage.** Use Argo's pod-level cache or Flyte's task-level cache to skip a stage whose inputs are unchanged. *Solution sketch:* Argo's `memoize` block with a cache key derived from the inputs' content hashes.
4. **Wire a sweep on top of Argo.** Use Argo's `withParam` or a Python driver that submits one workflow per hyperparameter combination. *Solution sketch:* a Python script that loops over `params.yaml` and calls `argo submit` once per combination; a comparison query in MLflow.
5. **Move from default scheduler to KAI Scheduler.** Adopt KAI Scheduler; declare a `PodGroup` that the orchestrator creates; verify that the scheduler gang-schedules the multi-GPU DAG. *Solution sketch:* install KAI; declare a `PodGroup` in the DAG; observe the gang allocation.
6. **Add Prometheus alerts for stuck workflows.** Configure the orchestrator to emit a metric for workflows that have not progressed in 30 minutes; alert on the metric. *Solution sketch:* Argo emits `argo_workflow_duration_seconds`; a Prometheus rule alerts on `time() - workflow_last_progress > 30m`.

---

## Checkpoint questions

<details><summary>1. What four components does every orchestrator have?</summary>
A DAG definition language (YAML or Python), a scheduler that respects dependencies and resources, a runtime that runs each stage as a container, and a metadata store that records runs and lineage. The differences are in the language, the scheduler, the runtime, and the metadata store.
</details>

<details><summary>2. What is the difference between Argo Workflows and Kubeflow Pipelines?</summary>
Argo is a pure Kubernetes-native orchestrator with YAML DAGs and a Postgres metadata store. KFP compiles Python DAGs to Argo Workflows under the hood and adds a typed input/output system, a metadata-aware UI, and richer artefact handling. KFP is the right fit for teams already on Kubeflow; Argo is the right fit for Kubernetes-native teams that want a lighter stack.
</details>

<details><summary>3. What is the difference between Argo, KFP and Flyte?</summary>
Argo uses YAML and has pod-level caching. KFP uses Python (KFP SDK) and has step-level caching. Flyte uses Python with strong type annotations and has content-hash task-level caching. Flyte's type system and cache key are the strongest of the three.
</details>

<details><summary>4. Why is Airflow still in the conversation?</summary>
Airflow is the most widely adopted orchestrator outside Kubernetes-native teams. Its strength is its ecosystem of operators (Spark, BigQuery, Snowflake, HTTP) and the size of its community. The cost is that its Kubernetes integration is layered on top of the original scheduler rather than native to it.
</details>

<details><summary>5. What is gang scheduling and why does the default scheduler not provide it?</summary>
Gang scheduling means all pods of a multi-pod job start together. The default Kubernetes scheduler allocates pods one at a time and does not know that a multi-pod job is a single unit. The result is the "two pods got GPUs, six are pending" failure. The fix is a gang scheduler (Volcano, KAI, Kueue) that wraps the pods in a PodGroup and holds them until the group can be satisfied.
</details>

<details><summary>6. What three gang schedulers are in production today?</summary>
Volcano (mature; supports gang, queue, fairshare, priority), Kueue (queue-based; works with Volcano or scheduler plugins; native to Kubernetes), and KAI Scheduler (NVIDIA-native; gang, topology, GPU fractions, MIG). The choice is operational; all three are correct.
</details>

<details><summary>7. How does the orchestrator pass large artefacts between stages?</summary>
Through the orchestrator's artefact store, not through the cluster's file system. Argo Artifacts (S3-backed), KFP `dsl.Artifact` with the KFP metadata store, Flyte's typed outputs to the blob store, and Airflow XCom for small values plus object storage for large values. The pattern is: the stage writes a pointer to object storage; the next stage resolves the pointer and downloads the bytes.
</details>

<details><summary>8. What cache strategy does Flyte implement?</summary>
Flyte implements content-hash caching at the task level. A task whose inputs have not changed since the last run is skipped; the cached output is reused. The cache key is deterministic; the cached output is stored in the configured blob store.
</details>

<details><summary>9. What is the retry policy for a stage that fails on a transient error?</summary>
Three retries with exponential backoff. The backoff starts at one minute and doubles; the cap is ten minutes. Logic errors (schema mismatch, code bug) get no retry; resource errors (OOM, NCCL timeout) get one retry after the resource pressure clears.
</details>

<details><summary>10. What is the stuck-workflow metric?</summary>
A Prometheus metric that fires when a workflow has not progressed in 30 minutes. The alert is `time() - workflow_last_progress > 30m`. The metric catches DAGs that have lost a pod, are stuck waiting for a quota, or have entered an unrecoverable state.
</details>

<details><summary>11. Why is the resource request the contract with the scheduler?</summary>
A stage that asks for eight GPUs is making a contract that says "I need all eight GPUs in the same NUMA domain, with NVLink between them, all at once". The gang scheduler's job is to honour that contract; the default scheduler cannot. The pattern in production is to declare the resource request, the scheduler name, and the gang-scheduling plugin in the pod spec.
</details>

<details><summary>12. Why is the artefact store separate from the metadata store?</summary>
Because the metadata store is hot, small metadata (run records, stage statuses, lineage); the artefact store is cold, large bytes (model weights, checkpoints, datasets). Putting them in the same place forces one to compromise on the other. The split lets the metadata store be fast and small and the artefact store be cheap and large.
</details>

<details><summary>13. What is the IAM pattern for a multi-tenant orchestrator?</summary>
One namespace per team, one service account per pipeline, and one orchestrator Workflow or KFP pipeline per DAG. The service account's IAM bindings determine what the DAG can read and write; the namespace's resource quotas determine how much GPU the DAG can request. The platform team owns both.
</details>

<details><summary>14. How does the orchestrator integrate with the tracker?</summary>
The orchestrator opens a tracker run at the start of the DAG and closes it at the end. The orchestrator's metadata (workflow id, execution id, namespace) becomes a tag in the tracker; the tracker's run id becomes a tag in the orchestrator's metadata. The double-tagging is what lets an operator navigate from one system to the other.
</details>

<details><summary>15. What is the difference between a DAG and a workflow?</summary>
A DAG is the static definition (the YAML or Python file in Git). A workflow is a single execution of that DAG (a Workflow object in the cluster). The DAG is reviewable; the workflow is observable. A DAG can produce many workflows; each workflow has its own run record.
</details>

<details><summary>16. Why does Airflow still beat Argo for some teams?</summary>
Airflow has the largest ecosystem of operators (Spark, BigQuery, Snowflake, SageMaker, Vertex AI, HTTP, Slack, email). A team that runs Airflow for non-ML workloads can add an ML DAG to the same instance and operate one scheduler. Argo is the right fit for Kubernetes-native teams that do not want the operator ecosystem overhead.
</details>

<details><summary>17. What is the difference between a Kubernetes Job and an orchestrator stage?</summary>
A Kubernetes Job runs a single pod to completion. An orchestrator stage runs a single pod with explicit dependencies on prior stages, retries, caching, and artefact passing. The orchestrator is the system that schedules the Jobs; the Jobs are the units of work. For one-off batch tasks, a Kubernetes Job is fine; for a DAG, an orchestrator is required.
</details>

<details><summary>18. What is the operational cost of an orchestrator?</summary>
A Postgres database with automated backups and a 7-day PITR, an object storage bucket for artefacts with lifecycle policies, a Kubernetes Deployment with two or more replicas, an IAM model with one service account per pipeline, and an observability stack with metrics, logs, and alerts. The platform team owns all of it.
</details>

<details><summary>19. How does the orchestrator integrate with the feature store?</summary>
The orchestrator runs the materialisation stage; the stage calls the feature store's materialisation API; the feature store writes the offline and online views. The orchestrator's run record carries the feature table id; the feature store's metadata carries the lineage. The integration is a stage in the DAG, not a side effect.
</details>

<details><summary>20. Why is the orchestrator a production service rather than a developer tool?</summary>
Because every ML pipeline run depends on it. When the orchestrator is down, every pipeline is down. When the orchestrator is slow, every pipeline is slow. The platform team owns the orchestrator as a service with SLOs, IAM, backups, and on-call; the data scientists consume it.
</details>

---

## Sources and review notes

- *Designing Machine Learning Systems* (`designing-machine-learning-systems`, Chapter 10). Source for the orchestration-as-a-service framing, the comparison of Argo / KFP / Flyte / Airflow, the resource-request contract with the scheduler, and the integration with the tracker and registry. Chapter 10 is approximately 13,500 words.
- *Machine Learning Platform Engineering* (`machine-learning-platform-engineering`, Chapters 1, 5, 6). Source for the Argo Workflows and KFP deployment patterns on Kubernetes, the IAM model, the multi-tenancy patterns, and the integration with the tracker. Chapter 5 is approximately 9,000 words; Chapter 6 is approximately 9,500 words.
- *Practical MLOps* (`practical-mLOps`, Chapter 5). Source for the AutoML and KaizenML discussion of feature pipelines and sweeps as orchestrator DAGs, and the Flyte origin story at Lyft. Chapter 5 is approximately 8,800 words.
- Argo Workflows, Kubeflow Pipelines, Flyte, and Airflow official documentation. Source for the API shapes, the YAML and Python SDK syntax, the cache semantics, and the retry policies.

### Cross-references to other handbook chapters

- Chapter 16.1 Section 4.3 for the promotion gate function that the orchestrator invokes.
- Chapter 16.2 for the tracker that the orchestrator tags.
- Chapter 16.3 for the pipeline stages that the orchestrator runs.
- Chapter 11.16 for the KAI gang scheduler.
- Chapter 5 (Kubernetes) for the cluster primitives the orchestrator depends on.

### Migrated from `nvidia-devops`

The Volcano PodGroup shape and the resource-request contract in Section 3 draw on Volume 25 chapter 8 (scaling to multi-node distributed training). The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The cache comparison in Section 2.4 is an inference from each orchestrator's documentation; specific behaviour depends on the version and the configuration.
- The retry policy (three retries with exponential backoff) is a starting point drawn from common practice; specific workloads may need different policies.
- The freshness check in the failure modes is an inference from the operational pattern in Chapter 16.3; specific thresholds depend on the use case.

### Not verified on live hardware

- The lab in Section 7 is **untested** against a live GKE cluster in this repository.
- The Volcano, KAI Scheduler and Kueue versions assumed in the lab should be pinned against the current releases before production use.
- The Prometheus alert thresholds (workflow stuck at 30 minutes, quota at 80 percent) are starting points; specific thresholds depend on the team's DAG patterns.
