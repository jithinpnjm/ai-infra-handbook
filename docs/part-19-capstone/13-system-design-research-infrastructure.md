---
id: "c19-13"
title: "19.13 System design: research infrastructure"
sidebar_label: "19.13 System design: research infrastructure"
sidebar_position: 13
description: "System design for research infrastructure: notebook environments, experiment tracking, dataset versioning, JupyterHub multi-tenancy, shared storage, FAIR data principles, and the design review checklist for the research platform."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "On-prem"
---

# 19.13 System design: research infrastructure

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | On-prem |
| Part | Part 19: Capstones, design and interview readiness |
| Primary sources | NVIDIA Zero-to-Hero Volume 23 (`chapter-12-system-design-research-infrastructure.md`); NVIDIA Zero-to-Hero Volume 8; Part 16 (MLOps) |
| Cross-references | Chapter 16.2 (Data versioning); Chapter 16.3 (Data pipelines); Chapter 19.10 (Customer workshops) |
| Coverage file | `planning/coverage/chapters/19-13.md` |
| Claim & number ledger | `planning/ledgers/19-13.md` |

## Research infrastructure design at a glance

```mermaid
flowchart TB
    subgraph Notebooks["Notebooks"]
        JH[JupyterHub]
        IM[Per-user images]
    end

    subgraph Tracking["Tracking"]
        ML[MLflow<br/>tracking + registry]
    end

    subgraph Data["Data"]
        DVC[DVC<br/>versioning]
        OBJ[Object storage<br/>datasets]
    end

    subgraph Tenants["Multi-tenancy"]
        T1[Team A]
        T2[Team B]
        T3[Team C]
    end

    subgraph FAIR["FAIR data"]
        F1[Findable]
        F2[Accessible]
        F3[Interoperable]
        F4[Reusable]
    end

    JH --> IM
    IM --> ML
    ML --> OBJ
    ML --> DVC
    JH --> T1
    JH --> T2
    JH --> T3
    DVC --> OBJ
    OBJ --> F1
    OBJ --> F2
    OBJ --> F3
    OBJ --> F4
```

The research infrastructure: JupyterHub notebooks, MLflow tracking, DVC data versioning, FAIR principles.

## Why this matters for AI infrastructure

Research infrastructure is the production shape of data science at scale. The system design covers: notebook environments (JupyterHub), experiment tracking (MLflow), dataset versioning (DVC), shared storage, multi-tenancy, FAIR data principles, and the security. A team that has run a research infrastructure design can describe each piece; a team that has run the design review can identify the gaps.

The research infrastructure system design is the platform engineer's blueprint for the data science layer. The blueprint is the input to the procurement order; the blueprint is the input to the customer workshop; the blueprint is the input to the production deployment.

```text
Why the research infrastructure system design matters (V23 ch12; Part 16):
- Research infrastructure is the production shape of data science at scale.
  The system design is the blueprint that ties notebook environments,
  experiment tracking, dataset versioning, and shared storage together.
- The system design has three perspectives: the platform engineer's view
  (how to size the components); the data scientist's view (how to use the
  components); the FinOps lead's view (how to track the cost).
- The system design is the reference architecture. Every chapter in Part 16
  maps to a section of the system design.
```

Three operational realities make this chapter a platform-team deliverable rather than a tutorial:

1. **The system design is the blueprint.** The platform team references the system design when deploying JupyterHub; the platform team references the system design when configuring MLflow.
2. **The system design is the interview anchor.** The candidate is asked "how would you design research infrastructure?"; the candidate points at this system design.
3. **The system design is the data scientist's guide.** The data scientist uses the system design to understand the platform; the data scientist uses the system design to plan experiments.

**Before a team can claim they have designed research infrastructure, the team must have produced this system design. A team that has not produced the system design has not integrated the pieces.**

## Prerequisites and outcomes

### Prerequisites

- Chapter 16.2 (Data versioning and experiment tracking).
- Chapter 16.3 (Data pipelines and feature stores).
- Chapter 19.10 (Customer workshops).

### Outcomes

After completing this chapter you will be able to:

1. Deploy JupyterHub with multi-tenancy and per-user notebook environments.
2. Configure MLflow for experiment tracking and model registry.
3. Configure DVC for dataset versioning with FAIR data principles.
4. Design the shared storage layer for dataset and notebook access.
5. Implement the security controls for research data (RBAC, encryption, audit).
6. Run the design review with the platform team and the research team.

---

## 1. The notebook environment

### 1.1 JupyterHub

JupyterHub is the multi-tenant notebook server. JupyterHub spawns a notebook server for every user; the notebook server has the user's storage and the user's kernels.

```yaml
# code/part19/jupyterhub.yaml (shape only)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jupyterhub
  namespace: research
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jupyterhub
  template:
    metadata:
      labels:
        app: jupyterhub
    spec:
      containers:
        - name: jupyterhub
          image: jupyterhub/jupyterhub:4.0
          env:
            - name: JUPYTERHUB_CRYPT_KEY
              valueFrom:
                secretKeyRef:
                  name: jupyterhub-crypt-key
                  key: crypt-key
```

The pattern is: JupyterHub runs as a single Deployment; JupyterHub spawns per-user notebook servers; the notebook servers have the user's storage.

### 1.2 The per-user notebook server

The per-user notebook server is a Kubernetes pod spawned by JupyterHub. The notebook server has the user's kernels; the notebook server has access to the user's storage.

```text
Per-user notebook server:
- Image: jupyter/scipy-notebook:latest
- CPU: 2 cores
- Memory: 8 GB
- GPU: 0-1 (optional, requested by the user)
- Storage: 10 GB per user
```

The pattern is: every user has a notebook server; the notebook server has the user's storage; the notebook server has the user's kernels.

---

## 2. The experiment tracking

### 2.1 MLflow

MLflow is the experiment tracking and model registry. MLflow tracks the experiments; MLflow stores the model artefacts; MLflow serves the model artefacts.

```yaml
# code/part19/mlflow.yaml (shape only)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow
  namespace: research
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mlflow
  template:
    metadata:
      labels:
        app: mlflow
    spec:
      containers:
        - name: mlflow
          image: ghcr.io/mlflow/mlflow:2.10
          env:
            - name: BACKEND_STORE_URI
              value: postgresql://mlflow:mlflow@postgres:5432/mlflow
            - name: DEFAULT_ARTIFACT_ROOT
              value: gs://mlflow-artifacts/research
```

The pattern is: MLflow tracks the experiments; MLflow stores the model artefacts; MLflow is the source of truth for the model lineage.

---

## 3. The dataset versioning

### 3.1 DVC

DVC is the dataset versioning tool. DVC tracks the dataset files; DVC stores the dataset metadata in Git; DVC stores the dataset files in object storage.

```bash
# Initialise DVC
dvc init

# Track a dataset
dvc add data/churn.csv

# Commit the metadata to Git
git add data/.gitignore data/churn.csv.dvc
git commit -m "v1 of churn dataset"

# Push the data to object storage
dvc push
```

The pattern is: DVC stores the metadata in Git; DVC stores the data in object storage; the team can reproduce the dataset from Git + object storage.

### 3.2 The FAIR data principles

The FAIR data principles are: Findable, Accessible, Interoperable, Reusable.

| Principle | What it means | Implementation |
|---|---|---|
| **Findable** | The dataset has a unique identifier and rich metadata | DVC metadata; MLflow tags |
| **Accessible** | The dataset is accessible via standard protocols | Object storage; signed URLs |
| **Interoperable** | The dataset is in a standard format | Parquet; CSV; JSON |
| **Reusable** | The dataset has a clear license and provenance | DVC provenance; license metadata |

The pattern is: every dataset follows the FAIR principles; the FAIR principles are documented; the FAIR principles are auditable.

---

## 4. The shared storage

### 4.1 The storage options

The storage options are: parallel file system (Lustre), object storage (S3, GCS), NFS.

| Storage | Strength | Weakness | Best fit |
|---|---|---|---|
| **Parallel FS (Lustre)** | High throughput; POSIX semantics | Complex to operate | Dataset storage; notebook access |
| **Object storage** | Cheap; durable; scalable | High latency; not POSIX | Dataset versioning; model artefacts |
| **NFS** | Simple; POSIX semantics | Single point of failure | User home directories; small datasets |

The pattern is: the storage tier is per workload type; the storage tier is sized for the throughput requirement.

---

## 5. Day-2 operations

### 5.1 The on-call runbook

The on-call runbook is the guide for the on-call engineer when the research infrastructure fails.

```markdown
## Runbook: JupyterHub down

### Symptoms
- Users cannot access their notebooks
- JupyterHub is not responding

### Diagnostic steps
1. Verify JupyterHub is running: kubectl get pods -n research
2. Check JupyterHub logs: kubectl logs -n research deployment/jupyterhub
3. Check the database connection: psql -h postgres.research -U mlflow

### Mitigation steps
1. Restart JupyterHub: kubectl rollout restart -n research deployment/jupyterhub
2. Verify users can access their notebooks
3. Escalate to the platform team if the issue persists

### Escalation path
If JupyterHub is still down after the mitigation, page the platform team.
```

The pattern is: the runbook has the symptoms, the diagnostic steps, the mitigation steps, the escalation path.

---

## 6. Hands-on lab

This lab walks through the research infrastructure system design: the JupyterHub deployment, the MLflow configuration, the DVC dataset versioning. The lab is **untested** in this repository.

### 6.1 Prerequisites

- A simulated research workload.
- The reference architectures from the capstone templates.

### 6.2 Step 1: deploy JupyterHub

```bash
helm install jupyterhub jupyterhub/jupyterhub \
  --namespace research --create-namespace
```

### 6.3 Step 2: configure MLflow

```bash
helm install mlflow my-charts/mlflow \
  --namespace research
```

### 6.4 Step 3: initialise DVC

```bash
cd data
dvc init
git add .dvc .dvcignore
git commit -m "Initialise DVC"
```

### 6.5 Step 4: track a dataset

```bash
dvc add data/churn.csv
git add data/.gitignore data/churn.csv.dvc
git commit -m "v1 of churn dataset"
dvc push
```

### 6.6 What to record

After the lab, you should be able to answer five questions in five seconds each:

1. What is the current JupyterHub status?
2. What is the current MLflow status?
3. What is the current DVC status?
4. What is the current FAIR data status?
5. What is the current research data lineage status?

If any takes more than 30 seconds, the research infrastructure is not yet a production service. The lab is **untested** against a live cluster.

---

## Exercises

1. **Add a new notebook image.** Add a new notebook image to JupyterHub. *Solution sketch:* the JupyterHub profile configuration.
2. **Add a new MLflow backend.** Add a new MLflow backend (e.g. Databricks, Vertex AI). *Solution sketch:* the MLflow backend configuration.
3. **Add a new DVC remote.** Add a new DVC remote storage. *Solution sketch:* the DVC remote configuration.
4. **Add a new FAIR data check.** Add a new automated FAIR data check. *Solution sketch:* the FAIR data check script.
5. **Add a new shared storage option.** Add a new shared storage option (e.g. Weka). *Solution sketch:* the storage configuration.
6. **Add a research on-call runbook.** Document the on-call runbook for the research infrastructure. *Solution sketch:* the Markdown runbook.

---

## Checkpoint questions

<details><summary>1. What is the research infrastructure system design?</summary>
The blueprint that ties JupyterHub, MLflow, DVC, shared storage, multi-tenancy, and the FAIR data principles together. The system design is the input to the procurement order; the system design is the input to the customer workshop.
</details>

<details><summary>2. What is JupyterHub?</summary>
The multi-tenant notebook server. JupyterHub spawns a per-user notebook server; the notebook server has the user's storage and the user's kernels. JupyterHub is the foundation of the data science workflow.
</details>

<details><summary>3. What is DVC?</summary>
The dataset versioning tool. DVC tracks the dataset files; DVC stores the metadata in Git; DVC stores the data in object storage. DVC is the foundation of the dataset lifecycle.
</details>

<details><summary>4. What are the FAIR data principles?</summary>
Findable, Accessible, Interoperable, Reusable. The principles are the foundation of the dataset lifecycle. Every dataset follows the FAIR principles.
</details>

<details><summary>5. What is the most common research infrastructure failure?</summary>
JupyterHub is down. Users cannot access their notebooks; the data science workflow is blocked. The fix is to restart JupyterHub; verify the database connection; escalate to the platform team.
</details>

<details><summary>6. What is the most dangerous research infrastructure failure?</summary>
MLflow is down. The experiment tracking is lost; the model lineage is lost. The fix is to restore MLflow from the backup; verify the database connection; verify the object storage.
</details>

<details><summary>7. What is the most expensive research infrastructure mistake?</summary>
Not versioning the datasets. The team cannot reproduce the experiments; the team cannot debug the model regressions. The fix is to use DVC for every dataset; track the dataset lineage.
</details>

<details><summary>8. What is the relationship between research infrastructure and the inference capstone?</summary>
The research infrastructure produces the model; the inference capstone serves the model. The research infrastructure is the upstream layer; the inference capstone is the downstream layer. The two are complementary.
</details>

<details><summary>9. What is the most common research infrastructure security failure?</summary>
The notebook image is not signed. A compromised image can be deployed; the notebooks are compromised. The fix is to enable image signing; configure the admission controller.
</details>

<details><summary>10. What is the most expensive research infrastructure security mistake?</summary>
The dataset is not encrypted at rest. A compromised dataset can be exfiltrated; the team's IP is stolen. The fix is to enable encryption at rest; configure the KMS keys.
</details>

<details><summary>11. What is the most important research infrastructure metric?</summary>
The notebook availability rate. The metric tells the team whether JupyterHub is available. A low availability rate indicates a JupyterHub issue.
</details>

<details><summary>12. What is the relationship between research infrastructure and the consulting method?</summary>
The research infrastructure system design is the blueprint that the consulting method delivers. The consulting method uses the system design to scope the deal; the consulting method validates the system design through the POC.
</details>

<details><summary>13. What is the most common JupyterHub failure?</summary>
The notebook server fails to start. The user's image is missing; the user's kernel is unavailable. The fix is to verify the image; verify the kernel; restart the notebook server.
</details>

<details><summary>14. What is the most expensive JupyterHub mistake?</summary>
Using a notebook image that is too large. The notebook takes minutes to start; the data scientist is blocked. The fix is to use a smaller notebook image; prebuild the kernel.
</details>

<details><summary>15. What is the relationship between research infrastructure and the FinOps dashboard?</summary>
The research infrastructure drives the FinOps dashboard. The dashboard shows the cost per research project; the system design drives the cost. Together, they inform the cost-vs-quality trade-off.
</details>

<details><summary>16. What is the most common MLflow failure?</summary>
The MLflow database is down. The experiment tracking is lost; the team cannot log experiments. The fix is to restore the database from the backup; verify the database connection.
</details>

<details><summary>17. What is the relationship between research infrastructure and the MLOps stack?</summary>
The research infrastructure is the upstream layer; the MLOps stack is the downstream layer. The research infrastructure produces the experiments; the MLOps stack tracks the experiments.
</details>

<details><summary>18. What is the most expensive DVC mistake?</summary>
Storing the dataset files in Git instead of in object storage. The Git repository becomes too large; the Git operations become slow. The fix is to use DVC to store the files in object storage and the metadata in Git.
</details>

<details><summary>19. What is the most common FAIR data failure?</summary>
The dataset does not have a license. The dataset cannot be reused; the dataset cannot be shared. The fix is to add a license metadata to the dataset; document the license in the DVC metadata.
</details>

<details><summary>20. Why is the research infrastructure system design a Tier 2 chapter?</summary>
Because the research infrastructure system design is the foundation of the data science layer. The system design is what the platform team references; the system design is what the data scientist uses; the system design is the foundation of the data science workflow.
</details>

---

## Sources and review notes

- NVIDIA Zero-to-Hero Volume 23 (`chapter-12-system-design-research-infrastructure.md`). Source for the research infrastructure system design patterns. The wording has been rewritten in the handbook's voice.
- NVIDIA Zero-to-Hero Volume 8. Source for the system design patterns.
- Part 16 (MLOps) for the platform stack patterns.

### Cross-references to other handbook chapters

- Chapter 16.2 for the data versioning and experiment tracking.
- Chapter 16.3 for the data pipelines and feature stores.
- Chapter 19.10 for the customer workshops.

### Migrated from `nvidia-devops`

The research infrastructure system design operational patterns draw on Volume 23 and the gem-book corpora. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The JupyterHub configuration is a starting point; specific configurations depend on the team's needs.
- The MLflow backend is a starting point; specific backends depend on the deployment.
- The DVC configuration is a starting point; specific configurations depend on the storage.

### Not verified on live hardware

- The lab in Section 6 is **untested** against a live cluster in this repository.
- The JupyterHub deployment assumes a working Kubernetes cluster.
- The MLflow deployment assumes a working database.
