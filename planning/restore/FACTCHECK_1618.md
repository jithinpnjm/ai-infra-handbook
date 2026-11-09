# Fact-check list from voice-rewrite agents (Parts 16-18). Verify each against upstream source, then fix or delete.

## 16.11
- Vertex AI Pipelines/Endpoints said to "run on GKE" (Google-managed)
- Vector Search index called "proprietary" (ScaNN-based)
- Model Registry "Postgres-like" backing store; Prometheus exporter names; `gcloud ai pipelines run` flags

## 16.4
- Argo metadata in Postgres (1.2, 1.6, 5.1); Argo "pod-level cache" and Airflow "None (built-in)" in 1.6 table
- metric `workflow_last_progress` (checkpoint 10); "same NUMA domain" (2.2)
- `schedulerName: kueue` in 2.2 YAML  <-- Kueue is not a scheduler; likely wrong

## 17.11 / 16.14 / 18.3 (pilot): done except 17.11 "most common" checkpoint answers, 18.3 gcr.io lab registry

## 17.2
- 6.3 uses a `during` keyword in an alert rule; real keyword is `for:`  <-- fix
- 1.2 cAdvisor job path (kubelet /metrics/cadvisor); `regex: false` in drop rule looks invalid
- PromQL names gpu_utilization_ratio / gpu_memory_used_bytes vs DCGM_FI_DEV_GPU_UTIL in the lab
- recording rule gpu_pool:utilization:avg5m has no 5m window; checkpoint 18 "silent failure" overstated; lab embeds admin:admin

## 17.4
- GPU_UTIL is "share of time a kernel runs", not an SM fraction (s2.1)
- DBE "corrupt data" (s2.3, cp 12,13,19) vs ASP ch3: detected and raised, not silently corrupting
- s3.1 `rate(...) > 100` is per second, not per hour; s6.6 nvidia-smi -q -d ECC only reads; s2.1 PromQL `sum by (team) ... by (gpu, team)` invalid; NVLink row duplicated in 1.3 table; $3-5/hour GPU cost unsourced

## 16.10
- text block "10-50 metrics per model" unsourced; table 3.3 "holdout" definition wrong; 4.2 datetime.utcnow deprecated; DMLS/Practical MLOps attributions unverified

## 17.3
- trace context "to the GPU kernel" (s1 text/bold, s2.4): traceparent travels in HTTP headers between services
- s2.2 YAML: metrics pipeline exports to Tempo (trace backend); s3.3 PromQL block invalid
- cp 8 "Loki indexes log lines" (indexes labels); cp 15 Collector "per cluster" vs DaemonSet; unsourced "Loki cheaper", loki-stack retention_period

## 17.1
- Alertmanager arrows in diagram; RED/USE/golden-signal attributions; flag --storage.tsdb.max-label-values-per-label-name; "GPU kernel" tracing (3.4); exercise 5 count query does not measure cardinality

## 16.7
- 6.1: "70B model with 80 GB weights" (FP16 70B is ~140 GB); 6.5 heading "deadlock" is really a backlog cascade; 6.6 panic window; 5.2 egress prose vs YAML; 7.6 kubectl get hpa vs Knative; 4.2 Seldon YAML structure; cp 15 "regulator review"

## 16.8 (agent corrected 4.3 arithmetic: $0.054 x 1000 QPS x 3600 = $194,400/hour -- verified OK)
- Milvus "IVF is the default", "HNSW most accurate", "HNSW in-memory only", "petabyte scale"; s5.1 "three components" lists five; Q7 freshness tolerances

## 16.9
- Prose calls safety/factuality filters LLM-as-judge / trained classifiers; code/part16 guardrails_*.py are rule-based stand-ins (mine) -> add a plain note that the files are stand-ins for the model-based filter described
- "expected_max_tokens" counts words in regression_eval.py; GKE 1.27 assumption

## 16.6
- 2.3 workflow: `cosign sign --key` vs OIDC text; `steps.train.outputs` never set; Argo CD/Flux credited to PK ch 11 (GitOps is ch 15); 4.1 "three patterns" lists four; blue/green "DNS swap" ignores caching; 5.2 IAM cannot check PR merge state

## 16.2
- 1.2 "any S3-compatible" (DVC also GCS); 3.1 "signed by the training image"; 3.2 Kyverno/Gatekeeper verify images not mounted weights; 7.3 `dvc metrics add` + appending to metrics.json; 7.6 `cosign sign` on .pkl should be sign-blob; 4.1 W&B "cloud only" vs W&B Server; 4.3 "Reproducibility 0/15, 15/15" unsupported

## 16.12
- question says six layers, diagram five; "every layer open source except support" vs NIM proprietary; "audited annually", "per GPU per year" unsourced; 7.5 CUDA mismatch blamed on data format / ResourceQuota cannot declare CUDA; cp16 RAPIDS pool; 7.3 OOMKilled is host memory; lab uses invented resources.gpu.type (see 3.1)

## 17.6
- lab step 4 POSTs to Prometheus admin TSDB API (does not fire alerts) -> use Alertmanager /api/v2/alerts; inhibit-rules ConfigMap likely never read; step 7 queries undefined cluster_availability_budget_remaining; `kubectl top pod` has no GPU memory; IAM role names invented

## 16.5
- Training Operator "no autoscale" (PyTorchJob has elasticPolicy); cp9 Kueue rejects vs 6.6 queued; Kueue called a gang scheduler; "36 node-hours" vs 64-GPU run; build_model/opt duplication in 3.2; deprecated MLflow stage API 4.3; Katib autoscaling row; KServe/Knative/RLlib claims 13-14

## 16.1
- lab 8.1 prose Postgres vs command sqlite; lab train.py column tier_gold vs dataset "tier"; lab 8.5 s3:// in GCS lab; lab 8.4 calls promote.py (exists now, check args); "MLflow/Vertex default monotonic" unsourced; 6.3 object storage "immutable by default" doubtful; exercises list has six items

## 17.5
- 6.2 "profile cardinality is storage cost"; 5.1 NCCL debug logging called "NCCL Profiler"; 7.3 `--sample` flag; 7.5 kernels "inlined"; 60-80%/20-40% time shares unsourced; 5.2 sample NCCL log lines unverified

## 16.13
- 5.3/cp10 l2_norm_clip, noise_multiplier are not the privacy budget (epsilon/delta); 1.3 canary as "human oversight"; 1.1/cp1,14 "satisfies GDPR/CCPA" overclaims; 3.3 versioning "makes record immutable"; 4.1 "weights are not personal data per se" (contested); EU AI Act "right to rectification"; "7% of turnover" unverified

## 16.15
- UCI Adult is not a churn dataset (s4); s3:// storageUri on GKE (s7); `kubectl argo rollouts` targets Rollouts not InferenceServices (s8); MLflow sqlite backend (s3); transition_model_version_stage deprecated; argo `--parameter-values` flag; "audit log" claim not produced by gate code

## 16.3
- 3.2 Great Expectations code mixes GX 1.x and 0.x APIs (won't run); 1.3 script reads Parquet as text; 2.3 Vertex "Bigtable" backend and 1.4 "~2x/~6x" unsourced; "most expensive mistake" claimed twice (Q10, Q11); code/part16/gx_suite.py needs same GX fix

## 17.13
- Chaos Mesh "older versions accepted scheduler field" (my own unverified addition -> removed); "1-3 latent failure modes", "10-100x cost", "99.9% monthly", 50/25/10% freeze thresholds in code blocks unsourced

## 17.12
- lab step 3 "6 (rounded up)" should be 7; chargeback SQL aliases (code file fixed); 6.3 80%-used commitment vs 30% discount contradiction; s13 cites AI Factory ch 8 (it is Software Engineering); admin:admin curl

## 17.9
- tables hold 207 items but score formula uses 175; `lfs iostat`, gsutil flags, NCCL_IB_TIMEOUT=600, node_exporter names unverified; clone URL placeholder; Sources overstates ASP appendix (no numbered yes/no items); agent read only ASP appendix (PK/AF not read)

## 18.1
- Q12-15, Q18 relationship claims; Engineering AI Systems / NVIDIA Volume citations unverified

## 17.8
- attention intensity (2045 FLOP/byte) counts one tensor, omits seq x seq, labels 4 bytes as FP16; decision-tree step 2 "No" branch; lab roofline hand-counted FLOPs; "FP8 doubles compute peak", H100 989 TFLOPS unverified; Gregg/RED attributions; admin:admin

## 17.10
- 4.2 `kubectl exec gpu-node-1` targets a Pod not a node; 7.2 GKE control-plane downgrade to 1.27 (GKE does not support); 1.3 blue/green "suitable for stateful"; 5.2 role names "not built-in"; 3.1 table Weekday/High vs Tue/Wed Medium; 7.6 says canary but commands apply directly

## 18.6
- DOCA expansion ("Data Center Infrastructure-on-a-Chip"?); Rivermax as packet capture; commands `doca_service list`, `nvidia-smi --query-gpu=cc_mode`, `--cc-mode=full`, `qemu -machine tdx-guest` likely wrong; `tpm2_pytss.verify` not a real API (4.2); chain order TPM->DPU->CVM->GPU unverified

## 17.15
- 7.7 curl to /api/v1/admin/tsdb "injects" an alert (cannot; use Alertmanager /api/v2/alerts); 3.2 handover 99.95% vs 38 min vs 99.9% math; Sources cite PK ch 14 (alerting is ch 9); 2.1 SLO-breach trigger no table row; Q18 "Tier 2" undefined

## 18.7
- "object-lock" is S3 term (GCS: retention policy/bucket lock); `gsutil pap set enforced` is public access prevention not DLP; audit log "signed/replicated" not in code (unsigned SHA-256); watermark "robust/unforgeable", "torchmark" unsourced; GKE 1.27+; audit_log.py docstring says named by hash, code uses timestamp+hash prefix

## 18.5
- time-slicing "strong memory isolation (overwritten)" (s4.2 table, cp5, cp15) -- time-slicing gives NO memory isolation; `nvidia-smi -vgpu 1`; perf stat IOMMU event names; A100 80GB MIG profile list; IOMMU credited with MIG isolation; time-slicing ConfigMap schema; `memory.used` as scraping detection; "cordon the workload" (nodes only); DMAR log text Intel-specific

## 18.2
- "keys are stored in the TPM" (1.2; UEFI key DBs live in firmware variables); ROM as a verified link; tpm2_pytss quote API and "workload reads the PCRs" (2.4); GPU endorsement key "in the fuse, unique per GPU"; `nv-switch-cli`, `ipmitool ... attestation verify` (3.2-3.3); firmware rollback "550.54.14" is a driver version; "scanned daily" vs "continuous" (Q17); unsourced "most common" Q6-9

## 17.16
- 5.2 one Kueue ClusterQueue across clusters needs MultiKueue; 5.1 KubeFed is archived; attributions "ASP Ch 20 anomaly detection", "LLMOps Ch 10 runbook generation" don't match books; lab steps 3,5,6 pass CLI flags the code does not define; cp18 doesn't answer tier question

## 18.4
- 5.1 "three types" lists four; ESO "rotates secrets automatically" (it syncs); 3.3 PSS sentences describe a custom ValidatingAdmissionPolicy; 4.3 "No policyTypes allows all traffic" doubtful; default-deny egress blocks DNS (silent); `vault write -force` on KV v2 needs `vault kv put`; "50-200 namespaces" unsourced

## 17.7
- 4.2/Q7 OOMKilled = container memory not GPU; 1.3/Q3 SM clock > 0 doesn't prove no hang; 2.3 `ansible all -m ping` not a partition detector; Q15 Linkerd has no Istio-style circuit breaker; 4.3 PromQL lacks `for: 5m`; 9.5 heading says simulate/inject but only reads ECC; diagram routes model serving to DCGM; `CUDA_OUT_OF_MEMORY` string, "Failed to verify signature" event text, blackbox-exporter partition detection unverified

## 17.14
- 3.1/8.2 `gsutil replication set ... --role` not a real command; 3.2 `lfsctl replication create` not a Lustre command; 4.1 `gsutil retention set` args reversed; 8.5 `kubectl cordon` does not move Pods (needs drain); 8.6 5-minute RPO "within" 1-minute target; Sources cite PK ch 14 for DR (none; use ch 2, 4)

---
# Resolution status (2026-11-08, fact-check pass 1)
FIXED: 17.4 SBE rate->increase (doc + gpu_alerts.yaml, promtool ok), -d ECC comment; 17.7 ansible ping wording, Linkerd; 17.3 GPU-kernel trace claims, Loki indexing; 17.2 `for:`; 17.10 GKE control-plane rollback; 17.14 gsutil/lfsctl/retention/cordon; 17.9 207 vs 175; 17.16 KubeFed->MultiKueue; 17.12 AF ch8 source note;
16.7 70B/80GB; 16.12 invented gpu.type; 16.2 cosign sign-blob, dvc metrics; 16.11 Vertex-on-GKE; 16.13 DP epsilon/delta; 16.3 GX 1.x code (tested in venv with great_expectations 1.24: good=True, bad=False);
18.5 time-slicing memory isolation; 18.4 secret types/ESO/vault kv put; 18.7 DLP/object-lock/torchmark; 18.6 DOCA name + illustrative commands; 18.2 TPM keys + illustrative commands; 49+ intro text blocks: source shorthand replaced by "background reading" with full book names and "figures are examples".
STILL OPEN (not verified, left as flagged): everything above not listed under FIXED, notably 17.5 NCCL log lines, 17.8 roofline arithmetic, 17.15 handover math, 16.4 Argo/Kueue claims, 16.5 Training Operator elasticPolicy, 16.8 Milvus index defaults, 16.9 chapter vs stand-in guardrail code, 16.10 holdout definition, 16.15 dataset/Argo Rollouts, 18.1 citations.
