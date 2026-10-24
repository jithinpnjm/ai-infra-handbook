---
id: "c05-16"
title: "5.16 Configuration, secrets and RBAC"
sidebar_label: "5.16 Configuration, secrets and RBAC"
sidebar_position: 16
description: "Managing configuration and secrets in Kubernetes (ConfigMaps, Secrets, projected volumes, immutability, rotation, external secret stores, encryption at rest) and access control (authentication, ServiceAccounts and tokens, RBAC roles, aggregation, least-privilege design, auditing) with AI-platform patterns"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 5.16 Configuration, secrets and RBAC

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | kind or kubeadm cluster; `kubectl auth can-i`, `rakkess`/`kubectl-who-can` optional; External Secrets Operator and Vault dev for the external store lab |
| Part | Part 5: Kubernetes |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

AI platforms accumulate sensitive material: object-store credentials for datasets and checkpoints, model hub tokens, API keys for LLM providers, registry credentials, database passwords for metadata stores, signing keys, and service tokens that operators use to reach the API. They also accumulate configuration: model parameters, tokenizer paths, NCCL environment, scheduler settings, feature flags. How you inject, rotate, and scope these decides whether a leaked notebook can read every team's checkpoints or a compromised job can create GPU pods without limit. RBAC is the authorisation layer for the Kubernetes API itself; a mistaken ClusterRoleBinding to `system:authenticated` or a broad `nodes/proxy` grant is a cluster-wide compromise. This chapter covers configuration objects, secret handling practices, and RBAC design.

## Prerequisites and outcomes

Needs 5.5 and 5.7. After this chapter you can:

- Use ConfigMaps and Secrets correctly (env vars, files, projected volumes, immutability, size limits, update propagation) and choose the injection method per use-case.
- Explain what Secrets really are (base64-encoded API objects in etcd), how to encrypt them at rest with KMS, restrict access with RBAC, and integrate external secret stores (External Secrets Operator, Secrets Store CSI, Vault Agent, SOPS/Sealed Secrets).
- Describe authentication methods (certificates, tokens, OIDC), ServiceAccounts with projected/bound tokens, and workload identity to cloud IAM.
- Design RBAC: Roles/ClusterRoles/bindings, verbs/resources/subresources, aggregation, default roles, least privilege patterns for multi-tenant AI platforms, and common escalation paths.
- Audit and test permissions (`can-i`, `auth whoami`, audit logs, RBAC reports, policy-as-code).
- Operate secrets and RBAC safely in GitOps pipelines.

## 1. ConfigMaps

A **ConfigMap** holds non-confidential configuration as key-value pairs (`data` for UTF-8, `binaryData` for bytes), up to ~1 MiB total (etcd/object limit). Create from literals, files or directories:

```bash
kubectl create configmap trainer-config --from-literal=LOG_LEVEL=info --from-file=hparams.yaml
kubectl create configmap nccl-env --from-env-file=nccl.env
```

Consumption patterns:

```yaml
spec:
  containers:
    - name: trainer
      envFrom:
        - configMapRef: { name: nccl-env }                   # all keys as env vars
      env:
        - name: LOG_LEVEL
          valueFrom: { configMapKeyRef: { name: trainer-config, key: LOG_LEVEL, optional: true } }
      volumeMounts:
        - { name: cfg, mountPath: /etc/trainer, readOnly: true }
  volumes:
    - name: cfg
      configMap:
        name: trainer-config
        items: [ { key: hparams.yaml, path: hparams.yaml, mode: 0444 } ]
        defaultMode: 0444
```

Semantics to know:

- **Environment variables** are resolved at container start; updating the ConfigMap does **not** change running processes. Names must be valid env var names; keys with dots/dashes can't be used with `envFrom` without remapping.
- **Volume mounts** are updated eventually (kubelet sync period + cache TTL, typically within ~1 to 2 minutes) via an atomic symlink swap of the `..data` directory. **`subPath` mounts do not receive updates**. Applications must re-read files (or be signalled) to pick up changes; config reloaders (e.g., sidecars, `reloader`, `kubectl rollout restart` triggered by a hash annotation) automate restarts: common GitOps pattern is to include a hash of the ConfigMap in the pod template annotations (Helm `checksum/config`, Kustomize `configMapGenerator` hashed names) so a config change rolls the Deployment.
- **Immutable ConfigMaps/Secrets** (`immutable: true`): cannot be changed, protect against accidental edits, and reduce API server load (kubelets stop watching them), valuable at scale; replace by creating a new name and rolling pods.
- **Size and structure**: don't store datasets, models or large JSON blobs; ConfigMaps are for small config. Keep per-job generated configs small; thousands of per-pod ConfigMaps create etcd and watch load.
- **Binary and multi-line**: use `binaryData` or `|` block scalars.
- **Downward API** (`fieldRef`/`resourceFieldRef`) exposes pod metadata and resource limits to the container (pod name, namespace, IP, node name, labels, CPU/memory limits) as env vars or files: useful for rank/ID derivation, NUMA/worker sizing.

## 2. Secrets

A **Secret** has the same shape as a ConfigMap (`data` base64-encoded, `stringData` write-only plain text) but is treated differently: kept in tmpfs on nodes when mounted, not written to disk by the kubelet, restricted by RBAC (separate `secrets` resource), and eligible for encryption at rest. Types: `Opaque`, `kubernetes.io/tls` (`tls.crt`/`tls.key`), `kubernetes.io/dockerconfigjson` (image pull), `kubernetes.io/basic-auth`, `kubernetes.io/ssh-auth`, `kubernetes.io/service-account-token` (legacy), `bootstrap.kubernetes.io/token`.

**Secrets are not encrypted by default.** Base64 is an encoding, not protection. Anyone with `get`/`list` on secrets (or `exec` into a pod mounting them, or read access to etcd or etcd backups, or `nodes/proxy`) can read them. The security model rests on:

1. **RBAC**: tight `secrets` permissions (avoid `list`/`watch` on all secrets: listing reveals contents; avoid wildcards).
2. **Encryption at rest** in etcd via the API server `EncryptionConfiguration` with a **KMS v2** provider (cloud KMS, Vault transit, etc.) for envelope encryption; `aescbc`/`secretbox` with local keys is weaker (key on disk of the control plane). Rotate keys; re-encrypt existing secrets (`kubectl get secrets -A -o json | kubectl replace -f -`). Verify: `etcdctl get /registry/secrets/ns/name` shows `k8s:enc:kms:v2:` prefix.
3. **Transport and node protection**: TLS between components; secrets are only sent to nodes that run pods needing them (Node authorizer); mounted on tmpfs; nodes are in the trust boundary.
4. **Minimising exposure**: prefer files over env vars (env vars appear in `/proc/<pid>/environ`, crash dumps, child processes, logs and runtime inspect output); set `defaultMode: 0400` and `readOnly: true`; use `fsGroup`; avoid logging; use `automountServiceAccountToken: false` where not needed.
5. **Short-lived credentials** over long-lived: workload identity, projected tokens, dynamic secrets from Vault.

```yaml
apiVersion: v1
kind: Secret
metadata: { name: hf-token, namespace: training }
type: Opaque
stringData: { token: "hf_xxx" }                 # example only; never commit real values to Git
immutable: true
---
spec:
  containers:
    - name: trainer
      volumeMounts: [ { name: hf, mountPath: /var/run/secrets/hf, readOnly: true } ]
      env: [ { name: HF_TOKEN_FILE, value: /var/run/secrets/hf/token } ]
  volumes:
    - name: hf
      secret: { secretName: hf-token, defaultMode: 0400 }
```

### Image pull secrets

`kubectl create secret docker-registry regcred --docker-server=... --docker-username=... --docker-password=...` produces `kubernetes.io/dockerconfigjson`; attach through `imagePullSecrets` on pods or the ServiceAccount (`kubectl patch serviceaccount default -p '{"imagePullSecrets":[{"name":"regcred"}]}'`). Better: node-level credential providers (kubelet image credential provider plugins for ECR/GCR/ACR) or workload identity so no long-lived password exists.

### GitOps-safe secret management

Never commit plaintext Secrets. Options (4.12, 4.26):

| Approach | How | Notes |
|---|---|---|
| **External Secrets Operator (ESO)** | `ExternalSecret`/`SecretStore` CRs reference Vault/AWS SM/GCP SM/Azure KV; ESO syncs into native Secrets | Secret values never in Git; native Secret still in etcd; refresh intervals handle rotation |
| **Secrets Store CSI Driver** + provider | Mounts secrets from a vault as a volume (and optionally syncs to a Secret) | Avoids etcd persistence when not syncing; per-pod volume; provider pods needed |
| **Vault Agent Injector / Vault Secrets Operator** | Sidecar/operator renders secrets into the pod via Vault Kubernetes auth | Dynamic secrets and leases |
| **Sealed Secrets** (Bitnami) | Encrypt to a cluster public key; controller decrypts to a Secret | Simple; cluster-bound key; rotate keys |
| **SOPS** (age/KMS) with Flux/Argo plugins | Encrypted YAML in Git, decrypted at apply | Reviewable diffs (keys visible) |
| **CSI/Workload Identity** | Pods authenticate to cloud APIs with federated tokens, no secret at all | Best for cloud resources |

### Rotation

Rotation requires consumers to reload: file mounts update automatically (kubelet refresh), apps must re-read; env-var-based secrets require pod restart (use a reloader controller keyed on secret hash, or `kubectl rollout restart`). Two-phase rotation (add new credential, switch consumers, remove old) for databases and tokens; automate with ESO refresh + Reloader, Vault dynamic leases, cert-manager for certs (5.12).

## 3. Projected volumes and ServiceAccount tokens

A **projected** volume combines several sources in one directory: `secret`, `configMap`, `downwardAPI`, `serviceAccountToken`, `clusterTrustBundle` (CA bundles).

```yaml
volumes:
  - name: creds
    projected:
      sources:
        - serviceAccountToken:
            path: sa-token
            audience: vault                 # token valid only for this audience
            expirationSeconds: 3600         # kubelet refreshes before expiry
        - configMap: { name: ca-bundle, items: [ { key: ca.crt, path: ca.crt } ] }
        - downwardAPI: { items: [ { path: labels, fieldRef: { fieldPath: metadata.labels } } ] }
```

### ServiceAccounts

Every namespace has a `default` ServiceAccount; pods use it unless `serviceAccountName` is set. Since 1.22+ pods receive a **bound ServiceAccount token** (a JWT signed by the API server, audience-bound to the API server, time-limited (default ~1 h, auto-refreshed), bound to the pod/node/secret object, invalidated when the pod is deleted) mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token` (via projected volume), replacing legacy never-expiring token Secrets (no longer auto-created since 1.24; create explicit `type: kubernetes.io/service-account-token` Secrets only when truly required, or use `kubectl create token <sa> --duration=...` for short-lived tokens). Best practices:

- One ServiceAccount per workload with **least-privilege RBAC**; never use `default` for anything privileged.
- `automountServiceAccountToken: false` on SA or pod if the workload does not call the API.
- Use **projected tokens with custom audiences** for external systems (Vault, cloud federation, SPIFFE-like identities, OIDC discovery) instead of passing long-lived keys.
- **Workload identity federation**: map Kubernetes ServiceAccounts to cloud IAM identities without keys: GKE Workload Identity, EKS IAM Roles for Service Accounts (IRSA) / Pod Identity, Azure Workload Identity; the cluster's OIDC issuer URL is registered with the cloud IAM, which trusts tokens for specific `namespace/serviceaccount` subjects; training pods then access buckets/registries with short-lived credentials (4.22, 5.34). For bare-metal clusters, expose the cluster's OIDC issuer (`--service-account-issuer`, `--service-account-jwks-uri`) and trust it from Vault/AWS/GCP.

## 4. Authentication

How the API server identifies callers (5.5): **client certificates** (CN = user, O = groups; used by kubelets, admin kubeconfig from kubeadm: avoid long-lived admin certs for humans), **bearer tokens** (ServiceAccount JWTs; static token files deprecated), **OIDC** (id_token from Dex/Keycloak/Okta/Entra; claims → username/groups via `--oidc-*` flags or the structured `AuthenticationConfiguration`), **webhook token authentication** (cloud IAM authenticators like `aws-iam-authenticator`, `gke-gcloud-auth-plugin`), **authenticating proxy** (front proxy headers; used by aggregated APIs), anonymous. Humans should authenticate through OIDC SSO with MFA and short-lived tokens (e.g., `kubelogin`/`kubectl oidc-login`, `kubectl --token`), mapped to groups used by RBAC. Machines use ServiceAccount tokens or federated workload identities. `kubectl auth whoami` shows the resolved identity.

## 5. RBAC

RBAC authorises requests by **verbs** on **resources** within **namespaces**. Four API objects:

| Object | Scope | Meaning |
|---|---|---|
| `Role` | Namespace | Set of allowed rules in that namespace |
| `ClusterRole` | Cluster | Rules for cluster-scoped resources (nodes, PVs, CRDs), non-resource URLs (`/healthz`, `/metrics`), or reusable across namespaces |
| `RoleBinding` | Namespace | Grants a Role or ClusterRole's permissions to subjects **within that namespace** |
| `ClusterRoleBinding` | Cluster | Grants a ClusterRole's permissions cluster-wide |

Subjects: `User`, `Group`, `ServiceAccount`. Rules: `apiGroups`, `resources` (with subresources like `pods/exec`, `pods/log`, `pods/eviction`, `nodes/proxy`, `deployments/scale`), `resourceNames` (restrict to specific objects), `verbs` (`get`, `list`, `watch`, `create`, `update`, `patch`, `delete`, `deletecollection`, plus special: `impersonate`, `bind`, `escalate`, `approve`, `sign`, `use`), `nonResourceURLs`.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: trainer-runner, namespace: team-a }
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["get", "list", "watch", "create", "delete"]
  - apiGroups: ["kubeflow.org"]
    resources: ["pytorchjobs"]
    verbs: ["*"]
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["trainer-config"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: team-a-researchers, namespace: team-a }
subjects:
  - { kind: Group, name: "oidc:team-a-researchers", apiGroup: rbac.authorization.k8s.io }
  - { kind: ServiceAccount, name: ci-runner, namespace: ci }
roleRef: { kind: Role, name: trainer-runner, apiGroup: rbac.authorization.k8s.io }
```

### Properties

- **Additive only**: no deny rules; permissions are the union of all bindings; a user with `edit` cannot be denied one verb except by removing the binding or using admission policy.
- **Bindings are immutable in `roleRef`**: to change the role referenced, delete and recreate the binding.
- **Default roles**: `cluster-admin` (everything), `admin` (namespace admin incl. RBAC within namespace), `edit` (read/write most objects, not roles/bindings; can read secrets, run pods → effectively access to namespace service account tokens), `view` (read most objects but not secrets), plus system roles (`system:node`, `system:kube-scheduler`, `system:discovery`, `system:public-info-viewer`, `system:basic-user`). **Aggregation**: ClusterRoles with `aggregationRule` collect rules from other ClusterRoles by label (`rbac.authorization.k8s.io/aggregate-to-edit: "true"`); CRD authors ship ClusterRoles labelled to extend `view/edit/admin` with their custom resources (e.g., Kueue, Argo).
- **Groups**: `system:authenticated`, `system:unauthenticated`, `system:serviceaccounts`, `system:serviceaccounts:<ns>`, `system:masters` (unrestricted, bypasses RBAC; avoid in certificates).
- **Escalation prevention**: you cannot create or update a Role/binding granting permissions you don't hold, unless you have the `escalate`/`bind` verbs on roles; `impersonate` allows acting as others; `create` on `pods` implies reading any Secret/ServiceAccount token in that namespace (by mounting) and potentially node access (hostPath, privileged): pod creation is a powerful permission; `create` on `pods/exec` equals shell in pods; `nodes/proxy` equals kubelet API access (exec on any pod on the node); `get` on `secrets` equals credentials; `create` on `serviceaccounts/token` mints tokens; `*` verbs/resources and `cluster-admin` bindings to groups like `system:authenticated` are never appropriate; `update` on `validatingwebhookconfigurations`/`mutatingwebhookconfigurations` or CRDs can disrupt the cluster; `get/list` on `secrets` cluster-wide is cluster compromise.

### Design patterns for AI platforms

1. **Namespace per team/project**; bind OIDC groups to `edit`/custom roles per namespace; no one except platform admins gets cluster-scoped write.
2. **Roles tailored to workflow**: `job-submitter` (create/delete Jobs/PyTorchJobs/LocalQueue workloads, read pods/logs/events, no secrets, no exec in prod), `notebook-user`, `inference-deployer` (Deployments/Services/HPA/InferenceService), `viewer` (view + metrics), `queue-admin` (Kueue ClusterQueue edits for team leads via ClusterRole + RoleBinding scoping).
3. **Operators and controllers** get the minimum cluster permissions they need (generate from kubebuilder markers, review them); separate service accounts per controller; use `resourceNames` where possible.
4. **CI/CD identities**: namespaced SAs or federated identities with permissions to apply only into their namespaces; no cluster-admin for pipelines; Argo CD/Flux projects restrict destinations (4.26).
5. **Break-glass**: time-bound elevated access via a controlled process (e.g., temporary RoleBinding by an access broker, `kubectl create token` for a break-glass SA, audit-logged), not permanent cluster-admin for humans.
6. **Separation of duties**: platform team owns CRDs, webhooks, policies, nodes; app teams own namespace content.
7. **Pod Security + admission policy complement RBAC**: RBAC says who can create pods; PSA/Kyverno/ValidatingAdmissionPolicy says what pods may look like (5.21).
8. **Read access for observability**: dedicated ClusterRole for Prometheus (`get/list/watch` on pods, nodes, endpoints, services; `/metrics` non-resource URL); avoid `nodes/proxy` where possible (use dedicated metrics endpoints or kubelet `/metrics` with `nodes/metrics` only).
9. **Multi-tenant inference platforms**: end users don't get Kubernetes RBAC at all; they call an API gateway with API keys/JWTs (5.12); Kubernetes RBAC is for engineers and automation.
10. **Documentation and review**: store RBAC as code with owners (CODEOWNERS), diff/review changes, run regularly an access review (`kubectl-who-can`, `rbac-tool`, `rakkess`, `kubectl auth can-i --list`, `rbac-lookup`, KubiScan, Kubescape/Polaris/Trivy RBAC checks).

### Testing and auditing RBAC

```bash
kubectl auth can-i create pods -n team-a --as=jane@example.com
kubectl auth can-i '*' '*' --as=system:serviceaccount:ci:ci-runner            # should be no
kubectl auth can-i --list -n team-a --as=system:serviceaccount:team-a:trainer
kubectl auth whoami
kubectl get clusterrolebinding -o json | jq -r '.items[] | select(.subjects[]?.name=="system:authenticated") | .metadata.name'
kubectl get clusterrolebindings,rolebindings -A -o wide | grep -E 'cluster-admin|system:masters'
kubectl who-can get secrets -n team-a            # krew plugin: kubectl-who-can
rbac-tool viz / rbac-tool lookup jane@example.com / rakkess --as jane
```

Audit logging (5.5) records `authorization.k8s.io/decision` and reasons; alert on `create` of ClusterRoleBindings, `exec` into production pods, secret reads by unusual identities, and token creation.

## 6. Configuration management patterns for AI workloads

- **Hierarchy**: image defaults < ConfigMap (cluster/env-level) < per-job overrides (env/args) < secrets (credentials). Keep model hyperparameters in versioned config files (Git, MLflow/W&B) rather than ad-hoc env vars; mount at read-only paths.
- **Generated configs**: operators (Training Operator, MPI Operator) write hostfiles and env; avoid per-pod ConfigMaps at scale; if needed use `immutable` and TTL cleanup (Job `ttlSecondsAfterFinished` cleans pods, but owned ConfigMaps need ownerReferences).
- **Feature flags and rollout**: ConfigMap-driven flags with hash-triggered rollouts; keep in GitOps.
- **Large artefacts**: model weights/tokenizers via PVC/object storage/OCI image volumes, not ConfigMaps.
- **Environment promotion**: Kustomize overlays/Helm values per environment; secrets via ESO references that differ per environment while manifests stay identical.
- **Validation**: schema-validate config (JSON Schema, pydantic in the app), `kubeconform` for manifests (4.13), startup self-checks failing fast with clear messages.
- **Namespaced defaults**: `LimitRange`, `ResourceQuota`, default `PriorityClass`, default `StorageClass` mean config choices are partly platform-provided (5.22).

## 7. Failure modes and troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Pod `CreateContainerConfigError` | Referenced ConfigMap/Secret/key missing | `describe pod`, create object, mark `optional` if appropriate |
| Config change not applied | Env var snapshot; `subPath`; app doesn't reload; kubelet sync delay | Rolling restart with hash annotation; avoid subPath; reload signal |
| `forbidden: User cannot list resource ... in API group` | Missing RBAC | `auth can-i`, add minimal rule; check subresource and group names |
| Operator can't reconcile after upgrade | New RBAC rules in new version not applied (Helm CRD/RBAC drift) | Update ClusterRole from chart; review diffs |
| Secret visible in logs/describe | Printed by app; env dumped | Mount as file, fix logging, rotate |
| Image pull `unauthorized` | Missing/expired pull secret | Check SA `imagePullSecrets`, credential provider, token expiry |
| `Unauthorized` (401) for kubectl | Expired OIDC token / cert / wrong context | Re-login, check `kubectl config view`, clock skew |
| Webhooks/SA tokens fail after clock skew or key rotation | JWT signing key changed, issuer mismatch | Keep issuer/keys stable; roll consumers |
| ServiceAccount token missing | Auto-mount disabled / token Secret not created (≥1.24) | Use projected token; `kubectl create token` |
| Overbroad access discovered | Wildcards, `edit` with secrets, exec rights | Tighten roles, remove bindings, rotate secrets |
| etcd compromised concern | Plaintext secrets in etcd/backups | Enable KMS encryption, rotate secrets, secure backups |

## 8. Lab (untested)

1. **ConfigMap propagation**: mount a ConfigMap as env, as volume, and with `subPath`; change it and measure which update and how long; use `immutable` and a hashed-name generator to roll deployments.
2. **Secrets reality check**: create a Secret, read it with `kubectl get -o yaml | base64 -d`, read it from etcd with `etcdctl` (plaintext); enable `EncryptionConfiguration` with a local `aescbc` key (lab) or a KMS plugin; verify `k8s:enc:` prefix; re-encrypt existing secrets.
3. **Exposure paths**: show a Secret read via env var in `/proc/1/environ`, via `kubectl exec`, via `pods/exec` permission, and via the node (`/var/lib/kubelet/pods/*/volumes`); decide mitigations.
4. **External secrets**: deploy Vault dev and External Secrets Operator; sync a Vault KV into a Secret; rotate in Vault and observe the refresh and consumer reload (Reloader); try the Secrets Store CSI driver as an alternative.
5. **Sealed Secrets / SOPS**: encrypt a Secret for Git with Sealed Secrets or SOPS+age; deploy via GitOps; verify the plaintext never appears in Git or logs.
6. **ServiceAccount tokens**: inspect a pod's projected token (decode JWT claims: `aud`, `exp`, `kubernetes.io`); create a token with a custom audience; call the API with it; delete the pod and show invalidation; show `automountServiceAccountToken: false`.
7. **Workload identity**: configure the cluster OIDC issuer and trust it from a cloud/Vault; have a pod obtain short-lived cloud credentials without secrets; verify bucket access and revocation by removing the binding.
8. **RBAC from scratch**: create a `job-submitter` Role and bind to a test user/group using certificates or impersonation; verify `can-i` for allowed and denied actions; add aggregation via a labelled ClusterRole to extend `view` with a CRD.
9. **Escalation paths**: as a user with `create pods` in a namespace, mount another ServiceAccount's token or run privileged (if PSA absent); demonstrate; then block with Pod Security Admission and RBAC tightening.
10. **RBAC audit**: run `rbac-tool`/`rakkess`/`kubectl-who-can`/Kubescape against the cluster; list dangerous bindings (`system:authenticated`, wildcards, `nodes/proxy`); remediate.
11. **Audit logging**: enable an audit policy; perform secret reads, exec, and RoleBinding changes; query logs to reconstruct; write alerts.
12. **Break-glass**: implement a time-bound elevation (temporary RoleBinding with a controller or script and expiry); test and review the audit trail.
13. **Clean up**.

Mark tested only after execution.

## 9. Common mistakes

- Believing Secrets are encrypted; storing real secrets in Git or ConfigMaps; secrets in env vars printed to logs.
- Granting `list/watch` on secrets (cluster-wide) to monitoring or "view" roles.
- Using `cluster-admin` for CI/CD, operators or developers; binding roles to `system:authenticated`.
- Forgetting that `create pods` ≈ read secrets/tokens in the namespace; allowing `pods/exec` in prod.
- Using the `default` ServiceAccount with extra permissions; leaving token automount on everywhere.
- Relying on env-var ConfigMap changes to propagate; `subPath` for configs that must reload.
- Long-lived static credentials instead of workload identity; shared credentials across teams.
- Not rotating secrets/keys; no re-encryption after enabling KMS.
- No audit review of RBAC; roles accumulate wildcards over time.
- Treating RBAC as sufficient: no admission policy for pod security; no namespace quotas.

## 10. Interview angles

- "Are Kubernetes Secrets secure? How do you protect them?" 
- "ConfigMap env vs volume: update behaviour? What is `immutable`?" 
- "Explain Role, ClusterRole, RoleBinding, ClusterRoleBinding; can a RoleBinding reference a ClusterRole?" 
- "What ServiceAccount token changed in 1.22/1.24? What is a bound token?" 
- "How do pods access cloud storage without keys?" (workload identity.)
- "Name RBAC permissions that are effectively cluster-admin." 
- "How would you design access for 20 research teams on a shared GPU cluster?" 
- "How do you keep secrets out of Git and rotate them safely?" 

## 11. Checkpoint questions (40)

1. ConfigMap size limit? **A:** ~1 MiB.
2. Do env vars update live? **A:** No.
3. Do mounted ConfigMaps update? **A:** Yes, eventually (not subPath).
4. What does `immutable: true` do? **A:** Prevents changes; reduces API load.
5. Secrets encoding? **A:** base64 (not encryption).
6. Default Secret encryption in etcd? **A:** None.
7. Best encryption approach? **A:** KMS v2 provider.
8. How verify etcd encryption? **A:** Prefix `k8s:enc:`.
9. Secret volume storage on node? **A:** tmpfs.
10. Safer injection method? **A:** Files with restrictive modes.
11. ESO purpose? **A:** Sync external secrets into Kubernetes.
12. CSI secret driver purpose? **A:** Mount external secrets as volumes.
13. Sealed Secrets idea? **A:** Encrypt to cluster key for Git.
14. SOPS idea? **A:** Encrypt values in YAML with KMS/age.
15. Bound SA token properties? **A:** Audience, expiry, bound to pod.
16. Legacy token Secrets created automatically since? **A:** Removed from 1.24.
17. Create short-lived token command? **A:** `kubectl create token`.
18. Why disable automount? **A:** Reduce credential exposure.
19. IRSA/Workload Identity do? **A:** Map ServiceAccounts to cloud IAM roles.
20. Humans should authenticate via? **A:** OIDC SSO.
21. RBAC allow/deny? **A:** Allow only, additive.
22. Role vs ClusterRole scope? **A:** Namespace vs cluster.
23. Can RoleBinding use ClusterRole? **A:** Yes, scoped to the namespace.
24. roleRef mutable? **A:** No.
25. Default roles? **A:** cluster-admin, admin, edit, view.
26. `edit` includes secrets? **A:** Yes (read).
27. `view` includes secrets? **A:** No.
28. Aggregation labels? **A:** `rbac.authorization.k8s.io/aggregate-to-*`.
29. `system:masters` risk? **A:** Bypasses RBAC.
30. Permission equal to exec? **A:** `pods/exec`; `nodes/proxy`.
31. Why `create pods` is powerful? **A:** Can mount secrets/tokens, hostPath.
32. Verbs enabling escalation? **A:** escalate, bind, impersonate.
33. `resourceNames` use? **A:** Restrict to specific objects.
34. Command to test permission? **A:** `kubectl auth can-i`.
35. List a user's permissions? **A:** `auth can-i --list`.
36. Audit event for authz? **A:** Audit annotations with decision.
37. Secret rotation for env-var consumers? **A:** Restart pods.
38. Secret rotation for file consumers? **A:** Auto-updated files, app must reload.
39. RBAC vs PSA? **A:** Who can act vs what pods may look like.
40. Break-glass principle? **A:** Time-bound, audited elevation.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Brendan Burns et al., *Kubernetes: Up and Running* (3rd edition; chapters 13 on ConfigMaps and Secrets and 14 on role-based access control).
- Josh Rosso et al., *Production Kubernetes* (chapter 7 on secret management).
- Kubernetes documentation on ConfigMaps, Secrets, encryption at rest, ServiceAccounts, authentication and RBAC; External Secrets, Secrets Store CSI Driver, Vault, Sealed Secrets and SOPS documentation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** KMS v2 and structured authentication configuration status by release, kubelet refresh timings, token lifetimes and defaults, aggregation labels for specific CRD projects, tool names for RBAC auditing, and every manifest/command; all labs are **untested**.
