---
id: "c16-12"
title: "16.12 NVIDIA enterprise stack: AI Enterprise, NGC and licensing"
sidebar_label: "16.12 NVIDIA enterprise stack"
sidebar_position: 12
description: "The NVIDIA AI Enterprise (NVAIE) software stack: NGC containers and models, NIM (NVIDIA Inference Microservice), NeMo framework, RAPIDS for data science, licensing models, and the operational pattern that ties the stack to a Kubernetes GPU cluster."
status: "drafted"
tier: "1b"
level: "I"
lab_venue: "GCP / GKE"
---

# 16.12 NVIDIA enterprise stack: AI Enterprise, NGC and licensing

| Field | Value |
|---|---|
| Level | Intermediate |
| Priority tier | 1b (NVIDIA-specific) |
| Lab venue | GCP / GKE |
| Part | Part 16: MLOps and LLMOps tools and platforms |
| Cross-references | Chapter 10.9 (NVIDIA software stack); Chapter 15.7 (NVIDIA NIM and NIM Operator); Chapter 16.5 (Distributed compute); Chapter 16.7 (Serving platforms); Chapter 16.6 (Model registry) |
| Coverage file | `planning/coverage/chapters/16-12.md` |
| Claim & number ledger | `planning/ledgers/16-12.md` |

## Why this matters for AI infrastructure

Parts 1 through 15 gave you the cluster primitives, and Chapter 16.5 added the scheduler for training jobs. Chapter 16.7 added the serving platform for inference. This chapter covers the NVIDIA layer that sits on top of all three. Think of it as the software that turns a rack of expensive GPUs into something a team can actually use. It has five parts: the NVIDIA AI Enterprise (NVAIE) software stack, the NGC catalog of containers and models, the NIM inference microservice, the NeMo framework for LLM customization, and the RAPIDS library for GPU-accelerated data science. NGC is NVIDIA's catalog, and NIM and NeMo are both explained where they first appear below.

NVAIE is NVIDIA's production software stack, sold with enterprise support. You can assemble the same pieces from open source, such as PyTorch, TensorRT, Triton, NeMo, and RAPIDS, and skip the support contract. That choice looks like the managed-versus-self-hosted decision from Chapter 16.11. You either pay for the support contract, or you pay engineers to maintain the pieces. Neither answer is wrong, but the two costs look different on a budget sheet and show up at different times.

```text
Why NVAIE is on the critical path (background reading: NVIDIA AI Enterprise docs; NVIDIA Zero-to-Hero volume 14; the figures below are examples, not quotations):
- A production GPU cluster without the NVIDIA software stack is a cluster
  that runs CUDA kernels but cannot serve an inference, cannot train an LLM,
  cannot accelerate a dataframe. The software is what makes the hardware
  useful.
- The NGC catalog is the registry of pre-built containers (TensorRT, Triton,
  NeMo, RAPIDS, NIM) and pre-trained models (Llama, Mistral, SDXL) that the
  team would otherwise have to build and curate by hand.
- NVAIE licensing is the contract that gives the team access to NVIDIA's
  enterprise support, the NGC catalog, and the right to use NVAIE-licensed
  containers in production. Without the license, the team uses the open-source
  equivalents without the support contract.
```

Three realities make this a platform-team concern, not only a data-science concern. Each one lands on a specific piece of the platform, so each needs a named owner.

1. The NGC catalog is the team's container registry. The platform team owns the cache, the pull-through proxy, and the access model that lets the cluster pull from NGC. When a pull fails in the middle of the night, this is the team that gets the page.
2. NVAIE licensing is the team's budget. The platform team owns the seat count, the per-GPU license, the renewal calendar, and the audit log that proves compliance. A lapsed license does not stop a training job at once, which is exactly why it is easy to forget until it does.
3. NIM and NeMo are the team's inference and training stacks. The platform team owns the Helm charts, the Kubernetes operators, the GPU pool bindings, and the service targets. Those are the pieces that decide whether a model is up or down.

Before your team adopts NVAIE, make sure someone owns the license, the catalog, and the inference pattern. An unowned license turns into a surprise invoice, and an unowned catalog turns into images that nobody can trace.

## Prerequisites and outcomes

### Prerequisites

Picture a new GPU node that is ready for work but cannot pull its first NIM image. Before you start the NVIDIA layer, the earlier GPU and serving chapters need to be in place. Each bullet names the chapter that supplies one of the building blocks used below.

- Where do the driver, the CUDA toolkit, and the container toolkit come from? Chapter 10.9 covers them.
- Where does the NIM microservice come from? Chapter 15.7 covers the NIM microservice and the NIM Operator.
- Where does the gang scheduler come from? Chapter 16.5 covers the GPU pool and the gang scheduler.
- Where does the endpoint come from? Chapter 16.7 covers the InferenceService and the autoscaler.

### Outcomes

Picture the team lead who asks for the NVIDIA layer in one afternoon. This chapter walks through the NVAIE software stack from the driver up to NIM, NeMo, and RAPIDS. It then sets up an NGC pull-through proxy, so the cluster can pull images without holding the team's NGC credentials. Next it deploys NIM as an InferenceService bound to the right GPU pool, and it runs NeMo for LLM fine-tuning as a Kubernetes Job with gang scheduling. It finishes with RAPIDS as a GPU-accelerated dataframe service on the data engineering cluster, and with the NVAIE licensing audit covering the seat count, the per-GPU license, the renewal calendar, and the compliance report.

---

## 1. The NVAIE software stack

### 1.1 The layers

Suppose a NeMo job fails and the error points at the driver. Which layer is at fault? The application is only the top of the picture, and the failure could start several layers below it. The stack is easier to debug once you see it as layers, from the hardware up to the application. The diagram below shows five. Read it from the bottom up, because each layer depends on the one beneath it. A driver problem shows up as an application error, so you need the diagram to trace the error back down.

```mermaid
flowchart TB
    subgraph App["Application layer"]
        A[NeMo<br/>LLM framework]
        B[NIM<br/>inference microservice]
        C[RAPIDS<br/>data science]
    end

    subgraph Framework["Framework layer"]
        F1[PyTorch<br/>TensorFlow]
        F2[NVIDIA TensorRT<br/>inference optimiser]
        F3[NVIDIA Triton<br/>serving engine]
    end

    subgraph Runtime["Runtime layer"]
        R1[NVIDIA CUDA<br/>GPU compute]
        R2[NVIDIA cuDNN<br/>deep learning primitives]
        R3[NVIDIA NCCL<br/>collective communication]
        R4[NVIDIA TensorRT-LLM<br/>LLM inference]
    end

    subgraph Driver["Driver layer"]
        D1[NVIDIA GPU driver]
        D2[NVIDIA Container Toolkit]
        D3[NVIDIA Fabric Manager]
    end

    subgraph Hardware["Hardware layer"]
        H[GPU nodes<br/>H100, A100, L40S]
    end

    A --> F1
    B --> F2
    B --> F3
    C --> F1
    F1 --> R1
    F1 --> R2
    F2 --> R1
    F3 --> R1
    R1 --> D1
    D1 --> H
    D2 --> H
```

Most of these components are open source. The subscription adds enterprise support, and it covers the pieces that are not open source. In the chapter's account, the subscription buys four things beyond the open code. Each of the four is tied to one layer, so you can ask of any component which layer it sits in and what the subscription adds there.

- The driver layer gets signed updates and security patches, along with the Fabric Manager for NVLink topologies. NVLink is NVIDIA's high-speed link between GPUs in one server, and Fabric Manager is the component that sets those links up.
- The runtime layer gets CUDA, cuDNN, NCCL, and TensorRT-LLM under a support contract. CUDA is the programming platform that runs code on the GPU, and NCCL is the library that moves data between GPUs during training.
- The framework layer gets TensorRT, Triton, NeMo, and RAPIDS with pre-built containers.
- The application layer gets NIM and the NGC catalog, the container registry.

When a job fails, start by naming the layer the error comes from. A message about a missing kernel points at the runtime, while a message about a missing device points at the driver. Naming the layer first keeps you from rebuilding the application when the real fault is in the driver.

### 1.2 What the NVAIE subscription buys

Picture a procurement form that asks what the subscription adds, and nobody in the room can say. Before you buy, you need to know what changes. Most of these components are open source already. The subscription changes the support, the signing, and the production rights around them. Reading the table as a set of questions helps. For each row, ask what you would do if the open-source version failed in production at night, and who would answer.

| Layer | Open source | NVAIE subscription |
|---|---|---|
| GPU driver | Yes | Enterprise support; signed driver updates; security patches |
| CUDA | Yes | Enterprise support; version compatibility guarantees |
| Container Toolkit | Yes | Enterprise support; signed images |
| PyTorch / TensorFlow | Yes | Enterprise support; pre-built NGC containers |
| TensorRT | Yes | Enterprise support; performance guarantees |
| Triton | Yes | Enterprise support; signed images |
| NeMo | Yes | Enterprise support; pre-built containers; framework updates |
| RAPIDS | Yes | Enterprise support; pre-built containers |
| NIM | No (proprietary) | Production license; signed containers; support contract |
| NGC catalog | Free for evaluation | Production license for selected containers and models |

The subscription is priced per GPU, per year. The price depends on the GPU class and the length of the commitment. Your job is to track the per-GPU license, because finance will see it as a line item. Ask for the GPU class and commitment length behind any quote before you sign. A quote without those two details cannot be compared with the next one.

### 1.3 The license audit

Imagine an auditor asks which GPUs run an NVAIE-licensed container. If you cannot answer quickly, you have a compliance problem. The license is audited every year. NVIDIA's team, or a third-party auditor, asks you to prove that every GPU running a licensed container has a valid license. The question is simple, but answering it means joining four lists that usually live in four different places.

The audit needs four things from you:

- A list of every GPU node in the cluster.
- The license key assigned to each node.
- The containers running on each node.
- The expiration date of each license.

Most teams keep this list in a configuration management database, or CMDB, and refresh it automatically. A CMDB is an inventory of the assets and their relationships. The CMDB reads the license state from the NVAIE License Server, the GPU inventory from the cluster API, and the container list from the runtime. Build that inventory before the audit, not during it. A list assembled under audit pressure is almost always incomplete, and an incomplete list looks worse than no list at all.

---

## 2. The NGC catalog

### 2.1 What NGC is

Suppose a data scientist asks for the latest NeMo container. Where does it come from, and who decides whether your cluster may pull it? The answer is the NGC catalog. It holds three kinds of items, and each one needs a different rule.

- Containers: pre-built images for PyTorch, TensorFlow, Triton, NeMo, RAPIDS, TensorRT-LLM, and the NIM microservices.
- Models: pre-trained models such as Llama 3, Mistral, SDXL, CLIP, and NeMo Retriever.
- Resources: training scripts, notebooks, Helm charts, and reference architectures.

The catalog is free for evaluation. Production use of selected containers and models needs an NVAIE subscription. Your job is to decide which of those items the cluster may pull, and then to enforce that decision. A decision that exists only in a document is not enforced, so the rest of this section shows where the enforcement lives.

### 2.2 The NGC pull-through proxy

Picture a scale-up event, where many new nodes all reach for the same large image in the same minute. If every node pulls it from NGC directly, you waste bandwidth and depend on NGC being reachable at all times. The cluster therefore does not pull directly from NGC. It pulls through a proxy that your platform team runs, and the proxy does four jobs.

- It caches each image locally, so the first pull is slow and later pulls come from the cache.
- It authenticates to NGC with the team's NGC API key.
- It enforces licensing. Only NVAIE-licensed containers go into the cache, and open-source images come from their original registry.
- It audits every pull, so the log shows who pulled what, and when.

```yaml
# code/part16/ngc_proxy.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ngc-proxy-config
  namespace: nvaie
data:
  config.yaml: |
    upstream: nvcr.io
    cache:
      backend: gcs
      bucket: ngc-cache-${PROJECT_ID}
    licensing:
      enforce: true
      licensed_images:
        - nvcr.io/nvidia/pytorch:24.06-py3
        - nvcr.io/nvidia/tritonserver:24.06-py3
        - nvcr.io/nim/llama3-8b-instruct:1.0.0
        - nvcr.io/nvidia/nemo:24.06
    audit:
      backend: bigquery
      dataset: nvaie_audit
```

Read the file top to bottom. The upstream line says where the proxy fetches from, the cache section says where the copies live, the licensing section lists the images that are allowed in, and the audit section says where every pull is recorded. The list of licensed images is the place where the policy from the previous subsection becomes a concrete rule.

The proxy runs as a Kubernetes Deployment behind an internal Service. The cluster's pods point at the proxy, and only the proxy talks to NGC. That one-way path is what makes the audit complete, because nothing reaches NGC without going through the proxy's log.

Production Kubernetes, chapter 15, raises a catch for this design. Notary signatures are tied to the registry name, so a copy served from a cache can fail verification. Notary is the signing system that proves an image came from its publisher. Test your signing tool against the proxy address before you rely on it, because a verification failure at deploy time looks like a broken image when the real cause is the path the image took.

### 2.3 The NGC API key and IAM

Picture a departing engineer whose laptop still holds the NGC key. Whoever holds the NGC API key can pull NVIDIA's images in your name. Keep that key in one place, and let as few services read it as possible. The key lives in a secret store such as Vault or Secret Manager, and the proxy reads it at startup. A secret store encrypts the value and records who reads it, which a plain Kubernetes Secret does not do by default.

Production Kubernetes, chapter 7, explains that the built-in Kubernetes Secret API can fall short for enterprise secrets. That is why this key belongs in an external store. The access rules are simple.

- The platform team owns the NGC API key and rotates it on a schedule. This chapter uses quarterly as its example.
- Only the pull-through proxy authenticates against NGC. No other service holds the key.
- The cluster's pods authenticate to the proxy with a Kubernetes image pull secret, and they never see the NGC key.

Production Kubernetes, chapter 7, also uses a three-month rotation as its example for encryption keys. It adds that re-encrypting old data is not enough once a key has leaked. The secret itself must be rotated too. The pattern matches the cluster boundary from Chapter 16.6, where one service holds the credential, and its use is audited. Decide now who may read the NGC key, and write that rule down before the first pull. A rule written after the first leak is much harder to enforce.

---

## 3. NIM: the inference microservice

### 3.1 What NIM is

Suppose a product team needs a chat model in production by the end of the week. They could download the weights, pick an inference engine, and tune it themselves. That work takes weeks if it goes well. NIM is NVIDIA's packaged answer to that work. It is a Docker image that bundles a model, an inference engine such as TensorRT-LLM, vLLM, or Triton, and the runtime. NVIDIA signs the image, licenses it, and supports it. A container image is a sealed bundle of software, so the packaged answer means the team deploys one thing instead of assembling five.

The platform team deploys NIM as an InferenceService on Kubernetes. The NIM Operator from Chapter 15.7 does the deployment. The NIM Helm chart manages the GPU pool binding, and the image registry enforces the licensing. An operator is a controller that watches a custom resource and keeps the cluster matching it, so you describe the NIM in a short manifest and the operator does the rest.

```yaml
# Shape follows the k8s-nim-operator sample config/samples/nim/serving/standalone
# (checked against the NIMService CRD, group apps.nvidia.com). Image tag and model are examples.
apiVersion: apps.nvidia.com/v1alpha1
kind: NIMCache
metadata:
  name: llama-3-2-1b-instruct
  namespace: nim-service
spec:
  source:
    ngc:
      modelPuller: nvcr.io/nim/meta/llama-3.2-1b-instruct:1.12.0
      pullSecret: ngc-secret
      authSecret: ngc-api-secret
      model:
        engine: tensorrt_llm
        tensorParallelism: "1"
  storage:
    pvc:
      create: true
      size: "50Gi"
      volumeAccessMode: ReadWriteOnce
---
apiVersion: apps.nvidia.com/v1alpha1
kind: NIMService
metadata:
  name: llama-3-2-1b-instruct
  namespace: nim-service
spec:
  image:
    repository: nvcr.io/nim/meta/llama-3.2-1b-instruct
    tag: "1.12.0"
    pullPolicy: IfNotPresent
    pullSecrets:
      - ngc-secret
  authSecret: ngc-api-secret
  storage:
    nimCache:
      name: llama-3-2-1b-instruct
  replicas: 1
  resources:
    limits:
      nvidia.com/gpu: 1
  expose:
    service:
      type: ClusterIP
      port: 8000
```

The NIM Operator's API group is `apps.nvidia.com`, not `serving.nvidia.com`, and the manifest has no `resources.gpu.type` field. The model weights come from a separate NIMCache resource that the NIMService names. The Operator reads both resources and builds a Deployment with the right GPU binding, pull secret, model storage, and service. Read the manifest as a pair of objects. The cache holds the heavy weights once, and the service points at the cache, so scaling replicas does not mean downloading the model again.

### 3.2 The NIM model's lifecycle

Picture a NIM image that reaches production without anyone checking its signature. As you deploy a NIM, it passes through five stages, from the first pull to retirement. Each stage has an owner and a control. If you skip one, an unsigned or unretired model can end up serving traffic. Think of the stages as a relay, where each one hands the model to the next only after its check passes.

| Stage | What it is | How the platform team manages it |
|---|---|---|
| Pull | The image and the model weights are pulled from NGC | The pull-through proxy caches the image. The model weights are pulled on first deploy. |
| Sign | The image is signed by NVIDIA | The admission controller verifies the signature (cosign) |
| Deploy | The NIM Operator deploys the NIMService | The NIM Operator's Helm chart, driven by the platform team's GitOps loop |
| Serve | The NIM receives inference requests | The InferenceService, the autoscaler, and the SLO |
| Retire | The NIM is removed from production | The platform team's GitOps loop, and the registry's archived stage |

Production Kubernetes, chapter 15, notes that signature checks are often enforced by an admission webhook, which refuses unsigned images before they run. An admission webhook is a small service that the API server calls before it accepts a new object. The same chapter points out that this check sits on the deploy path. The webhook therefore has to stay highly available. If it is down, nothing new can deploy, and the failure looks like a broken pipeline rather than a broken webhook.

The lifecycle matches the model registry lifecycle from Chapter 16.6. The NIM image is the artifact, the NIMService is the registry entry, and the InferenceService is the deployment. Seeing the three names side by side makes it easier to explain the same model to an auditor and to an engineer.

### 3.3 NIM and the model registry

When someone asks which model runs in production, the answer should not depend on memory. A NIM image is a model in the NVAIE sense and also in the MLOps sense. The platform team therefore mirrors each NIM deployment in its own model registry. That way the answer lives in one place, and the answer is the same whether the question comes from a product manager or from an auditor.

```yaml
# code/part16/nim_in_registry.yaml
apiVersion: mlops.example.com/v1
kind: ModelStage
metadata:
  name: llama3-8b-instruct
  namespace: mlops
spec:
  model_name: llama3-8b-instruct
  stage: production
  version: 1.0.0
  artifact_uri: nvcr.io/nim/llama3-8b-instruct:1.0.0
  signature_id: sha256:nvidia-signed...
  nim:
    gpu_type: h100-sxm5-80gb
    replicas: 1
```

The entry records the image URI, the GPU type, the replica count, and the signature. The deployment pipeline reads that entry and asks the NIM Operator to deploy the NIMService. Keep the registry entry and the running NIMService in sync, or your records will not match production. A mismatch is the most common reason a team gives an auditor the wrong answer, and it is easy to avoid if the pipeline writes both records in the same step.

---

## 4. NeMo: the LLM framework

### 4.1 What NeMo is

Suppose you want a general model to answer questions about your company's runbooks. Training a large model from scratch is expensive, so you usually fine-tune an existing one instead. Fine-tuning means continuing the training of a model that already knows language, using your own examples so it learns your domain. The base model brings the general knowledge, and your examples bring the specifics about your runbooks, your product, and your vocabulary. NeMo is NVIDIA's framework for that kind of work. It covers three jobs.

- Pre-training: large-scale LLM training on thousands of GPUs.
- Fine-tuning: supervised fine-tuning, LoRA, QLoRA, and preference alignment with DPO or RLHF.
- Inference: NeMo Retriever, NeMo Guardrails, and NeMo Curator.

LoRA, low-rank adaptation, trains a small set of extra weights instead of the whole model, which is why it costs far less. QLoRA does the same with a compressed copy of the base model. DPO and RLHF are two ways to teach a model which answers people prefer.

The platform team uses NeMo for LLM customization. Fine-tuning runs as a Kubernetes Job with gang scheduling, and inference runs on NIM. That split keeps the expensive training work on a schedule the platform controls, and it keeps the serving path small and predictable. The two halves meet at the model registry, where a fine-tuned model is written by the training job and read by the NIM deployment. Pre-training at the top of the list is usually a job for a research group with a large cluster, not for a platform team serving a product.

### 4.2 Fine-tuning with NeMo

Picture a fine-tuning job that grabs some GPUs and then sits waiting for the rest. A fine-tuning job needs all of its GPUs at the same time. If only some of them are free, the job should wait rather than start and stall. A stalled job holds the GPUs it did get while it waits for the rest, and that wastes the pool. Gang scheduling makes that rule explicit, and the Job below uses it.

```yaml
# code/part16/nemo_finetune.yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata:
  name: nemo-finetune-llama3
spec:
  minAvailable: 8
  queue: gpu-pool
  tasks:
    - replicas: 8
      template:
        spec:
          containers:
            - name: nemo
              image: nvcr.io/nvidia/nemo:24.06
              command: [python, nemo_finetune.py]
              args: ["--model", "llama3-8b-instruct", "--dataset", "s3://my-bucket/dataset", "--lora"]
              resources:
                limits:
                  nvidia.com/gpu: 1
```

This job asks for eight tasks with one GPU each, and it waits until all eight can start. It uses LoRA to keep the training cost low. The fine-tuned model is saved to object storage and registered in the model registry. Check that the dataset path and the registry entry exist before you submit the job, because a missing dataset is the cheapest failure to catch and the most common one to skip.

### 4.3 NeMo Guardrails

Picture a customer asking a chatbot for another customer's address. An LLM app can answer a question it should refuse, or repeat personal data from its context. Guardrails are the rules that stop those answers. NeMo Guardrails is the runtime safety layer, and you write its rules as programmable steps the model must follow. The guardrail sits between the user and the model, so every request passes through it.

```python
# code/part16/snippets/nemo_guardrails.py
from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("./guardrails")
rails = LLMRails(config)

response = rails.generate(
    messages=[{"role": "user", "content": user_query}]
)
```

The snippet loads a rails configuration from a folder, builds the rails object, and sends the user's message through it. The configuration folder is where your rules live, so it belongs in version control next to the application code.

The guardrails cover four areas.

- Topic boundaries: the model refuses topics outside the application's domain.
- Factuality: the model refuses to answer when the answer is not in the retrieval context.
- PII redaction: the model removes personal data from its responses.
- Jailbreak resistance: the model refuses prompts that try to bypass the system prompt.

Guardrails run on every request, and they sometimes block a good answer. That false-positive rate is the price of safety, so measure it on your own traffic. Test the guardrail config against real questions before you ship it. A guardrail that blocks a customer's valid question is a product bug, even when the rule itself is working as written.

---

## 5. RAPIDS: GPU-accelerated data science

### 5.1 What RAPIDS is

Your feature pipeline runs in pandas on the CPU, and it takes so long that the data team is blocked. RAPIDS offers GPU versions of the tools you already use. It runs on CUDA underneath, and it runs on the same GPU nodes as your training jobs. The idea is that the code looks almost the same, and the work moves to hardware built for it.

| Library | CPU equivalent | What it accelerates |
|---|---|---|
| **cuDF** | pandas | DataFrame manipulation |
| **cuML** | scikit-learn | Machine learning algorithms |
| **cuPy** | NumPy | Array operations |
| **cuGraph** | NetworkX | Graph algorithms |
| **cuSignal** | scipy.signal | Signal processing |

The platform team runs RAPIDS as a Kubernetes Deployment on the data engineering cluster. Data scientists reach it from a Jupyter notebook or a Python script. A useful test before you adopt it is to ask where the time goes. If the CPU is busy doing arithmetic on large tables, the GPU version will help. If the time goes to waiting for files to download, the GPU will sit idle just as the CPU did. Because the library names mirror the CPU tools, a team that knows pandas can read a RAPIDS script on the first pass.

### 5.2 RAPIDS on the data engineering cluster

Picture a pandas script that takes all night to group transactions by user. Consider a script that groups transactions by user. In pandas, it reads the data, groups it on the CPU, and writes the result. The RAPIDS version keeps the same shape, but the grouping runs on the GPU. Compare the two line by line, and you will see that only the import and the reading step change in any real way.

```python
# code/part16/rapids_dataframe.py
import cudf

df = cudf.read_parquet("s3://my-bucket/dataset.parquet")
df_grouped = df.groupby("user_id").agg({"amount": "sum"})
result = df_grouped.to_pandas()  # copy back to CPU for downstream use
```

The data is read from object storage and computed on the GPU. The result is copied back to the CPU for code that comes after. The script looks almost like a pandas script, and that is the point. The main change is where the work runs. The copy back to the CPU at the end is a deliberate choice, because downstream code that expects pandas will fail on a GPU dataframe.

### 5.3 RAPIDS for feature engineering

Picture a feature job that keeps the training GPUs busy and starves the next run. Feature pipelines often wait on the CPU for long stretches. Chapter 16.3 uses RAPIDS for feature pipelines that would otherwise bottleneck the CPU. The pipeline runs in the data engineering namespace, on the same GPU pool as the training jobs. Sharing the pool is efficient, but it also means a heavy feature job can take GPUs away from a training run, so the namespace quota matters.

Speedups depend on your data and your pipeline, so this chapter does not quote one. Time the CPU version and the GPU version on the same data before you move a pipeline. That measurement is what justifies the move. A pipeline that is mostly reading from a slow store will not speed up much, because the GPU is waiting on the same disk.

---

## 6. Operating NVAIE on GKE

Picture the night a pull fails and the first question is which of the five pieces is down. Running NVAIE on GKE means watching five components, and each one can fail without the others noticing. The sections below cover where each piece runs, who may touch it, and which signals warn you before a license or a pull goes wrong.

### 6.1 The components

Picture a dashboard with five boxes, and only one of them is red. Five components make up the NVAIE service on GKE, and each one can fail on its own. Each needs an owner and a target. The table shows where each component runs, what it stores data in, and an example target. The targets are examples, not limits from NVIDIA. Choose your own numbers based on what your users need. A target that nobody reads is decoration, so pair each one with the team that gets paged when it is missed.

| Component | Where it runs | Backing store | Example SLO (choose your own) |
|---|---|---|---|
| NGC pull-through proxy | Kubernetes Deployment | GCS bucket for cache; BigQuery for audit | Pull latency p99 < 30 s |
| NIM Operator | Kubernetes Deployment | etcd | NIMService reconcile p99 < 30 s |
| NeMo fine-tuning | Kubernetes Job | Object store for datasets and models | Training SLO per job |
| RAPIDS | Kubernetes Deployment on data cluster | Object store for dataframes | Query latency p99 < 1 s |
| NVAIE License Server | NVIDIA-managed | n/a | API latency p99 < 1 s |

The NVAIE License Server is the one component you do not operate yourself. You can still watch its latency from your side, which is why it has a row in the table. etcd is the key-value store that holds the Kubernetes API state, so an etcd problem shows up as slow reconciliation everywhere.

### 6.2 IAM and the audit log

Picture an auditor asking who pulled an image last Tuesday. A pull, a deployment, and a fine-tuning run each change what runs in your cluster. Each of those actions should map to a role and leave a record. The platform team owns the access model for NVAIE. A role is a named set of permissions, so the question "who can do this" always has a short answer.

| Role | Who | What they can do |
|---|---|---|
| `nvaie.license.reader` | Platform team | Read license state from the License Server |
| `nvaie.image.puller` | The pull-through proxy | Pull from NGC; cache; audit |
| `nvaie.cluster.reader` | Cluster | Pull from the pull-through proxy; deploy NIM |
| `nvaie.admin` | Platform team | Manage the pull-through proxy; manage the License Server integration |

Keep each role narrow. The proxy pulls from NGC, while the cluster only pulls through the proxy and deploys NIM. The audit log records every pull from the proxy, every NIM deployment, and every NeMo fine-tuning run. Those records are your proof of NVAIE compliance. A role that can do everything is the first thing an auditor will question, so the admin role should be held by as few people as possible.

### 6.3 Observability

Picture a renewal date that passes over a holiday weekend. A license can lapse without any alarm going off until the renewal date passes. Because nothing on the cluster breaks in advance, the warning has to come from a calendar-aware rule rather than from a service metric. Metrics and alerts are how you see that coming. The table lists the signals to watch. The thresholds are examples, so set your own. Most of these signals are about the customer, but the license expiration row is about the paperwork, and it is the one most teams forget.

| Metric | Why it matters | Example alert (set your own) |
|---|---|---|
| NGC pull latency p99 | Hot path for every NIM deploy | > 60 s |
| NIM inference latency p99 | Customer-facing SLO | > SLO threshold |
| NIM GPU utilisation | Affects cost | < 30% for 30 min |
| NIM error rate | Customer-facing SLO | > 0.1% |
| License expiration | Affects compliance | < 30 days remaining |
| NeMo training duration | Affects throughput | > baseline for 3 runs |

The license expiration alert matters most. The chapter's example fires 30 days before expiry, which leaves time to renew and to record the renewal in the audit log. Set up that alert before the first renewal date arrives. Waiting until the license has already lapsed means the NIM containers are failing while you are still arranging the purchase.

---

## 7. How it fails

Picture the same outage reappearing on a new cluster every few weeks. Five failure modes come back again and again. Learn their symptoms, and you will recognize the next outage faster. Each one below follows the same three steps: the symptom you see, the diagnosis that explains it, and the fix that closes it.

### 7.1 "The cluster cannot pull from NGC"

Picture a pod that has been stuck in `ImagePullBackOff` since the deploy, and nobody has noticed yet. A pod stuck in `ImagePullBackOff` is a common NGC problem, and the pod never starts. The kubelet keeps retrying the pull with longer and longer waits, which is why the pod looks stuck rather than failed.

**Symptom:** The pod's image pull fails with `ImagePullBackOff`, and the error reads "unauthorized: authentication required". The pod stays stuck.

**Diagnosis:** One of three things usually went wrong. The image pull secret is missing, the pull-through proxy is misconfigured, or the NGC API key has expired. The error text is the same for all three, so you have to check each one.

**Fix:** Check the proxy's NGC API key, and rotate it if it has expired. Confirm the pod's image pull secret, then confirm that the pod's namespace can reach the proxy. Working through the three checks in that order is faster than guessing.

### 7.2 "The NVAIE license is expired"

**Symptom:** The NIM containers start, then fail with a license error. The NIM service reports that the license has expired, and the cluster runs degraded. Customers may see errors before anyone on the platform team knows why.

**Diagnosis:** The renewal was missed, and the audit did not catch it in time. A renewal date on a calendar is not an alert, so the miss is usually a process gap.

**Fix:** Renew the license now, and redeploy the NIM containers. Confirm the license state with the NVAIE License Server. Then add an expiration alert, using the 30-day example from Section 6.3 or a window you choose.

### 7.3 "The NeMo fine-tuning is OOM"

**Symptom:** The NeMo fine-tuning pod crashes with `OOMKilled`. The pod's memory request was too low for the job. OOM means out of memory, and the kernel kills the process when it runs out.

**Diagnosis:** The model is too large for the GPU's memory. A 70B model needs parallelism across several GPUs. Parallelism means splitting the model's weights and work across more than one GPU, so no single card has to hold all of it.

**Fix:** Raise the GPU count from 1 to 4 or 8. Turn on FSDP or DeepSpeed ZeRO-3, covered in Chapter 14.5. Check the memory budget before the next run, so the change is based on a number rather than a guess.

### 7.4 "The NIM autoscaler is too aggressive"

**Symptom:** The NIM replicas scale up to 100 in response to a traffic spike. The GPU pool runs out, and other workloads cannot get GPUs. The spike may last only minutes, but the damage to the rest of the cluster lasts longer.

**Diagnosis:** The autoscaler's `maxReplicas` is too high. The autoscaler also does not respect your team's GPU quota, so it asks for more GPUs than the team is allowed to hold.

**Fix:** Lower `maxReplicas`. Bind the NIM to the team's Kueue LocalQueue, so the Kueue admission controller enforces the quota. Kueue is the queueing system that admits jobs only when quota is free. With that binding in place, a traffic spike can make the NIM wait in a queue, but it cannot take GPUs that another team has paid for. Choose the replica ceiling from the quota, not from the peak you hope to survive.

### 7.5 "The RAPIDS job uses a different CUDA version than the training job"

**Symptom:** The RAPIDS feature pipeline runs CUDA 12.2, and the training job runs CUDA 12.4. The data handoff fails because the formats do not match.

**Diagnosis:** The RAPIDS container and the training container use different CUDA versions. The chapter attributes the failure to a data format mismatch. Containers that look compatible can still disagree about the bytes they hand over.

**Fix:** Pin all GPU containers in the namespace to one CUDA version. The platform team's pattern is "one CUDA version per namespace", declared in the namespace's ResourceQuota. A ResourceQuota is the Kubernetes object that caps what a namespace may use, and it is a convenient place to write down the version rule.

---

## 8. Hands-on lab

Picture a platform team that has to show an auditor a working path from pull to log. This lab sets up the NGC pull-through proxy, deploys a NIM microservice, runs a NeMo fine-tuning job, and checks the licensing audit. Run the steps in order, because each one depends on the last. The lab is **untested** in this repository, so treat every expected output as a claim to check.

### 8.1 Prerequisites

Picture a lab that stops at the first command because the GPU node pool was never created. Before you begin, make sure the cluster, the subscription, and the operator are ready. Missing any one of them will stop the lab at the first step that needs it.

- A GKE Autopilot or Standard cluster, version 1.27 or later, with at least one H100 GPU node.
- An NVAIE subscription with an NGC API key.
- The NIM Operator installed with Helm.
- A GPU node pool with H100 or A100 GPUs.

### 8.2 Step 1: configure the NGC API key

Picture a fresh namespace with no credentials in it, and a NIM that cannot download its model. Start by storing the key as two Kubernetes secrets in the `nvaie` namespace. They use the same names as the NIM examples in Section 3.1. The first, `ngc-api-secret`, holds the key itself for the NIM to download models. The second, `ngc-secret`, is the image pull secret for `nvcr.io`. Both secrets are needed because the model download and the image pull are separate requests with separate credentials.

```bash
kubectl create namespace nvaie
kubectl create secret generic ngc-api-secret \
  --namespace nvaie \
  --from-literal=NGC_API_KEY=${NGC_API_KEY}
kubectl create secret docker-registry ngc-secret \
  --namespace nvaie \
  --docker-server=nvcr.io \
  --docker-username='$oauthtoken' \
  --docker-password=${NGC_API_KEY}
# expected: both secrets are created in the nvaie namespace
```

### 8.3 Step 2: deploy the NGC pull-through proxy

Picture the first pull that takes minutes because nothing is cached yet. Next, install the proxy with the cache and the audit log pointed at your project. The cache keeps later pulls local, and the audit log is where the pull records will appear in the final step.

```bash
helm install ngc-proxy my-charts/ngc-proxy \
  --namespace nvaie \
  --set ngc.upstream=nvcr.io \
  --set cache.backend=gcs \
  --set cache.bucket=${PROJECT_ID}-ngc-cache \
  --set audit.backend=bigquery \
  --set audit.dataset=nvaie_audit
# expected: the proxy pod is running; the proxy service is reachable from the cluster
```

### 8.4 Step 3: deploy the NIM microservice

Picture the NIM pod waiting for a GPU that another team is still holding. Then deploy the NIM with one GPU and the pull secret it needs. The NIM is the first real workload on the proxy, so it doubles as a test of the proxy's cache and its licensing rule.

```bash
helm install nim-llama3 nvidia/nim-llm \
  --namespace nvaie \
  --set model.name=llama3-8b-instruct \
  --set image.repository=nvcr.io/nim \
  --set image.tag=1.0.0 \
  --set resources.limits.nvidia\\.com/gpu=1 \
  --set imagePullSecrets[0]=ngc-secret
# expected: the NIM pod is running; the InferenceService URL is printed
```

### 8.5 Step 4: query the NIM

Picture the on-call engineer who asks whether the model is actually answering yet. Send one chat request to confirm that the model answers. A running pod only tells you the container started, so the answer is the real test that the model works.

```bash
URL=$(kubectl get nimservice llama3-8b-instruct -n nvaie -o jsonpath='{.status.url}')
curl -X POST $URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3-8b-instruct", "messages": [{"role": "user", "content": "What is MLOps?"}]}'
# expected: a JSON response with the model's answer
```

### 8.6 Step 5: run a NeMo fine-tuning

Picture a training run scheduled for tonight that may or may not get all its GPUs. Submit the fine-tuning Job and watch it start. Watching matters here, because a gang job that cannot get all its GPUs will sit in a waiting state rather than fail.

```bash
kubectl apply -f code/part16/nemo_finetune.yaml
kubectl get job -n nvaie -w
# expected: the fine-tuning runs on 8 GPUs; the model is saved to object storage
```

### 8.7 Step 6: verify the licensing audit

Picture the auditor's question arriving the morning after the lab. Finally, check that the pulls you just made appear in the audit log. If they do not, the proxy is not recording pulls, and the compliance answer from the license audit section is not yet true.

```bash
bq query --use_legacy_sql=false \
  "SELECT timestamp, image, user
   FROM \`${PROJECT_ID}.nvaie_audit.pulls\`
   ORDER BY timestamp DESC
   LIMIT 10"
# expected: a list of the most recent NGC pulls with the user and the image
```

### 8.8 What to record

Picture a manager who stops you in a hallway and asks for the current status. After the lab, record five answers that you can give quickly, without digging through dashboards. The questions match the ones an auditor or an on-call engineer is likely to ask on the same day.

1. What is the current NIM InferenceService URL?
2. What is the most recent NGC pull, and what user pulled it?
3. What is the current NVAIE license expiration date?
4. What is the most recent NeMo fine-tuning run, and what model was fine-tuned?
5. What is the cost per NVAIE-licensed GPU per month?

If any answer takes you too long, the NVAIE stack is not yet ready to run as a production service. Set your own time limit for this check, because the right limit depends on how often your team gets asked these questions.

---

## Exercises

Picture a platform team that has run the lab once and now wants the NVIDIA layer to survive a real change. Each exercise below adds one capability, and the solution sketch shows one way to build it. Work through them in order if you can, since later exercises reuse the proxy and the audit log from earlier ones.

1. **Add a pull-through proxy for a second registry.** Your proxy already serves NGC. Now let it pull from a private registry as well, and enforce licensing per team. *Solution sketch:* a proxy configuration with a second upstream, and a per-team allow-list.
2. **Add a NIM canary.** Deploy a second NIM with a small share of the traffic, and check its SLO before you promote it. *Solution sketch:* an Argo Rollouts canary strategy aimed at the NIMService, with an analysis template that watches the SLO metrics.
3. **Add a NeMo fine-tuning pipeline.** Build an Argo Workflow that reads from the feature store, runs the fine-tuning, and writes the model to the registry. *Solution sketch:* an Argo DAG with stages for data preparation, fine-tuning, evaluation, and registration.
4. **Add a RAPIDS feature pipeline.** Build a RAPIDS pipeline on the data engineering cluster, and measure it against your pandas baseline. *Solution sketch:* a Kubernetes Job that uses the RAPIDS container, reads from object storage, and writes to the feature store.
5. **Add a NVAIE license expiration alert.** Configure a Prometheus alert that fires before the license expires. The chapter's example window is 30 days. *Solution sketch:* a Prometheus rule that reads the NVAIE License Server's API and alerts on `expiration_date - today < 30 days`.
6. **Add a NIM autoscaler bound to the team's quota.** Make the NIM autoscaler respect the team's Kueue quota, so it never exceeds it. *Solution sketch:* a Kueue LocalQueue that bounds the NIM's GPU requests, with the autoscaler reading that quota.

---

## Checkpoint questions

<details><summary>1. An auditor asks which GPUs run an NVAIE-licensed container, and you cannot answer quickly. What should you have built?</summary>
An inventory before the audit. The audit needs a list of every GPU node, the license key for each node, the containers running on each node, and each license's expiry date. Most teams keep this in a CMDB that refreshes automatically. It reads license state from the NVAIE License Server, the GPU inventory from the cluster API, and the container list from the runtime.
</details>

<details><summary>2. NIM containers start and then fail with a license error that says the license has expired. What is the cause and what do you do?</summary>
The renewal was missed and the audit did not catch it in time. Renew the license now and redeploy the NIM containers. Confirm the license state with the NVAIE License Server. Then add an expiration alert, for example 30 days before expiry, or a window you choose.
</details>

<details><summary>3. A NeMo fine-tuning pod crashes with `OOMKilled`. What does the chapter say the cause is, and what is the fix?</summary>
The chapter says the model is too large for the GPU's memory, and that a 70B model needs parallelism across several GPUs. Raise the GPU count from 1 to 4 or 8. Turn on FSDP or DeepSpeed ZeRO-3, covered in Chapter 14.5. Check the memory budget before the next run.
</details>

<details><summary>4. A traffic spike scales NIM replicas to 100, the GPU pool runs out, and other workloads cannot get GPUs. What went wrong?</summary>
The autoscaler's `maxReplicas` is too high and the autoscaler does not respect your team's GPU quota. Lower `maxReplicas`. Bind the NIM to the team's Kueue LocalQueue, so the Kueue admission controller enforces the quota.
</details>

<details><summary>5. The RAPIDS pipeline runs CUDA 12.2 and the training job runs CUDA 12.4. The data handoff fails. What is the fix?</summary>
The two containers use different CUDA versions, and the chapter attributes the failure to a data format mismatch. Pin all GPU containers in the namespace to one CUDA version. The platform team's pattern is one CUDA version per namespace, declared in the namespace's ResourceQuota.
</details>

<details><summary>6. Someone asks which NIM model runs in production, and your records do not match what is running. What was missed?</summary>
The NIM deployment was not mirrored in the model registry, or the entry fell out of sync with the running NIMService. The platform team mirrors each deployment as a registry entry that records the image URI, GPU type, replica count, and signature. The deployment pipeline reads that entry and asks the NIM Operator to deploy. Keep the entry and the running NIMService in sync.
</details>

<details><summary>7. Why does the cluster pull NGC images through a proxy instead of directly?</summary>
Direct pulls waste bandwidth when every node fetches the same large image, and they depend on NGC being reachable. The proxy caches each image, so later pulls come from the cache. It is also the only service that holds the NGC API key, it enforces which images are licensed, and it audits every pull.
</details>

<details><summary>8. Why can image signature verification fail when the image comes from a cache?</summary>
*Production Kubernetes*, chapter 15, says Notary signatures are tied to the registry name. A copy served from a cache has a different registry name, so verification can fail. Test your signing tool against the proxy address before you rely on it.
</details>

<details><summary>9. Why does the NeMo fine-tuning Job use gang scheduling with `minAvailable: 8`?</summary>
The job needs all of its GPUs at the same time. If only some are free, the job should wait rather than start and stall. With `minAvailable: 8` and eight tasks of one GPU each, nothing starts until all eight can start.
</details>

<details><summary>10. Why does the NIM deployment use a separate NIMCache resource alongside the NIMService?</summary>
The model weights come from a separate NIMCache resource that the NIMService names. The NIMCache pulls the model from NGC into storage, which in the example is a 50Gi persistent volume claim. The Operator reads both resources and builds a Deployment with the right GPU binding, pull secret, model storage, and service.
</details>

<details><summary>11. Why must the admission webhook that verifies image signatures be highly available?</summary>
It refuses unsigned images before they run, so it sits on the deploy path. If it is down, deployments cannot pass its check. *Production Kubernetes*, chapter 15, makes this point. The webhook is therefore a production service with its own availability target.
</details>

<details><summary>12. When would you buy the NVAIE subscription instead of assembling the stack from open source, and what do you give up?</summary>
Buy the subscription when you want enterprise support, signed images, and the right to use licensed containers in production. NIM is proprietary and needs the production license. You pay per GPU per year. The alternative is to run PyTorch, TensorRT, Triton, NeMo, and RAPIDS from open source without the contract, and you pay engineers to maintain them.
</details>

<details><summary>13. When would you fine-tune with LoRA instead of training from scratch, and what do you give up?</summary>
Fine-tune an existing model when you want it to answer questions about your own material, such as company runbooks. Training a large model from scratch is expensive. LoRA keeps the training cost low. You give up the freedom of choosing the base model's design, because you start from someone else's model.
</details>

<details><summary>14. A team needs a chat model in production this week. When do you choose NIM over picking and tuning an engine yourself?</summary>
Choose NIM when speed and support matter. It bundles a model, an inference engine such as TensorRT-LLM, vLLM, or Triton, and the runtime, and NVIDIA signs, licenses, and supports the image. You give up control over the engine choice and you need a production license, since NIM is proprietary.
</details>

<details><summary>15. Your pandas feature pipeline blocks the data team. Do you move it to RAPIDS, and how do you decide?</summary>
Time the CPU version and the GPU version on the same data first. Speedups depend on your data and your pipeline, so the chapter quotes none. The script barely changes, because `cudf` looks like pandas and the main change is where the work runs. The cost is that the pipeline now needs GPU nodes and a copy back to the CPU for downstream code.
</details>

<details><summary>16. The fine-tuning Job asks for eight tasks with one GPU each, and only six GPUs are free. What happens?</summary>
Nothing starts. The Job has `minAvailable: 8`, so it waits until all eight GPUs can be given at once. Six running tasks would stall with two missing. The job starts when two more GPUs free up.
</details>

<details><summary>17. Each NIM replica requests one GPU. A spike scales it to 100 replicas on a pool of 120 GPUs, and a fine-tuning job needs 8. What is left, and what is the result?</summary>
The NIM takes 100 GPUs, which leaves 20. The 8-GPU fine-tuning job fits, but any workload that needs more than 20 more GPUs cannot start. The pool and sizes here are example numbers. The fix is a lower `maxReplicas` and a Kueue quota.
</details>

<details><summary>18. The NGC API key is rotated quarterly. How many rotations a year is that, and if the last was on 1 February, when is the next?</summary>
Quarterly means every three months, so 12 divided by 3 is 4 rotations a year. If the last was 1 February, the next is 1 May. The quarterly cadence is the chapter's example. If a key leaks, re-encrypting old data is not enough and the secret itself must be rotated.
</details>

<details><summary>19. A NeMo job fails and the error points at the driver. In what order do you look?</summary>
First name the layer the error comes from. Read the stack from the bottom up, because each layer depends on the one beneath it. Second check the driver layer, which holds the GPU driver, the Container Toolkit, and the Fabric Manager. Third check the runtime layer above it, such as CUDA, cuDNN, and NCCL.
</details>

<details><summary>20. A pod is stuck in `ImagePullBackOff` with "unauthorized: authentication required". In what order do you check?</summary>
First check the proxy's NGC API key and rotate it if it has expired. Second confirm the pod's image pull secret exists and is correct. Third confirm that the pod's namespace can reach the proxy. These are the three usual causes in the chapter.
</details>

---

## Sources and review notes

- NVIDIA AI Enterprise (NVAIE) documentation. Source for the software stack layers, the licensing model, the NGC catalog, and the support contract.
- NVIDIA NGC catalog documentation. Source for the container and model inventory, the pull-through proxy pattern, and the licensing enforcement.
- NVIDIA NIM documentation. Source for the inference microservice, the NIM Operator, the model lifecycle, and the GPU pool binding.
- NVIDIA NeMo framework documentation. Source for the LLM framework, the fine-tuning patterns, the NeMo Guardrails, and the NeMo Retriever.
- NVIDIA RAPIDS documentation. Source for the GPU-accelerated dataframe library, the cuDF / cuML / cuPy / cuGraph libraries, and the feature engineering patterns.
- NVIDIA Zero-to-Hero Volume 14 (`chapter-01-introduction.md` through `chapter-06-rapids.md`). Source for the introduction to the NVAIE stack, the licensing chapter, the NGC chapter, the NIM chapter, the NeMo chapter, and the RAPIDS chapter. The wording has been rewritten in the handbook's voice.

### Cross-references to other handbook chapters

- Chapter 10.9 (NVIDIA software stack) for the driver, CUDA, and container toolkit.
- Chapter 15.7 (NVIDIA NIM and NIM Operator) for the inference microservice in detail.
- Chapter 16.5 (Distributed compute) for the GPU pool and the gang scheduler.
- Chapter 16.7 (Serving platforms) for the InferenceService and the autoscaler.

### Migrated from `nvidia-devops`

The NVAIE stack overview, the NGC pull-through proxy pattern, and the NeMo / RAPIDS chapter structure draw on Volume 14 chapters 1-6. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The NVAIE pricing model in Section 1.2 is starting points; specific prices vary by commitment, GPU class, and region.
- The NIM and NeMo versions assumed in the lab should be pinned against the current NGC releases before production use.
- The NeMo Guardrails configuration in Section 4.3 is a sketch; production guardrails require careful design and testing.

### Not verified on live hardware

- The lab in Section 8 is **untested** against a live GKE cluster in this repository.
- The NGC API key in the lab is a placeholder; production keys are rotated quarterly.
- The NVAIE license costs in the lab are illustrative; production costs vary by commitment.
