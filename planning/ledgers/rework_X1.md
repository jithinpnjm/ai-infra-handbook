# Rework ledger X1 (18.5, 18.6, 18.2, 18.7, 18.4)

All five chapters rebuilt from the Opus section 5 instruction. Front matter and metadata tables kept; 20 checkpoint questions each (rewritten as scenarios). Gates: chain_gate 0.0 for all five, summary count 20, check_code_files part18 0 problems, test_part18 18 passed, no language_audit row, no raw angle brackets or braces in prose, no exclamation marks.

## 18.5 (FA's cost fix kept: 400-1,600 GPUs, 1.2k-8k dollars an hour; cost arithmetic checkpoints carried over)
Rebuilt as a threat table (5 threats to controls), opening on CVE-2024-0132. Old mermaid replaced because it encoded the wrong DMA model.
- Cross-tenant read via DMA stopped by IOMMU: fixed. IOMMU protects host memory from devices (kernel VFIO doc); GPU processes are separated by per-context address space (CUDA programming guide) or MIG.
- Time-slicing "no memory isolation": fixed. Device plugin README: shared memory, same fault domain, no claim that data is read.
- Non-MIG vGPU called spatial: fixed. vGPU docs: time-sliced or MIG-backed; best effort, equal share, fixed share.
- `nvidia-smi -vgpu 1`, perf iommu events, `/sys/class/iommu` listing, `mig -cgi 0..6`, "IOMMU logs DMA", `gpusharing.*` roles, memory.used anomaly alert: removed (unsourced). `sriov-manage`, `mig -lgip`, `-L` now cited.
- Time-slicing interval/timeout: fixed; code/part18/timeslicing.yaml rewritten to `sharing.timeSlicing.resources[].replicas` (README).
- Added CVE-2024-0132 (bulletin 5582) and CVE-2025-23266 (bulletin 5659) with fixed versions, LeftoverLocals, CC limits.
Unresolved: no NVIDIA source on zeroing freed GPU memory outside CC mode (chapter says so); exact CDI conditions of CVE-2025-23266 deferred to the bulletin; a Trend Micro report of an incomplete CVE-2024-0132 fix (CVE-2025-23359) seen only in secondary results, not included.

## 18.6
Rewritten on NVIDIA CC docs (modalities, threat models, attestation flow, ready state, limits, ~4 GB/s CPU-GPU figure from the H100 blog) plus BlueField zero-trust mode and secure boot (BSP 4.8 and 4.5.2 pages).
- `nvidia-smi --query-gpu=cc_mode`: removed; real commands `nvidia-smi conf-compute -f`, `-srs 1`; mode set on host with gpu-admin-tools (not possible with host Secure Boot).
- "GPU CC encrypts GPU memory": fixed (access controls; HBM not encrypted).
- `doca_service list`, tpm2_pytss verifier, `highassurance.*` roles, BlueField core/memory figures, TPM-DPU-CVM-GPU chain: removed, no source.
Unresolved: the 4 GB/s figure is H100-era; no vendor doc for a TPM-to-DPU chain.

## 18.2
Rebuilt around Secure Boot vs measured boot, TPM quote with nonce (tpm2-tools, Redfish ComponentIntegrity), SPDM, BMC trust (CVE-2024-54085: NVD published 2025-03-11, CISA KEV 2025-06-25), firmware inventory, staged updates.
Removed: `nvidia-smi -q | grep attestation`, `nv-switch-cli`, `ipmitool raw 0x30 0x0e` and `attestation verify`, tpm2_pytss snippet, vendor key table, `firmware.*` roles. Repo fw_* scripts kept as local simulation; their versions are simulation values (noted in chapter).
Unresolved: no vendor command for a GPU attestation report outside CC mode; CVE-2024-54085 affected range differs across trackers.

## 18.7
Rebuilt around model weights: pickle vs safetensors, `torch.load` weights_only, model_signing, KMS and envelope encryption, Kubernetes Secrets at rest (KMS v1 deprecated 1.28, disabled 1.29, v2 stable 1.29), GCS Data Access logs, Bucket Lock, audit log (code block equal to audit_log.py), lineage.
Removed: torchmark watermarking, `gcloud kms keys rotate` (not a command), DLP/public-access conflation, `gsutil encryption set` (replaced by `gcloud storage buckets update --default-encryption-key`), `dataprotection.*` roles, bq queries.
Unresolved: Cloud KMS rotation flags left to current docs; no legal summaries.

## 18.4
Removed off-topic webhook and Gatekeeper sections (old 3.4 to 3.7; the Ingress example used removed v1beta1). Added RBAC escalation table (RBAC good practices), GPU Pod Security (device plugin privileged per Kubernetes docs; GPU Operator namespace privileged per NVIDIA docs), two-namespace pattern. All yaml blocks unchanged and equal to code/part18. Removed `rbac.*` roles and SLO tables.
Unresolved: ExternalSecret v1beta1 served version; hostPath /dev risk not separately sourced (covered through the PersistentVolume hostPath doc).

## Neighbours
- 18.1 and 18.3 not read. Snippets model_watermark.py, attestation_verifier.py, tpm_attestation.py in code/part18 are now unreferenced by chapters.
- 11.21 to 11.26 should be checked for the same time-slicing field mistakes.
