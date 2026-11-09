# code/part18: what is tested and how

Run everything: `python3 code/part18/security_lab.py`.

| Kind | How it was checked |
|---|---|
| Measurement chain, firmware lifecycle, CVE correlation, threat catalogue, lineage, audit bucket | `pytest code/part18/test_part18.py`, with tamper and forgery cases |
| Core Kubernetes manifests (NetworkPolicy, RBAC, Deployment, admission policy, ...) | kubeconform, strict |
| Policy engines (Kyverno, Gatekeeper) | CRD schema check for Kyverno; Gatekeeper Rego not executed |
| `snippets/` (TPM attestation, watermarking) | Syntax only. Needs a TPM and libraries whose APIs were not verified. |

`establish_chain.py` models the extend-and-sign logic of a TPM quote with an HMAC key on disk. A real attestation key never leaves the TPM and real quotes use asymmetric signatures; this tests the chain logic, not TPM behaviour.
A NetworkPolicy cannot enforce a TLS version. That is set at the ingress or service mesh.
