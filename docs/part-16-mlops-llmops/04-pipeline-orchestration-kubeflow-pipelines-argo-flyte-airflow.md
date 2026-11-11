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

Imagine a churn model that retrains every night. One Monday the feature build stops halfway, and the training job quietly uses last week's table. Nobody notices until the scores drift and someone asks why. An orchestrator exists to stop this kind of silent failure. It runs the stages in order, retries the ones that fail, skips the ones that have not changed, and records every run.

If you operate a GPU cluster for AI, you also operate an orchestrator, whether or not you call it that. It schedules the training jobs, the feature builds, the evaluation runs, the promotion gate, and the rollback. When it is slow or down, every one of those workflows waits with it.

```text
Why the orchestrator is on the critical path (background reading: Designing Machine Learning Systems; Machine Learning Platform Engineering; the figures below are examples, not quotations):
- A typical mature MLOps platform runs dozens to hundreds of DAGs per day across
  teams (training, retraining, feature materialisation, evaluation, deployment).
- Each DAG has between 5 and 50 stages; each stage has its own resource request,
  retry policy, and SLA. The orchestrator's job is to keep all of them on schedule.
- The orchestrator's metadata database (Postgres) is the audit trail for every
  pipeline run. A metadata database that is slow or wiped is the same failure as
  losing the audit log.
```

Three realities make this a platform-team concern rather than a data-science concern.

1. The orchestrator controls the GPU queue. Each training job it schedules becomes a Kubernetes pod that asks for GPUs. The platform team owns that queue and its quota, so the platform team decides who waits and who runs.
2. The orchestrator is a stateful service. Its Postgres backend, artifact store, identity model, and service levels are platform decisions. Its metadata is the audit trail for every run, so losing it is close to losing your Git history.
3. The orchestrator makes the retry and backfill decisions. When a stage fails, it chooses to retry, stop, or fall back. When a feature store is rebuilt, it chooses which downstream stages to run again. The platform team sets that policy.

**Run the orchestrator as a production service, with a service level objective, before any training job depends on it.** A best-effort orchestrator is the one that pages you at 2 a.m.

## Prerequisites and outcomes

Check the earlier chapters before you build anything here. The sections that follow assume a tracker, a registry, and a feature store already exist.

### Prerequisites

- Chapter 16.1 (the lifecycle and the four pillars).
- Chapter 16.2 (experiment tracking and registry).
- Chapter 16.3 (data pipelines and feature stores).
- Chapter 5 (Kubernetes) for the cluster primitives the orchestrator depends on.
- Familiarity with YAML, container images, and basic CI/CD concepts.

### Outcomes

After completing this chapter, you will be able to:

1. Compare Argo Workflows, Kubeflow Pipelines, Flyte and Airflow on execution model, artefact handling, caching, retry semantics, IAM and ecosystem fit.
2. Build a DAG that runs training, evaluation, validation, promotion, and materialisation stages with explicit dependencies and resource requests.
3. Wire a stage to GPU node pools with the right queue, priority and topology binding, and understand why default Kubernetes scheduling is not enough for gang-scheduled multi-GPU jobs.
4. Pass artefacts between stages by reference, not through the file system, and implement retries, caching, conditional branches, and parameter sweeps.
5. Operate the orchestrator on GKE with a Postgres backend, object-store artefacts, IAM, secrets, and observability.

---

## 1. The four orchestrators and how they differ

Your team has a notebook that trains a model. Now the model must retrain on a schedule, with a record of every run. Four orchestrators are common answers to that need. They look different on the surface, but they share one conceptual model.

### 1.0 The orchestrator as the surface where Kaizen happens

*Practical MLOps* Chapter 5 introduces AutoML and KaizenML as continuous improvement. The orchestrator is where that idea becomes a working habit. Each pipeline run is a hypothesis. The orchestrator records the hypothesis, runs the experiment, and feeds the result into the next iteration.

The Kaizen discipline asks three things of an orchestrator:

1. Every step is recorded. The metadata store is the audit log of every change the team has made.
2. Every step is reproducible. The artefact store is the source of truth for every artefact the team has produced.
3. Every step is reversible. The deployment layer, such as Argo Rollouts or a KServe canary, gives you a rollback path for a bad change.

An orchestrator that meets all three conditions turns "be more disciplined" into a property of the system. One that fails any of them is a notebook with extra steps.

### 1.1 A unified mental model

Look closely at any of the four orchestrators and you see the same parts. The surface differs, but the parts line up. The diagram shows how a DAG flows through the scheduler, the runtime, and the metadata store.

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
        R3["Outputs (artefacts)"]
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

Each orchestrator needs a way to define the DAG, a scheduler that respects dependencies and resources, a runtime that runs each stage as a container, and a metadata store that records what happened. The tools differ in four places. They differ in the definition language (YAML or Python), the scheduler (Kubernetes-native or custom), the runtime (container or task), and the metadata store (Postgres or a separate service).

### 1.2 Argo Workflows

Suppose your team already runs Kubernetes and wants pipelines without learning a new framework. Argo Workflows is built for that case. You write each DAG in YAML, and each stage runs as a Kubernetes pod. Argo has no Python layer and no hidden services, which keeps the stack small.

```yaml
# code/part16/argo_dag.yaml
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

A data scientist wants to write a training step in Python and let the platform run it without hand-written YAML. Kubeflow Pipelines was built for that situation. You define components and pipelines with the KFP SDK, and KFP compiles them to Argo Workflows and submits them to the cluster.

KFP also adds a run UI, a metadata store for artefacts, and typed inputs and outputs. The typed inputs and outputs catch a class of bugs when you compile the pipeline. A YAML DAG catches the same class of bugs only at run time.

```python
# code/part16/kfp_pipeline.py
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

*Machine Learning Platform Engineering* Chapter 6 walks through KFP as the orchestrator that ships with a metadata-aware UI.

### 1.4 Flyte

Your pipeline passes large data tables from one step to the next. A type mismatch can fail an hour into a run. Flyte is built to catch that kind of mismatch early. It started at Lyft, and it treats each stage as a typed task.

You declare inputs and outputs with type annotations, and the runtime checks those types against the dependency graph. In this chapter's comparison, Flyte has the strongest type system of the four. It also has the most support for conditional and dynamic workflows.

```python
# code/part16/snippets/flyte_pipeline.py
from flytekit import Resources, task, workflow

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

Flyte's type system and its first-class support for `pandas.DataFrame`, `numpy.ndarray`, and structured types make it a strong fit for data-heavy ML. *Practical MLOps* Chapter 5 describes Flyte's origin at Lyft and its growth into an open-source project under the Linux Foundation.

### 1.5 Airflow

Many data teams already run Airflow for nightly ETL jobs. Adding an ML training DAG to the same instance can be the cheapest path. Airflow is the oldest of the four, and it is the most widely adopted outside Kubernetes-native teams.

In Airflow, DAGs are Python files. Each task can be a Kubernetes pod, a Spark job, a database query, or an HTTP call. The metadata store is Postgres or MySQL. Airflow's strength is its operator ecosystem and its community. Its weakness is that Kubernetes support sits on top of a scheduler that was not built around Kubernetes.

```python
# code/part16/airflow_dag.py
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

*Designing Machine Learning Systems* Chapter 10 describes Airflow as the common choice for data engineering teams that already run it for non-ML work. The cost is that Airflow does not speak Kubernetes natively. The benefit is that the same operator pattern runs Spark, BigQuery, Snowflake, and HTTP tasks next to the Kubernetes pod.

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

Choosing among these four is rarely about features. Ask which team will run the tool, which ecosystem already lives in your cluster, and how much Python abstraction your team can absorb.

---

## 2. Building a DAG that actually runs

### 2.1 The shape of a production pipeline

A model that trains well in a notebook can still fail in production at a step nobody checked. Production pipelines add an explicit gate at each step, so a bad input stops the run early. The table lists eight stages that many teams use. Each stage has an artefact, a gate, and a resource request.

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

Each gate is a check you can automate. Put the check in the pipeline, not in someone's memory. Keep the DAG in Git so reviewers can read it, and let each run create its own Workflow object in the cluster.

### 2.2 The resource request is the contract

A training stage that asks for eight GPUs makes a promise to the scheduler. It needs all eight at the same time, in the same NUMA domain, with NVLink between them. The default Kubernetes scheduler cannot keep that promise on its own. Gang scheduling, covered in Chapter 11.16, is the tool for it.

```yaml
# code/part16/gpu_resource_request.yaml
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

The same pattern works in KFP, Flyte, and Airflow's `KubernetesPodOperator`. You declare the resource request and the scheduler name. The gang plugin, whether KAI, Volcano, or Kueue, then holds the GPUs until all eight are free. Check the request against your cluster before a long run starts, so the job does not wait in silence.

### 2.3 Artefact passing without the file system

Picture a stage that writes a multi-gigabyte checkpoint to a shared disk. The next stage reads it back from the same disk. Every byte crosses the storage system, so the pipeline slows down as the data grows. That design ties the pipeline's speed to storage rather than to compute.

All four orchestrators have an artefact store, so use it.

```text
Artefact passing patterns (background reading: Designing Machine Learning Systems; Machine Learning Platform Engineering; the figures below are examples, not quotations):
- Argo: Argo Artifacts (S3-backed) or a sidecar that uploads to object storage
- KFP: dsl.Artifact with an underlying KFP metadata store
- Flyte: typed outputs that are automatically uploaded to the configured blob store
- Airflow: XCom for small values (kilobytes), object storage for large values
```

The rule is the same for every orchestrator, so you can apply it everywhere. A stage writes its output to the artefact store and passes a pointer to the next stage. The next stage resolves the pointer to a content hash, verifies the hash, and downloads the bytes only when it needs them.

### 2.4 Caching is the cheapest optimisation

Retraining every stage every night wastes GPU hours on steps whose inputs have not changed. A cache lets the orchestrator skip those steps and reuse an earlier output. The four orchestrators decide what counts as a cache hit in different ways.

| Orchestrator | Cache key | Cache scope |
|---|---|---|
| Argo | Pod-level cache by container image + command + args | Same workflow definition |
| KFP | Step-level cache by component + params + inputs | Same pipeline version |
| Flyte | Task-level cache by input content hash | Same task definition |
| Airflow | None by default; operators can implement their own | Per operator |

Flyte's content-hash cache is the most exact of the four. A task is skipped only when its inputs match exactly, and the cached output is reused. The cost is some storage for cached outputs. The cache also works only if its key is deterministic.

In practice, cache feature engineering aggressively, because its inputs are versioned and never change. Rarely cache training, because the inputs, seeds, and code usually change between runs. Cache evaluation when the training output is unchanged. Ask of each stage whether its inputs can change, and cache only the stages where the answer is no.

### 2.5 Retries and backoff

A nightly job fails at one in the morning with an image pull error. Run it again a few minutes later and it succeeds. A retry policy decides which failures deserve another try, and which ones should wake someone up.

The chapter sorts failures into three groups.

- Transient errors, such as network blips, image pull rate limits, and scheduler races, deserve a few retries with backoff.
- Logic errors, such as a schema mismatch or a code bug, fail the same way every time. Do not retry them. Page the on-call engineer instead.
- Resource errors, such as out-of-memory or a GPU NCCL timeout, deserve one retry after the pressure clears.

The YAML below shows one example policy. It allows three retries, starting at one minute and doubling up to ten minutes. Those values are examples. Choose yours from how long a stage takes and what a failed retry costs.

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

The other orchestrators follow the same discipline with different syntax. Before you set a retry limit, decide which of the three error types each stage can produce.

---

## 3. GPU pool integration and gang scheduling

### 3.1 Why default Kubernetes scheduling is not enough

Your job needs eight GPUs. The scheduler places two of its pods and finds no room for the other six. The two running pods hold their GPUs and wait. The cluster looks busy, but the job makes no progress.

The default Kubernetes scheduler places pods one at a time. It does not know that eight pods form a single job. That produces the classic failure, in which two pods get GPUs, six stay pending, and the cluster is wedged. The fix is a gang scheduler, and three are in common use.

| Scheduler | Strength | Ecosystem |
|---|---|---|
| **Volcano** | Mature; supports gang, queue, fairshare, priority | Strong in Asia-Pacific; integrated with Kueue |
| **Kueue** | Queue-based; works with Volcano or scheduler plugins | Strong on GKE; native to Kubernetes |
| **KAI Scheduler** | NVIDIA-native; gang, topology, GPU fractions, MIG | NVIDIA GPU platforms; see Chapter 11.16 |

*Designing Machine Learning Systems* Chapter 10 argues that any of the three is a sound choice, and the decision comes down to ecosystem and operations. *Machine Learning Platform Engineering* Chapter 5 adds that the scheduler must understand the pool's topology, such as NVLink domains and rack affinity, for multi-node training.

### 3.2 A Volcano PodGroup example

A PodGroup tells the scheduler that a set of pods is one unit. The example below asks for eight pods and eight GPUs before any pod starts.

```yaml
# code/part16/podgroup.yaml
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

The scheduler holds all eight pods until the group fits. The pods then start together. If one pod fails, the group fails with it. Set `minMember` to the number of pods the job cannot run without.

### 3.3 The KAI Scheduler alternative

KAI Scheduler, covered in Chapter 11.16, is NVIDIA's alternative to Volcano. It understands GPU topology, MIG slices, and GPU fractions. It can gang-schedule a job that mixes resource types. For example, a job might need one H100 SXM5 split into four MIG slices, plus a CPU-bound data loader.

The configuration looks much like the Volcano example.

```yaml
# code/part16/kai_podgroup.yaml
apiVersion: scheduling.run.ai/v2alpha2
kind: PodGroup
metadata:
  name: train-gang
spec:
  minMember: 8
  queue: gpu-pool
  priorityClassName: high
```

Choose between Volcano and KAI on operations. If your jobs mix GPU slices with CPU work, check whether you need KAI before you adopt it. You will also want to ask the platform team which one it can run. Volcano is mature and widely adopted. KAI fits NVIDIA stacks that have detailed GPU topology requirements.

---

## 4. Integration with the tracker, registry, and feature store

### 4.1 The orchestrator as the glue

A pipeline run should leave a trail. The trail shows which data it read, which model it trained, and where the artefact went. The orchestrator makes those calls to the other systems at the right moment. The integration looks the same whichever orchestrator you choose.

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
        TR["Tracker (MLflow / W&B)"]
        RE[Registry]
        AR["Artifact store (GCS)"]
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

Each arrow is an integration point, and each arrow is a stage in the DAG. The arrow carries an artefact with an id. The orchestrator does not store the data itself. It decides the order in which the systems are called.

### 4.2 Run records from the orchestrator

Six months from now, someone will ask which pipeline run produced a given model. The answer should be one click away in both systems. Every orchestrator produces a run record, and that record feeds the tracker in Chapter 16.2.

Open a tracker run at the start of the DAG and close it at the end. Store the orchestrator's execution id as a tracker tag, so the tracker can point back to the pipeline.

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

Tag each system with the other's id. That double tagging is what lets an operator move from the tracker to the orchestrator run, and back again.

### 4.3 Secrets and IAM

A training pod needs credentials to read a bucket and push an image. If you paste those keys into the DAG file, they end up in Git. Store them somewhere else and let the pod fetch them at run time. The pattern is the same whichever orchestrator you use. Each pod runs as a service account and mounts only the secrets it needs.

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

In this setup, secrets live in Vault or Secret Manager and reach the cluster through External Secrets Operator. The chapter's setup assumes rotation happens automatically. Confirm the rotation schedule in your own configuration. The platform team owns the service account bindings, so ask it before you widen a pipeline's access.

---

## 5. Operating the orchestrator on GKE

### 5.1 The components

When the orchestrator slows down, every team's pipeline slows with it. Know which component owns which store before an incident starts. The table lists the components, their backing stores, and their service-level targets. The targets are example values, not measurements. Set your own from the latency you actually observe.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| Argo Workflows controller | Kubernetes Deployment | Postgres for workflow metadata | Workflow submit p99 < 5 s |
| KFP backend | Kubernetes Deployment | MLMD on MySQL/Postgres | Pipeline submit p99 < 10 s |
| Flyte propeller | Kubernetes Deployment | Postgres + blob store | Task scheduling p99 < 2 s |
| Airflow scheduler | Kubernetes Deployment | Postgres | DAG parse p99 < 30 s |
| Object store (artefacts) | Direct from worker pods | GCS bucket | p99 put < 5 s |
| Secrets | External Secrets Operator | Vault or Secret Manager | p99 secret fetch < 500 ms |
| IAM | Kubernetes RBAC + GCP IAM | n/a | n/a |

The orchestrator writes to a database, and that database needs the same care as the orchestrator itself. Back it up, and test that you can restore it.

### 5.2 IAM and multi-tenancy

Two teams share one cluster, and one team's runaway job takes every GPU. Isolation is what prevents that. The default pattern is one namespace per team, one service account per pipeline, and one Workflow or KFP pipeline per DAG.

*Production Kubernetes*, chapter 16, describes a standard onboarding bundle for each namespace. The bundle covers role-based access control, network policies, resource quotas, limit ranges, and pod security defaults. Not every team needs all five, but together they let a new team start without manual steps.

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

The service account's IAM bindings decide what the DAG can read and write. The namespace's quotas decide how much GPU the DAG can request. The platform team owns both, so check with it before you change either.

### 5.3 Observability of the orchestrator

A DAG that sits in the running state with no stage progress wastes time without raising an error. The orchestrator is a production service, so it needs metrics, logs, and alerts. The table lists the metrics a platform team usually watches. The alert thresholds in it are examples. Set them from your own baseline.

| Metric | Why it matters | Alert |
|---|---|---|
| Workflow submit latency p99 | Hot path for every pipeline | > 10 s |
| Stage duration p99 | Catch slow stages before they miss SLA | > 2x baseline for 3 runs |
| Stage failure rate | Catch a single bad upstream change | > 0 for 5 minutes |
| Postgres connection pool utilisation | Catch a sizing bottleneck | > 80 percent |
| Stuck workflows | Catch a DAG that is not progressing | > 0 for 30 minutes |
| Backlog (workflows pending) | Catch a queue that is too long | > 100 pending |

The stuck-workflow metric matters most. A DAG that has been running with no stage progress has probably lost a pod or is waiting on a quota. An alert on elapsed time catches that case, while an alert on stage count can miss it.

**Run the orchestrator as a production service, give its stages service levels, and page someone when workflows get stuck.** The orchestrator is the audit trail, so if it breaks, the trail breaks with it.

---

## 6. How it fails

Six failures come up again and again. Each one has a name, a symptom, a diagnosis, and a fix. Start with the symptom, since that is what you or the on-call engineer sees first.

### 6.1 "Two pods got GPUs, six are pending"

Symptom: A multi-GPU training job is stuck. `kubectl describe pod` shows two pods scheduled and six pending. The cluster has free GPUs, but they sit on different nodes.

Diagnosis: The default Kubernetes scheduler placed the first two pods greedily. It does not know the job needs all eight at once.

Fix: Adopt a gang scheduler, such as Volcano, KAI, or Kueue with a gang-scheduling plugin. Wrap the pods in a PodGroup with `minMember` set to eight. The scheduler then holds every pod until the group fits.

### 6.2 "The DAG ran but the data is from yesterday"

Symptom: The pipeline finished successfully. The training stage produced a model trained on yesterday's data, while serving reads today's data. Offline metrics no longer match production.

Diagnosis: The freshness check from Chapter 16.3 is missing or switched off. The DAG accepted a stale snapshot.

Fix: Add a freshness check as the first stage of the DAG. The stage reads the metadata database, confirms the snapshot is newer than your freshness target, and fails the DAG if it is not. Connect the check to an alert so the on-call engineer sees the violation.

### 6.3 "The orchestrator's Postgres is full"

Symptom: Workflows start failing with a database error. The Postgres disk is at 100 percent, and `kubectl` commands feel slow.

Diagnosis: The metadata database has not been vacuumed. Old workflow records are bloating its tables.

Fix: Turn on autovacuum for the orchestrator's tables. Add a retention policy that archives completed workflows to object storage once they are old enough. The chapter's example archives after 90 days and alerts at 70 percent disk use. Those are example values, so pick your own.

### 6.4 "The artefact upload times out"

Symptom: A stage that writes a large artefact, such as a model checkpoint, times out on upload. The DAG fails.

Diagnosis: The artefact travels through the orchestrator's pod-to-pod channel. The pod's network bandwidth therefore limits the upload.

Fix: Upload to the artefact store directly. Argo Artifacts, KFP Artifacts, Flyte's blob store, and Airflow's object-store hooks all skip the pod-to-pod channel. For very large artefacts, a presigned URL lets the worker pod upload straight to the bucket. The size at which to switch is a decision for your team.

### 6.5 "The pipeline is running on the wrong GPU pool"

Symptom: A multi-node training job lands on nodes without NVLink. NCCL initialisation fails, and the job retries until it times out.

Diagnosis: The orchestrator's scheduler is the default Kubernetes scheduler, which does not understand GPU topology.

Fix: Adopt a topology-aware scheduler, such as KAI Scheduler or Volcano with its topology plugin. Declare the NVLink domain in the pod spec, and the scheduler lands all pods in the same domain.

### 6.6 "The DAG fails on a missing IAM role"

Symptom: The training stage fails with `Permission denied` on a GCS bucket. The error names a missing role.

Diagnosis: The service account's IAM bindings are out of date. The bucket was created after the service account.

Fix: Manage the buckets and their IAM bindings as code, with Terraform or Pulumi, owned by the platform team. Review the plan before each apply, since that is where a bucket without a binding should show up.

---

## 7. Hands-on lab

Imagine your team must show that a training run leaves a trail from the orchestrator to the tracker. This lab builds that trail on GKE and checks each link. The lab is untested in this repository, so treat each "expected" line as something to confirm on your cluster.

### 7.1 Prerequisites

- Chapters 16.1, 16.2 and 16.3 labs completed (MLflow + DVC + Feast on GKE).
- An Argo Workflows installation on GKE (Helm chart available).
- A Volcano or KAI Scheduler installation (or a stub that accepts the PodGroup).

### 7.2 Step 1: install Argo Workflows

Install the controller first. The expected line tells you what a healthy install looks like.

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm install argo-workflows argo/argo-workflows \
  --namespace argo --create-namespace \
  --set controller.serviceType=ClusterIP
# expected: argo-workflows controller and workflow-controller pods in Running state
```

### 7.3 Step 2: install Volcano (or use an existing gang scheduler)

If your cluster already has a gang scheduler, skip this step.

```bash
helm repo add volcano-sh https://volcano-sh.github.io/helm-charts
helm install volcano volcano-sh/volcano \
  --namespace volcano-system --create-namespace
# expected: volcano-scheduler pods in Running state
```

### 7.4 Step 3: submit a multi-stage DAG

Submit the training DAG and watch it move through its stages.

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

Submit the multi-GPU DAG and check that its PodGroup holds all eight pods.

```bash
argo submit -n mlops code/part16/multi_gpu_dag.yaml
kubectl describe podgroup train-gang -n mlops
# expected: minMember=8, phase=Running, all 8 pods scheduled on the same NVLink domain
```

### 7.6 Step 5: verify the integration with the tracker and registry

Query MLflow for runs that carry the Argo workflow tag.

```bash
# Open MLflow and confirm the run record has tags flyte_execution_id or argo_workflow_name
curl -s http://localhost:5000/api/2.0/mlflow/runs/search \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids":["1"],"filter_string":"tags.argo_workflow_name != \"\""}' \
  | jq '.runs[].info.run_id'
# expected: at least one run with the argo_workflow_name tag
```

### 7.7 Step 6: observe the orchestrator's metrics

Port-forward the metrics service, then read the workflow duration histogram.

```bash
kubectl -n argo port-forward svc/argo-workflows-metrics 9090:9090 &
curl -s http://localhost:9090/metrics | grep argo_workflow_duration
# expected: histogram metrics for workflow duration; alert thresholds from Section 5.3
```

### 7.8 What to record

After the lab, you should be able to answer these five questions without digging through the cluster:

1. What orchestrator is the cluster running?
2. What is the namespace and service account for the team's pipelines?
3. What is the freshness check that the DAG runs first?
4. Where do the DAG's artefacts land (object store URI, lifecycle policy)?
5. What is the gang scheduler that the multi-GPU DAG uses?

If you cannot answer one of these from the cluster itself, the orchestrator is not yet ready to run production pipelines. The lab is untested against a live GKE cluster.

---

## Exercises

Each exercise asks you to change one part of the pipeline and check the result. Try them in order, since later exercises build on the cluster you set up in the lab.

1. Add a freshness check as the first stage. Write an Argo template that reads the latest snapshot timestamp from the metadata DB and fails the workflow if the snapshot is older than the freshness target. *Solution sketch:* an Argo `http` template that calls the metadata DB, and an exit code that fails the stage.
2. Add a per-team resource quota. Declare a `ResourceQuota` and a `LimitRange` in the team's namespace, then check that the scheduler respects them. *Solution sketch:* `kubectl apply -f resource_quota.yaml`, then submit a DAG that exceeds the quota and expect it to be queued, not scheduled.
3. Add content-hash caching to a stage. Use Argo's pod-level cache or Flyte's task-level cache to skip a stage whose inputs have not changed. *Solution sketch:* Argo's `memoize` block, with a cache key derived from the inputs' content hashes.
4. Wire a sweep on top of Argo. Use Argo's `withParam`, or a Python driver that submits one workflow per hyperparameter combination. *Solution sketch:* a Python script that loops over `params.yaml` and calls `argo submit` once per combination, then a comparison query in MLflow.
5. Move from the default scheduler to KAI Scheduler. Adopt KAI, declare a `PodGroup` that the orchestrator creates, and check that the multi-GPU DAG is gang-scheduled. *Solution sketch:* install KAI, declare a `PodGroup` in the DAG, and observe the gang allocation.
6. Add Prometheus alerts for stuck workflows. Configure the orchestrator to emit a metric for workflows that have not progressed in 30 minutes, then alert on that metric. *Solution sketch:* Argo emits `argo_workflow_duration_seconds`, and a Prometheus rule alerts on `time() - workflow_last_progress > 30m`. The metric name in this sketch is illustrative. Confirm which progress metric your controller actually exposes before you write the rule.

## Checkpoint questions

<details><summary>1. A multi-GPU training job is stuck. `kubectl describe pod` shows two pods scheduled and six pending, and the cluster has free GPUs on other nodes. What happened and what is the fix?</summary>
The default Kubernetes scheduler places pods one at a time and does not know the eight pods form a single job. It placed two greedily, and those two hold their GPUs while they wait. Adopt a gang scheduler such as Volcano, KAI or Kueue. Wrap the pods in a PodGroup with `minMember` set to eight, so the scheduler holds every pod until the group fits.
</details>

<details><summary>2. Workflows start failing with a database error, the Postgres disk is at 100 percent and `kubectl` feels slow. What do you do now and what do you change afterwards?</summary>
The metadata database was never vacuumed, and old workflow records are bloating its tables. Turn on autovacuum for the orchestrator's tables. Add a retention policy that archives completed workflows to object storage once they are old enough. The chapter's example archives after 90 days and alerts at 70 percent disk use, and you should pick your own values.
</details>

<details><summary>3. A stage that writes a large model checkpoint times out on upload and the DAG fails. Where is the bottleneck and how do you remove it?</summary>
The artefact travels through the orchestrator's pod-to-pod channel, so the pod's network bandwidth limits the upload. Upload to the artefact store directly. Argo Artifacts, KFP Artifacts, Flyte's blob store and Airflow's object-store hooks all skip that channel. For very large artefacts, a presigned URL lets the worker pod write straight to the bucket.
</details>

<details><summary>4. The training stage fails with `Permission denied` on a GCS bucket, and the error names a missing role. What is the cause and the lasting fix?</summary>
The service account's IAM bindings are out of date, because the bucket was created after the service account. Manage the buckets and their IAM bindings as code with Terraform or Pulumi, owned by the platform team. Review the plan before each apply, since that is where a bucket without a binding should show up.
</details>

<details><summary>5. A DAG has been in the running state for an hour with no stage progress and no error. What is the likely cause, and why does an alert on stage count miss it?</summary>
The DAG has probably lost a pod or is waiting on a quota. An alert on elapsed time catches that case, because the stuck-workflow metric fires when it exceeds 0 for 30 minutes. An alert on stage count can miss it, since nothing fails and the count simply stops changing.
</details>

<details><summary>6. A nightly job fails at 1 a.m. with an image pull error and succeeds when rerun a few minutes later. How should the retry policy treat this, and how would it treat a schema mismatch?</summary>
An image pull rate limit is a transient error, so it deserves a few retries with backoff. A schema mismatch is a logic error that fails the same way every time. Do not retry it, and page the on-call engineer instead. An out-of-memory or NCCL timeout is a resource error and gets one retry after the pressure clears.
</details>

<details><summary>7. Why do you set `minMember` to the number of pods the job cannot run without, and what happens when one pod fails?</summary>
The scheduler holds all pods until the group fits, then starts them together. If one pod fails, the whole group fails with it. A value that is too low would let a partial group start, and a job that needs all eight would then run wedged.
</details>

<details><summary>8. Why does a stage pass a pointer to the next stage and not write the bytes to a shared file system?</summary>
Writing a multi-gigabyte checkpoint to a shared disk means every byte crosses the storage system, so the pipeline speed ties to storage and slows as the data grows. With a pointer, the stage writes its output to the artefact store. The next stage resolves the pointer to a content hash, verifies it, and downloads the bytes only when it needs them.
</details>

<details><summary>9. Why tag the tracker run with the orchestrator execution id and tag the orchestrator run with the tracker id?</summary>
Six months later someone asks which pipeline run produced a model. The double tag lets an operator move from the tracker to the orchestrator run and back again. Each system points at the other, so neither is a dead end.
</details>

<details><summary>10. Why must a gang scheduler understand topology and not only count GPUs?</summary>
An eight-GPU stage needs all eight at once, in the same NUMA domain, with NVLink between them. Machine Learning Platform Engineering chapter 5 says the scheduler must understand the pool's topology for multi-node training, such as NVLink domains and rack affinity. Without that, the pods can land on nodes without NVLink and NCCL initialisation fails.
</details>

<details><summary>11. Why does the chapter say to cache feature engineering aggressively and training rarely, and what must be true for a cache to work?</summary>
Feature engineering inputs are versioned and never change, so a rerun gives the same output. Training inputs, seeds and code usually change between runs, so a cache hit would be rare. A cache also works only if its key is deterministic. Ask of each stage whether its inputs can change, and cache only the stages where the answer is no.
</details>

<details><summary>12. A team that runs Kubernetes wants pipelines. When do you choose Argo, Kubeflow Pipelines or Flyte, and what do you give up?</summary>
Argo suits Kubernetes-native teams with simple dependencies, and it keeps the stack small with YAML and no Python layer. Kubeflow Pipelines suits teams on Kubeflow that want typed artefacts and a rich UI, and it compiles to Argo. Flyte suits data-heavy ML with the strongest type system and dynamic workflows, and it adds a Python abstraction your team must absorb. The choice is rarely about features and mostly about who will run the tool.
</details>

<details><summary>13. How do you choose between Volcano, Kueue and KAI Scheduler?</summary>
Designing Machine Learning Systems says any of the three is a sound choice, and the decision comes down to ecosystem and operations. Volcano is mature and supports gang, queue, fairshare and priority. Kueue is queue-based and strong on GKE. KAI is NVIDIA-native and handles topology, GPU fractions and MIG, so check whether your jobs mixing GPU slices with CPU work need it. Ask which one the platform team can run.
</details>

<details><summary>14. Your data team already runs Airflow for nightly ETL. Do you add the ML training DAG there, and what is the cost?</summary>
It can be the cheapest path, since the operator pattern runs Spark, BigQuery, Snowflake and HTTP tasks next to the Kubernetes pod. The cost is that Airflow's Kubernetes support sits on top of a scheduler that was not built around Kubernetes. It also has no built-in caching. GPU work goes through `KubernetesPodOperator`.
</details>

<details><summary>15. A data scientist wants to write the training step in Python with no hand-written YAML. What does Kubeflow Pipelines give over a raw YAML DAG?</summary>
You define components with the KFP SDK, and KFP compiles them to Argo Workflows and submits them. KFP adds a run UI, a metadata store for artefacts and typed inputs and outputs. The types catch a class of bugs at compile time, while a YAML DAG catches the same class only at run time. You give up the small stack that plain Argo offers.
</details>

<details><summary>16. An Argo retry policy has a limit of 3, a first delay of 1 minute, a factor of 2 and a max duration of 10 minutes. How long does the stage wait in total before giving up?</summary>
The delays are 1, 2 and 4 minutes, which is 7 minutes of backoff, and none reaches the 10-minute cap. The stage makes four attempts in all, the first run plus three retries. These values are examples, so choose yours from how long a stage takes and what a failed retry costs.
</details>

<details><summary>17. A job needs 8 GPUs and the default scheduler placed 2 pods. How many GPUs are held idle and what fraction of the job is that?</summary>
Two pods hold their GPUs and make no progress, because the other six are pending. That is 2 of 8, or 25 percent of the job. The cluster looks busy but the job makes no progress.
</details>

<details><summary>18. A stage normally takes 12 minutes. At what duration does the example alert fire, and how many runs must it happen on?</summary>
The alert fires above 2 times the baseline, which is 24 minutes, and it must persist for 3 runs. That catches slow stages before they miss their SLA without paging on one slow run. The thresholds are examples, so set yours from your own baseline.
</details>

<details><summary>19. A multi-node training job lands on nodes without NVLink, NCCL initialisation fails, and the job retries until it times out. What do you check first, second and third?</summary>
First, check which nodes the pods landed on and whether they share an NVLink domain. Second, check which scheduler placed them, because the default Kubernetes scheduler does not understand GPU topology. Third, move to a topology-aware scheduler such as KAI or Volcano with its topology plugin, and declare the NVLink domain in the pod spec.
</details>

<details><summary>20. The pipeline finished successfully, but the model trained on yesterday's data while serving reads today's. What do you check first, second and third?</summary>
First, read the metadata database and compare the snapshot timestamp with your freshness target. Second, check whether the freshness check from Chapter 16.3 exists in the DAG or was switched off. Third, add it as the first stage so the DAG fails when the snapshot is too old, and connect it to an alert.
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
