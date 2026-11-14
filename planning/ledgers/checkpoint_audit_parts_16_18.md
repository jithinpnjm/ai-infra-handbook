# Checkpoint audit: Parts 16-18 (rule 10)

Scope: 760 checkpoints in 38 chapters (docs/part-16-mlops-llmops, docs/part-17-operations, docs/part-18-security). Read-only audit; no docs/ files were edited.

Classes: **OK** scenario-style, 2-5 sentence answer supported by the chapter. **RECALL** bare definition, lookup or 'what does X do' with no scenario. **SHORT** answer is one sentence. **LONG** answer is over five sentences. **UNSUPPORTED** answer claims something the chapter does not say.

Method: sentence counts from a regex splitter (max found = 5, so LONG = 0). RECALL is a judgement on question wording, with answers of two sentences or fewer used as the trigger. UNSUPPORTED was checked by grep for every cited number, named source book, tool name and cross-reference (about 105 claims plus about 40 spot checks). Those all appeared in the chapter except one attribution. Conceptual sentences were not verified line by line, so OK is 'no problem found', not 'verified'.

## Summary per chapter

| Part | Chapter | Total | OK | RECALL | SHORT | LONG | UNSUPPORTED | Non-OK |
|---|---|---|---|---|---|---|---|---|
| 16 | 01-mlops-foundations-and-lifecycle.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 02-data-versioning-and-experiment-tracking-dvc-mlflow-weights-and-biases.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 03-data-pipelines-and-feature-stores.md | 20 | 19 | 0 | 0 | 0 | 1 | 1 |
| 16 | 04-pipeline-orchestration-kubeflow-pipelines-argo-flyte-airflow.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 05-distributed-compute-for-ml-ray-kuberay-training-operator-and-katib.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 06-model-registry-ci-cd-and-gitops-for-models.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 07-model-serving-platforms-kserve-seldon-and-bentoml.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 08-llmops-rag-vector-databases-and-agents.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 09-llm-evaluation-and-guardrails.md | 20 | 19 | 1 | 0 | 0 | 0 | 1 |
| 16 | 10-monitoring-drift-and-continual-learning.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 11-cloud-mlops-platforms-vertex-ai-sagemaker-and-azure-ml.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 12-nvidia-enterprise-stack-ai-enterprise-ngc-and-licensing.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 13-governance-privacy-and-compliance-for-ml-platforms.md | 20 | 19 | 1 | 0 | 0 | 0 | 1 |
| 16 | 14-platform-design-multi-tenant-ai-factory-quotas-and-chargeback.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 16 | 15-lab-end-to-end-mlops-on-gke.md | 20 | 19 | 1 | 0 | 0 | 0 | 1 |
| 17 | 01-observability-foundations-metrics-logs-and-traces.md | 20 | 19 | 1 | 0 | 0 | 0 | 1 |
| 17 | 02-prometheus-and-grafana.md | 20 | 18 | 2 | 0 | 0 | 0 | 2 |
| 17 | 03-logging-with-loki-and-tracing-with-opentelemetry.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 04-dcgm-exporter-and-interpreting-gpu-metrics.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 05-distributed-observability-and-profiling.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 06-alerting-slos-and-health-checks-for-gpu-clusters.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 07-failure-modes-and-detection.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 08-performance-engineering-methodology-and-decision-trees.md | 20 | 19 | 1 | 0 | 0 | 0 | 1 |
| 17 | 09-the-ai-systems-performance-checklist-master.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 10-cluster-lifecycle-upgrades-and-change-management.md | 20 | 17 | 3 | 0 | 0 | 0 | 3 |
| 17 | 11-incident-response-and-game-days.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 12-capacity-planning-and-cost-optimisation.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 13-reliability-engineering-for-ai-infrastructure.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 14-disaster-recovery-and-data-resilience.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 17 | 15-on-call-runbooks.md | 20 | 19 | 1 | 0 | 0 | 0 | 1 |
| 17 | 16-ai-assisted-operations-and-scaling-toward-very-large-clusters.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 18 | 01-threat-modeling-for-ai-infrastructure.md | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| 18 | 02-hardware-and-firmware-trust.md | 20 | 15 | 3 | 2 | 0 | 0 | 5 |
| 18 | 03-containers-and-the-software-supply-chain.md | 20 | 19 | 1 | 0 | 0 | 0 | 1 |
| 18 | 04-kubernetes-access-control-and-pod-security.md | 20 | 12 | 5 | 3 | 0 | 0 | 8 |
| 18 | 05-gpu-sharing-security-dma-iommu-and-sr-iov.md | 20 | 19 | 1 | 0 | 0 | 0 | 1 |
| 18 | 06-bluefield-doca-and-confidential-computing.md | 20 | 15 | 4 | 1 | 0 | 0 | 5 |
| 18 | 07-data-and-model-protection-audit-and-compliance.md | 20 | 9 | 8 | 3 | 0 | 0 | 11 |

## Totals by part

| Part | Total | OK | RECALL | SHORT | LONG | UNSUPPORTED | Non-OK |
|---|---|---|---|---|---|---|---|
| 16 | 300 | 296 | 3 | 0 | 0 | 1 | 4 |
| 17 | 320 | 312 | 8 | 0 | 0 | 0 | 8 |
| 18 | 140 | 109 | 22 | 9 | 0 | 0 | 31 |
| All | 760 | 717 | 33 | 9 | 0 | 1 | 43 |

Note: a RECALL item that is also one sentence is counted under RECALL only, so SHORT counts only the one-sentence answers that are not already RECALL.

## Non-OK checkpoints

| Chapter file | # | Class | Question | Scenario-style version (proposal only) |
|---|---|---|---|---|
| 03-data-pipelines-and-feature-stores.md | 16 | UNSUPPORTED | A CSV file with 17,654 rows and 10 columns takes 14 MB, and the same data as Parquet takes 6 MB. How much smaller is Parquet, and what is the downside? | Ask the reader to compute the Parquet saving from the chapter's own 14 MB vs 6 MB example and state why 6x is a best case, not the expected result. |
| 09-llm-evaluation-and-guardrails.md | 11 | RECALL | Why does the chapter recommend a dead man's switch for monitoring? | Give a silent overnight alerting failure and ask which dead man's switch signal reveals it and how on-call responds. |
| 13-governance-privacy-and-compliance-for-ml-platforms.md | 15 | RECALL | Why would you publish the differential privacy budget on the model card, and which numbers make it up? | Given a deployed model's noise scale, batch size and step count, ask the reader to derive epsilon and delta or decide what to publish. |
| 15-lab-end-to-end-mlops-on-gke.md | 9 | RECALL | Why does `dvc add` plus a Git commit make the dataset part of your code history? | Give a dataset file that changed in the bucket after its commit and ask which hash mismatch reveals it and what to do. |
| 01-observability-foundations-metrics-logs-and-traces.md | 14 | RECALL | Should you rely on a service mesh to give you complete traces? | Give a trace that breaks at one hop after a service mesh is added and ask which header and app change restores it. |
| 02-prometheus-and-grafana.md | 7 | RECALL | Why do applications never need to know anything about the metrics system behind Prometheus? | Give a new service that must expose metrics and ask what endpoint and format it needs and what the server does. |
| 02-prometheus-and-grafana.md | 8 | RECALL | Why does a dead man's switch alert exist, and how does it work? | Give a Prometheus host that dies overnight with a blank dashboard and ask which alert still reaches on-call and how you confirm it works. |
| 08-performance-engineering-methodology-and-decision-trees.md | 7 | RECALL | Why does the ridge point decide whether a kernel is memory-bound or compute-bound? | Give a kernel's arithmetic intensity against the ridge and ask the reader to classify it and pick the matching fix. |
| 10-cluster-lifecycle-upgrades-and-change-management.md | 9 | RECALL | Which pass conditions must a canary meet before the next stage? | Give a canary bus-bandwidth result 3 percent below baseline and ask whether it clears the gate and which conditions apply. |
| 10-cluster-lifecycle-upgrades-and-change-management.md | 14 | RECALL | How do you pause the driver upgrade, and what happens to nodes already done? | Give an upgrade that is 40 percent done and must stop, and ask which setting to change and what to check on the unfinished nodes. |
| 10-cluster-lifecycle-upgrades-and-change-management.md | 20 | RECALL | Why can a peer review not be replaced by automated tests, and in what order does a change move? | Give a change that skipped peer review and the rollback test, and ask at which stage each gap would have been caught. |
| 15-on-call-runbooks.md | 11 | RECALL | Why does the chapter recommend a dead man's switch alert? | Give a week with no pages and ask whether the silence is good news and which check proves the alert path still works. |
| 02-hardware-and-firmware-trust.md | 2 | RECALL | Secure Boot blocks unsigned code. Why do you also want measured boot? | Give a node that boots with Secure Boot on but an unexpected bootloader and ask whether measured boot evidence would show it and what the verifier compares. |
| 02-hardware-and-firmware-trust.md | 3 | RECALL | Why does a remote verifier send a nonce when it asks for a quote? | Give an attacker replaying an old healthy-node quote and ask how the nonce defeats it and what the verifier must reject. |
| 02-hardware-and-firmware-trust.md | 6 | RECALL | What does SPDM let one component do to another? | Give a failed GPU attestation and ask which Redfish field identifies the failing component and why. |
| 02-hardware-and-firmware-trust.md | 17 | SHORT | A fleet has 300 nodes and a 10 percent canary. How many are left for the full rollout? | Add a second ring (e.g. 20 nodes) and a budget so the reader must size each ring from the fleet, not one subtraction. |
| 02-hardware-and-firmware-trust.md | 20 | SHORT | After a clean firmware install, latency rises. What do you do, in order? | Add a version and time budget so the reader must choose which stage to halt and which to roll back. |
| 03-containers-and-the-software-supply-chain.md | 9 | RECALL | Why does keyless signing remove the key file problem, and what do you check before you depend on it? | Give CI runners behind an egress proxy that cannot reach the signing service and ask whether keyless signing can run and which check fails first. |
| 04-kubernetes-access-control-and-pod-security.md | 7 | SHORT | A user is allowed to create pods but not to read secrets. Why is that not enough? | Give a developer with pod-create rights in a tenant namespace and ask which Secrets and ServiceAccount tokens they can reach and the minimal Role fix. |
| 04-kubernetes-access-control-and-pod-security.md | 9 | RECALL | Why does a namespace alone not isolate a tenant's network traffic? | Give pods in two tenant namespaces that still reach each other after default-deny in one, and ask which policy is missing and in what order to add it. |
| 04-kubernetes-access-control-and-pod-security.md | 10 | RECALL | Why does a ValidatingAdmissionPolicy do nothing on its own? | Give a ValidatingAdmissionPolicy with no effect in a tenant namespace and ask which binding is missing and what Pod Security still enforces. |
| 04-kubernetes-access-control-and-pod-security.md | 11 | RECALL | Why must a device plugin run privileged? | Give a device plugin refused in a Restricted namespace and ask which label fixes it and what that label exposes. |
| 04-kubernetes-access-control-and-pod-security.md | 14 | RECALL | Why is a ClusterRoleBinding for namespace users a problem? | Give users who gain access in other teams' namespaces after a binding change and ask which binding type caused it and the RoleBinding fix. |
| 04-kubernetes-access-control-and-pod-security.md | 15 | RECALL | Why is Workload Identity safer than a copied key? | Give a copied service-account key found in a repo and ask for the rotation and Workload Identity migration steps in order. |
| 04-kubernetes-access-control-and-pod-security.md | 18 | SHORT | A tenant role includes list on secrets. What does that expose? | Give a shared namespace with a tenant role that has list on secrets and ask what a stolen token can read and the minimal role. |
| 04-kubernetes-access-control-and-pod-security.md | 19 | SHORT | A training pod cannot reach its bucket. What do you check? | Give a training pod that cannot reach its bucket after a ServiceAccount change and ask for the checks across token, annotation and IAM role in order. |
| 05-gpu-sharing-security-dma-iommu-and-sr-iov.md | 11 | RECALL | Why do ordinary vGPU profiles not give the same isolation as MIG-backed vGPU? | Give a tenant worried about noisy neighbours on a vGPU and ask which profile to choose and why, from the isolation model. |
| 06-bluefield-doca-and-confidential-computing.md | 6 | SHORT | A team uses MIG instances for confidential tenants. What is wrong? | Give a MIG-backed confidential tenant on a shared host and ask whether it is allowed and what configuration replaces it. |
| 06-bluefield-doca-and-confidential-computing.md | 7 | RECALL | Why is a baseline network card outside the trusted boundary even when it supports attestation? | Give a tenant whose RDMA traffic uses an attestation-capable NIC and ask whether the workload must encrypt payloads and why. |
| 06-bluefield-doca-and-confidential-computing.md | 9 | RECALL | What does zero-trust mode on a BlueField DPU restrict, and what does it not do? | Give an admin who needs host access to the BlueField during an incident and ask whether zero-trust mode allows it and what stays unprotected. |
| 06-bluefield-doca-and-confidential-computing.md | 10 | RECALL | How do you check that a BlueField's secure boot is anchored? | Give a reimaged BlueField that must prove secure boot is anchored and ask for the ordered checks and what a passing result looks like. |
| 06-bluefield-doca-and-confidential-computing.md | 15 | RECALL | Which GPUs and CPUs does NVIDIA support for confidential VMs? | Give a customer wanting confidential VMs on an older CPU generation and ask whether that pairing is supported. |
| 07-data-and-model-protection-audit-and-compliance.md | 2 | RECALL | What does safetensors remove, and what does it leave open? | Give a team converting a pickle checkpoint to safetensors and ask which risks remain and which provenance check is still needed. |
| 07-data-and-model-protection-audit-and-compliance.md | 7 | RECALL | Why prefer KMS v2 over v1 for Kubernetes envelope encryption? | Give a cluster still on KMS v1 at a given Kubernetes version and ask the migration steps and what changes in key handling. |
| 07-data-and-model-protection-audit-and-compliance.md | 8 | RECALL | What is envelope encryption, in one sentence? | Give an auditor asking how a stored Secret is protected and ask the reader to trace data key and key encryption key. |
| 07-data-and-model-protection-audit-and-compliance.md | 9 | RECALL | Why is a key stored next to the encrypted data a problem? | Give a backup job that copies the encryption key beside the data and ask the exposure and the key-management fix. |
| 07-data-and-model-protection-audit-and-compliance.md | 10 | RECALL | Why can a NetworkPolicy not give you TLS 1.3? | Give a team asking a NetworkPolicy to enforce TLS 1.3 and ask which layer must enforce it and where the policy boundary sits. |
| 07-data-and-model-protection-audit-and-compliance.md | 12 | RECALL | Why is locking a retention policy a decision to make carefully? | Give a 7-year retention lock request and ask whether to lock now or lengthen first, with the irreversibility consequences. |
| 07-data-and-model-protection-audit-and-compliance.md | 14 | RECALL | Why is O_EXCL used when writing each audit entry file? | Give an audit writer that overwrites an existing entry and ask which error O_EXCL raises and what the writer must do next. |
| 07-data-and-model-protection-audit-and-compliance.md | 15 | SHORT | A regulator asks which data trained the model that decided on a customer. What do you need ready? | Give a specific customer decision under regulator query and ask for the ordered record list and the tested query. |
| 07-data-and-model-protection-audit-and-compliance.md | 16 | SHORT | A retention period of 90 days is set on an entry written on 1 November. When can it first be deleted? | Add a legal hold that extends the retention and ask for the new earliest deletion date and the reason. |
| 07-data-and-model-protection-audit-and-compliance.md | 19 | RECALL | Signing events appear in a transparency log. Who notices an unexpected one? | Give a transparency-log event the team did not create and ask the response and the monitoring that would have caught it earlier. |
| 07-data-and-model-protection-audit-and-compliance.md | 20 | SHORT | Audit logs show a read of the weights by an unknown principal. What do you do, in order? | Give a time-ordered set of log extracts for an unknown principal and ask the reader to triage them in sequence. |
