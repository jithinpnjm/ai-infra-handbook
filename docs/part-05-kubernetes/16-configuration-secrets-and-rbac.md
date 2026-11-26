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

Consider a notebook that carries one token. Whether that token can read every team's checkpoints depends on how you injected it and how far you scoped it. AI platforms collect a lot of sensitive material. They hold object-store credentials for datasets and checkpoints, model hub tokens and API keys for LLM providers. They also hold registry credentials, database passwords for metadata stores, signing keys, and service tokens that operators use to reach the API. Configuration matters just as much: model parameters, tokenizer paths, NCCL environment, scheduler settings and feature flags all live there too.

How you inject, rotate and scope these values decides how far a single failure can reach. A leaked notebook can read every team's checkpoints, and a compromised job can create GPU pods without limit. RBAC is the authorisation layer for the Kubernetes API itself. A mistaken ClusterRoleBinding to `system:authenticated`, or a broad `nodes/proxy` grant, is a cluster-wide compromise. This chapter covers configuration objects, secret handling practices and RBAC design.

A useful picture is a research building with keycards. Configuration is the signage on the doors. It helps people find their way, and nobody is hurt if a sign is read by a visitor. Secrets are the keys to the server room. RBAC is the lock system that decides which keycard opens which door. A mistake with the signage costs you a confusing afternoon. A mistake with the keys or the locks can let someone walk into rooms they should never see. The chapter takes these in order, starting with the signage and moving toward the locks.

## Prerequisites and outcomes

This chapter builds on 5.5 and 5.7, so review those first. When you finish, you should be able to:

- Use ConfigMaps and Secrets correctly. That covers env vars, files, projected volumes, immutability, size limits and update propagation. You will also choose the injection method for each use case.
- Explain what Secrets really are: base64-encoded API objects in etcd. You will know how to encrypt them at rest with KMS, restrict access with RBAC, and integrate external secret stores such as External Secrets Operator, Secrets Store CSI, Vault Agent, and SOPS or Sealed Secrets.
- Describe authentication methods (certificates, tokens, OIDC), ServiceAccounts with projected or bound tokens, and workload identity to cloud IAM.
- Design RBAC with Roles, ClusterRoles, bindings, verbs, resources, subresources, aggregation and default roles. You will apply least-privilege patterns for multi-tenant AI platforms and recognize common escalation paths.
- Audit and test permissions with `can-i`, `auth whoami`, audit logs, RBAC reports and policy-as-code.
- Operate secrets and RBAC safely in GitOps pipelines.

If you are new to RBAC, do not try to memorize every verb in section 5 on the first read. Learn the shape first. Every request asks who is calling, what they want to do, and which object they want to do it to. The rest is detail you can look up when you need it.

## 1. ConfigMaps

![A timeline shows a new versioned ConfigMap created, the Deployment repointed and old pods replaced.](./img/p3-0516-immutable-rollout.svg)

*Figure 5.16.1. Immutable objects change by creating a new name and rolling pods onto it.*

![A ConfigMap reaches a container through env vars, a directory volume, or a subPath mount, and only the directory volume picks up changes.](./img/k16-config-doors.svg)

*Figure 5.16.2. Environment variables and subPath mounts keep the old value, while a directory volume mount picks up a ConfigMap change.*

Suppose a training job needs a log level and a hyperparameter file. Those settings are not confidential, so they belong in a ConfigMap rather than a Secret. A ConfigMap holds non-confidential configuration as key-value pairs. Use `data` for UTF-8 text and `binaryData` for bytes. The total size is up to ~1 MiB, which is the etcd and object limit. Think of a ConfigMap as a sticky note on the fridge. Anyone in the house can read it, and nobody expects it to hold a password. You can create one from literals, files or directories:

```bash
kubectl create configmap trainer-config --from-literal=LOG_LEVEL=info --from-file=hparams.yaml
kubectl create configmap nccl-env --from-env-file=nccl.env
```

The pod spec below shows three ways to consume a ConfigMap. `envFrom` loads every key as an environment variable, `env` picks out a single key, and `volumeMounts` places the files into the container.

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

Read the spec as three separate doors into the same ConfigMap. The `envFrom` block opens the whole `nccl-env` ConfigMap at once, so every key becomes an environment variable for the NCCL library. The `env` block is more precise. It takes one key, `LOG_LEVEL`, from `trainer-config`, and it sets `optional: true` so that a missing key is handled gently instead of stopping the start. The `volumeMounts` block is the third door. It places `hparams.yaml` under `/etc/trainer`, read-only, so the trainer can read its hyperparameters but cannot change them. The `defaultMode: 0444` line sets the file permissions for every file in the volume, and the `mode: 0444` on the item does the same for that one file.

Choosing among the three doors comes down to what the program expects. A library that reads environment variables wants `envFrom` or `env`. A program that reads a YAML file from disk wants a volume.

Each consumption method behaves differently when the ConfigMap changes, and that matters for config reloads. Environment variables are resolved when the container starts. Updating the ConfigMap does not change running processes. Names must be valid env var names, and keys with dots or dashes cannot be used with `envFrom` without remapping.

Here is what that means in practice. Suppose you change `LOG_LEVEL` from `info` to `debug` while a training run is halfway through. The ConfigMap now says `debug`, but the trainer keeps logging at `info`. The process started earlier still holds the old value in its environment, and the only way to pick up the new value is to start a new container. Keep that timing in mind before you blame Kubernetes for a change that never arrived.

Volume mounts update eventually. The kubelet sync period and cache TTL mean a change typically arrives within about 1 to 2 minutes. The update happens through an atomic symlink swap of the `..data` directory. `subPath` mounts never receive updates. Your application must re-read the files, or be signalled, to pick up a change. Config reloaders automate the restart: a sidecar, `reloader`, or `kubectl rollout restart` triggered by a hash annotation. A common GitOps pattern puts a hash of the ConfigMap into the pod template annotations. Helm uses `checksum/config` for this, and Kustomize uses hashed names from `configMapGenerator`. A config change then rolls the Deployment.

Pick the pattern that fits who should own the restart. A reloader is convenient when you want a change to take effect without a new deployment. A hash annotation is often the better choice when you want every config change to appear in Git history as a rollout, because a rollout is visible and easy to reverse. Many teams prefer that trade for training configs, since a change to a learning rate deserves the same review as a change to the code.

Setting `immutable: true` makes a ConfigMap or Secret unchangeable. That protects you from accidental edits. It also reduces API server load, because kubelets stop watching the object, and that matters at scale. To change an immutable object, create a new name and roll the pods onto it.

Here is a short walkthrough. Suppose `trainer-config` is immutable and you need to change `LOG_LEVEL` from `info` to `debug`. You create `trainer-config-v2` with the new value, point the Deployment at it, and let the rollout replace the old pods. The old ConfigMap stays in place until you delete it, so a rollback is a one-line change back to the old name.

Keep ConfigMaps small. Do not store datasets, models or large JSON blobs in them. Per-job generated configs should stay small too, because thousands of per-pod ConfigMaps create etcd and watch load. For binary content, use `binaryData`. For multi-line text, use `|` block scalars.

Think of the size limit as a rule about what belongs in the cluster at all. Every ConfigMap is stored in etcd, copied to every node that uses it and watched by the control plane. A large file multiplies that cost each time it is used. A model file that runs to many gigabytes belongs on storage built for that job, and the ConfigMap should only point to it.

The downward API, through `fieldRef` and `resourceFieldRef`, exposes pod metadata and resource limits to the container. The pod name, namespace, IP, node name, labels, and CPU and memory limits can arrive as env vars or files. That helps when you derive a rank or ID, or size workers for NUMA. For example, a distributed trainer might build its worker name from the pod name, then read its rank from a label that you set in the pod template. The app never calls the API server. It reads a value the kubelet already knows, so the app stays simple.

Three details from *Kubernetes: Up and Running* Chapter 13 come up often. The first is the key naming rule. A key may begin with an optional dot (`.`). It then needs a letter or digit (`[a-zA-Z0-9]`), followed by any mix of letters, digits, dots (`.`), dashes (`-`) and underscores (`_`). A key cannot contain consecutive `..` or spaces. So `.auth_token`, `Key.pem` and `config_file` are valid, while `Token..properties`, `auth file.json` and `_password.txt` are invalid. The `validate_configmap_or_secret_key()` function in `code/part05/rbac_secrets_validator.py` models this rule.

Read the examples slowly, because each one teaches a different part of the rule. The leading dot is allowed, so `.auth_token` passes. Underscores are allowed inside a key, so `config_file` passes. A key that starts with an underscore, such as `_password.txt`, fails, and so does a key with a double dot. The rule is easy to break with a file name copied from a laptop, such as `auth file.json` with a space in it. Check the key before you apply the object, rather than finding out from a pod that will not start.

The second detail is variable substitution. Kubernetes expands `$(ENV_VAR_NAME)` inside `command` and `args`. It uses the environment variables you defined earlier in `spec.containers[].env`. For example, `command: ["/kuard", "$(EXTRA_PARAM)"]` substitutes the value of `EXTRA_PARAM`.

Think of `$(VAR_NAME)` as a fill-in-the-blank that Kubernetes completes before the container starts. Kubernetes does the substitution itself, using the `$(...)` form, not the shell's `$VAR` form. That difference trips people up often, so check which one your field expects.

The third detail is how to update a file-backed ConfigMap or Secret without `kubectl edit`. Pipe a client-side dry run into `kubectl replace`:

`kubectl create configmap my-config --from-file=my-config.txt --dry-run=client -o yaml | kubectl replace -f -`

Read that pipeline from left to right. The first command builds the ConfigMap in memory and prints it as YAML, and the `--dry-run=client` flag keeps the cluster unchanged while it does so. The second command reads that YAML and replaces the stored object. The pipe is what turns a file change into a one-step update, instead of a manual edit that someone might get wrong.

The diagram below ties these pieces together. A Secret moves from an external store into a pod's tmpfs volume, while RBAC decides who can read the objects. Trace the top half first. The value starts in Vault or a cloud secret manager, a controller delivers it into the pod as a file in memory, and the application reads that file. The bottom half is about access. A subject, such as a user, a group or a ServiceAccount, reaches a Role through a binding. A RoleBinding keeps the grant inside one namespace, while a ClusterRoleBinding covers the whole cluster.

![ConfigMaps](./img/m5-16-1.svg)

*Figure 5.16.3. ConfigMaps, as a diagram.*

For a config change to reach running pods, pick a rollout pattern now and wire the hash into the pod template. Keep that choice in mind for the rest of the chapter. Whenever a section talks about rotating a credential or changing a setting, ask the same two questions: what has to restart, and who triggers the restart.

### Reading a ConfigMap back from the cluster

A ConfigMap is only key-value pairs stored in an object. The quickest way to check what a workload will see is to read the object back. Suppose you want a ConfigMap called `my-config`. It holds a settings file and two literal values. You create it like this:

```bash
kubectl create configmap my-config --from-file=my-config.txt --from-literal=extra-param=extra-value --from-literal=another-param=another-value
```

Then ask the API server for the stored object in YAML form:

```bash
kubectl get configmaps my-config -o yaml
```

```yaml
apiVersion: v1
data:
  another-param: another-value
  extra-param: extra-value
  my-config.txt: |
    # This is a sample config file that I might use to configure an application
    parameter1 = value1
    parameter2 = value2
kind: ConfigMap
metadata:
  creationTimestamp: ...
  name: my-config
  namespace: default
  resourceVersion: "13556"
  selfLink: /api/v1/namespaces/default/configmaps/my-config
  uid: 3641c553-f7de-11e6-98c9-06135271a273
```

The file name becomes the key, `my-config.txt`, and the file contents become its value. The `|` marker keeps the multi-line text together as one block. The literal values appear as plain keys next to it. Kubernetes fills in metadata such as `creationTimestamp`, `resourceVersion` and `uid` for you. Use `-o yaml` to confirm the real contents before you blame the application.

A habit that saves time is to read the object before you read the code. If the output shows a key missing, or a value with a stray space in it, the problem lives in the object. If the output looks right, the problem is in how the application reads it. Splitting the question that way narrows the search from the whole stack to one side of it.

## 2. Secrets

A data scientist pastes a Hugging Face token into a ConfigMap to get a job running, and the job works. Weeks later, a colleague with read access to the namespace runs `kubectl get configmap -o yaml` and copies the token into a chat message. Nothing was hacked. The token was simply stored in the wrong kind of object. That is the situation a Secret exists to prevent.

A Secret looks much like a ConfigMap. Its `data` field holds base64-encoded values, and `stringData` accepts write-only plain text. Kubernetes treats it differently, though. When a Secret is mounted, it sits in tmpfs on the node, and the kubelet does not write it to disk. RBAC restricts it through its own `secrets` resource, and it is eligible for encryption at rest. The types are `Opaque`, `kubernetes.io/tls` (which uses `tls.crt` and `tls.key`), `kubernetes.io/dockerconfigjson` for image pulls, `kubernetes.io/basic-auth`, `kubernetes.io/ssh-auth`, `kubernetes.io/service-account-token` (the legacy type) and `bootstrap.kubernetes.io/token`.

Pick the type that matches the job, because the type tells Kubernetes and other tools which keys to expect. A `kubernetes.io/tls` Secret always carries `tls.crt` and `tls.key`, so a component that handles HTTPS knows where to look. An `Opaque` Secret has no required keys, which is why it is the usual choice for a database password or an API token that you name yourself.

Secrets are not encrypted by default. Base64 is an encoding, not protection. Anyone with `get` or `list` on secrets can read them. So can someone who runs `exec` into a pod that mounts them, someone who reads etcd or an etcd backup, or someone with `nodes/proxy`. Think of base64 as a different font for the same letters. Anyone who can see the text can read it once they know the font. That is why the security model rests on five layers rather than one switch.

1. RBAC with tight `secrets` permissions. Avoid `list` and `watch` on all secrets, because listing reveals contents. Avoid wildcards too.
2. Encryption at rest in etcd. Configure the API server `EncryptionConfiguration` with a **KMS v2** provider, such as a cloud KMS or Vault transit, for envelope encryption. `aescbc` or `secretbox` with local keys is weaker, because the key sits on disk on the control plane. Rotate keys, then re-encrypt existing secrets with `kubectl get secrets -A -o json | kubectl replace -f -`. To verify, run `etcdctl get /registry/secrets/ns/name`. The output should show the `k8s:enc:kms:v2:` prefix.

Think of the encryption key as the lock on a safe-deposit box, and key rotation as changing that lock. You must keep the old key around long enough to open the boxes that were locked with it, or you lock yourself out of your own data. Checkpoint 5 at the end of this chapter walks through the safe order as a procedure.
3. Transport and node protection. TLS protects traffic between components. Secrets go only to nodes that run pods needing them, under the Node authorizer. They are mounted on tmpfs, and nodes sit inside the trust boundary.
4. Minimising exposure. Prefer files over env vars. Env vars show up in `/proc/<pid>/environ`, crash dumps, child processes, logs and runtime inspect output. Set `defaultMode: 0400` and `readOnly: true`, use `fsGroup`, avoid logging, and set `automountServiceAccountToken: false` where the workload does not need it.

Picture a crash. A framework prints its whole environment into the crash report, and the token ends up in a file that many people can open. A file path in a crash report shows only where the secret lives, not what it says. That is why the rule is to prefer files over environment variables.
5. Short-lived credentials instead of long-lived ones. Workload identity, projected tokens and dynamic secrets from Vault all fit here. A short-lived credential is a key that stops working on its own. Even if someone copies it, the window for misuse closes on its own schedule. That shift is worth more than careful storage alone, because a long-lived password stays useful to whoever copies it.

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

### Defense in depth for secrets

![Defence in depth for secrets as a stack of layers from physical security up to application credentials, with several locks and no single lock as the plan.](./img/p2-0516-layers-secrets.svg)

*Figure 5.16.4. Defence in depth for secrets is a stack of layers from physical security up to application credentials, where each layer covers a risk the one above cannot.*

How well you protect secret data comes down to how deep you are willing to go. Most teams start with choices that are "safe enough," then harden them over time. That approach carries risk and technical debt, and accepting that is part of the job. A wrong call about what is "safe enough" can still end in a bad headline, so it helps to know each layer.

A useful picture is a house with several locks. The front door lock matters, but so do the window latches, the safe in the bedroom and the habit of closing the garage. No single lock is the whole plan. The layers below run from the hardware upward, and each one covers a risk that the layer above it cannot cover.

Defense can start at the physical layer. Google, for example, has described its datacenter security in whitepapers and videos. The approach includes metal detectors, vehicle barriers and several layers of building security. When drives are retired, staff zero out the data, then crush or shred the drives. This section does not go deep into physical security, but it shows how seriously providers treat the hardware under your cluster.

Disk encryption is the next layer. Most cloud providers encrypt their physical disks at rest, using their own keys or keys you supply. That makes it very hard for anyone at the provider to read your data. On Linux, a common method for full block encryption is LUKS. It works with the dm-crypt subsystem, which has been in the Linux kernel since version 2.6. Dedicated storage systems such as vSAN, Ceph or Gluster each offer their own encryption at rest.

On AWS, enable encryption for Elastic Block Storage, and turn on encryption by default as a best-practice setting. Google Cloud encrypts at rest by default. You can also configure it with the Key Management Service, or KMS, to supply your own keys.

Whatever trust you place in your cloud provider or datacenter operators, make encryption at rest your default. It also guards against mistakes. Virtual machine snapshots are easy to create, and each one is a file that can leak onto a network. If someone picks the wrong option in a UI or an API field, encrypted data stays useless without the private key. Think of an unencrypted snapshot as a photocopy of your house keys that someone can carry out of the building. With encryption at rest, the photocopy opens nothing, because the key that matters is stored somewhere else.

Transport security is a separate concern. Encryption at rest does not cover data moving across the network, and a secret in flight is exposed the moment one hop skips TLS. Those hops include the path from you to the cluster through `kubectl`, and the path from the kubelet to the API server. Communication with the API server and etcd should always use TLS. Most installers already do this by default. You may only need to supply a Certificate Authority, or CA, to generate the certificates, and you may not need to replace the default CA.

Application encryption means your workload encrypts its own data with a key, at the user space level. Picture a dotfile full of credentials on a laptop. Disk encryption protects that file if someone pulls out the drive. If someone logs in as you, though, they can read the file. Encrypting the dotfile with a strong, password-protected `gpg` key closes that gap, because the attacker still sees only unreadable bits. The example also shows the limit of each layer. Disk encryption stops the stolen drive, but it does nothing against the person who logs in as you. Application encryption stops both, because the attacker then needs the passphrase as well as the file.

The rest of this chapter assumes that two things are already true in your cluster. Encryption at rest is enabled in the filesystem or storage systems that Kubernetes uses. TLS is enabled for all Kubernetes components and etcd. With those in place, we can look at how Kubernetes handles secrets itself. The etcd side of this is covered in 5.5.

### The Secret API, RBAC verbs, and scope

Suppose a workload needs its database login. The Secret API is one of the most used APIs in Kubernetes. You can create Secret objects in many ways, but workloads read them through one consistent API. Secrets look much like ConfigMaps, and workloads consume them the same way, through environment variables or volumes. Here is a Secret with base64 data:

```
apiVersion: v1
kind: Secret
metadata:
name: mysecret
type: Opaque
data:
dbuser: aGVwdGlvCg==
dbkey: YmVhcmNhbm9lCg==
```

The `data` field holds base64 encoded values, and every Kubernetes Secret stores its data this way. If you want to submit plain strings, use the `stringData` field instead:

```
apiVersion: v1
kind: Secret
metadata:
name: mysecret
type: Opaque
stringData:
dbuser: heptio
dbkey: bearcanoe
```

The API server encodes `stringData` when it applies the object to etcd. Many people assume this encoding protects Secrets, but it does not. Secret data can hold strange characters or binary data, and base64 makes sure that data is stored correctly. Protection comes from RBAC instead, so the verbs matter. These three verbs decide what a caller can do with Secrets:

- `get`: retrieve the data of a known Secret by its name.
- `list`: get a list of all Secrets and their data.
- `watch`: watch for any Secret change or any change to Secret data.

Read the three verbs as three different kinds of trust. `get` asks for one secret by name, so the caller must already know what it wants. `list` returns the secrets in the namespace, so it exposes many names and values at once. `watch` streams changes, so a caller holding it sees each new value as it arrives, not only the value that exists today.

Small RBAC mistakes can expose a lot. Granting `list` exposes every Secret in a Namespace. A ClusterRoleBinding used by accident can expose the whole cluster. In many cases, users do not need any of these verbs at all. A simple test helps. Ask whether the person needs to read the password, or only needs the application to receive it. Most people only need the second, and the kubelet already handles that path. A user's RBAC does not decide which Secrets a workload can use, though. The kubelet handles that part. As long as a Pod references a valid Secret, the kubelet makes it available through the method you choose.

Secrets are Namespace scoped. Without copying a Secret into other Namespaces, a Pod can reference only Secrets in its own Namespace. That also means any Pod in a Namespace can reach any Secret there. Think carefully about how you share Namespaces among workloads. Consider a shared namespace with two teams. If a Pod from team B names a secret that belongs to team A, the reference fails, because the Pod cannot see the other team's secrets. If an engineer on team B holds `get` on secrets in that namespace, though, that engineer can read the secret through the API without starting any Pod. Namespace boundaries only work when the RBAC behind them is also tight. Admission control can add checks on top of this model, which is a topic for a later chapter.

### Consumption models: environment variables, volumes, and the client API

Workloads can consume a Secret in three ways. The right choice may depend on what the application expects, and each choice comes with trade-offs.

Environment variables are the first option. A workload can inject Secret data into them. The YAML names an environment variable and points to a key in a Secret. This helps workloads that already expect an environment variable, because the application code may not need to change. Here is a Pod that does this:

```
apiVersion: v1
kind: Pod
metadata:
name: nginx
spec:
containers:
- name: nginx
image: nginx
env:
- name: USER
valueFrom:
secretKeyRef:
name: mysecret
key: dbuser
- name: PASS
valueFrom:
secretKeyRef:
name: mysecret
key: dbkey
```

In that example, the application sees the variable `USER`. `mysecret` is the Secret object, and `dbuser` is the key inside it that gets injected into `USER`.

Environment variables have a downside: they cannot hot reload. A change to a Secret does not reach the Pod until the Pod is re-created. That can happen through manual action or through a system event, such as a reschedule. Some people also consider environment variables less secure than volume mounts. That point is debatable, but the leak paths are real. Process and container runtime inspection can show environment variables in plain text. Some frameworks, libraries and languages dump environment variables into logs in debug or crash modes. Weigh these risks before you use environment variables. A quick way to decide is to ask who owns the code. If the program is a library that insists on environment variables, use them and set strict rules about logging. If you control the code, read the file instead. Reading the file also gives you an easy way to rotate, because the application can re-read it when the value changes.

Volumes are the second option. The Pod spec defines a volume that references the Secret, and the container mounts that volume with a `volumeMount`:

```
apiVersion: v1
kind: Pod
metadata:
name: nginx
spec:
containers:
- name: nginx
image: nginx
volumeMounts:
- name: creds
readOnly: true
mountPath: "/etc/credentials"
volumes:
- name: creds
secret:
secretName: mysecret
```

The `volumes` entry is the Pod-level volume, and its name must match the mount. The `volumeMounts` entry places that volume into the container filesystem at `mountPath`. With this Pod, the Secret data appears under `/etc/credentials`, and each key and value pair gets its own file:

```
root@nginx:/# cat /etc/credentials/db
dbkey dbuser
```

Volumes have the biggest advantage in updates. When the Secret changes, the kubelet reloads it, and the container filesystem shows the new value without a Pod restart. On Linux, the kubelet uses tmpfs, which keeps Secret data in memory only. You can confirm this on the Linux host through the mount table:

```
# grep 'secret/creds' secret/creds
tmpfs
/var/lib/kubelet/pods/
e98df9fe-a970-416b-9ddf-bcaff15dff87/volumes/
kubernetes.io~secret/creds tmpfs rw,relatime 0 0
```

Read the mount line the way you would read a receipt. The filesystem type is `tmpfs`, and the mount point is the secret's own folder inside the pod's directory under `/var/lib/kubelet`. Because tmpfs lives in memory, the files disappear when the mount is removed, which happens when the Pod leaves the node.

When the `nginx` Pod leaves this host, the mount goes away with it. Keep Secret data small, which makes credentials and keys the right fit. Do not use a Secret as a pseudo database. On the application side, watching the directory or file and re-injecting the values is enough. The application never needs to talk to the API server, and teams have seen this pattern work well in many workloads.

The last model is client API consumption, and it is not a core Kubernetes feature. The application talks to the kube-apiserver to fetch Secrets itself. Frameworks and libraries can make this easier. For Java, Spring Cloud Kubernetes connects Spring's PropertySource type to Kubernetes, so the application can read Secrets and ConfigMaps.

Be careful with this approach. *Production Kubernetes* generally discourages it. Even for ConfigMaps, it is less than ideal to have each application talk to the API server. We prefer applications that do not need to know where they run. An app that can run on a VM should also run on Kubernetes or another container service. Most languages already read environment variables and files, and the kubelet can deliver Secret data through those channels. Direct access adds another connection and another watch on the API server. Each workload then needs its own ServiceAccount with RBAC to read its Secrets. When the kubelet delivers Secrets, no ServiceAccount is needed, and the `default` ServiceAccount can and should be disabled altogether.

Think of the difference as a courier. In one model, the courier brings the package to your door, and you never leave the house. In the other, you drive to the warehouse yourself, show your ID, and carry the package home. The second model works, but every trip adds risk and a second place to check your identity. The kubelet is the courier, and the application should only open the door.

### A TLS Secret mounted as files

Secrets are easier to understand with a real case. Suppose the `kuard` app needs a TLS certificate and key to serve HTTPS. You should not bake those files into the image. Keeping them out of the image keeps the image portable, so it can run in any environment. You store the files in a Secret and mount them at run time instead.

Start by creating the Secret from the two files, `kuard.crt` and `kuard.key`:

```bash
kubectl create secret generic kuard-tls --from-file=kuard.crt --from-file=kuard.key
kubectl describe secrets kuard-tls
```

The output confirms that `kuard-tls` holds two data elements. It shows their sizes, not their contents:

```
Name:         kuard-tls
Namespace:    default
Labels:       <none>
Annotations:  <none>

Type:  Opaque

Data
====
kuard.crt:  1050 bytes
kuard.key:  1679 bytes
```

Each data element of a Secret becomes its own file under the mount point. The volume mount decides where that directory lives. In the `kuard` example, the Pod mounts `kuard-tls` at `/tls` as read-only, so the container sees `/tls/kuard.crt` and `/tls/kuard.key`:

```yaml
volumeMounts:
- name: tls-certs
  mountPath: "/tls"
  readOnly: true
volumes:
- name: tls-certs
  secret:
    secretName: kuard-tls
```

Create the Pod, then forward a local port to it:

```bash
kubectl apply -f kuard-secret.yaml
kubectl port-forward kuard-tls 8443:8443
```

Open https://localhost:8443 in a browser. The browser warns about an invalid certificate. That happens because the certificate is self-signed for `kuard.example.com`. Accept the warning, and the `kuard` server loads over HTTPS. Then open the File system browser tab to find the files in the `/tls` directory.

If the page loads and the files appear in the browser, the whole chain worked. The Secret held the bytes, the kubelet mounted them, and the application read them from `/tls`. If the page does not load, check the Secret's keys first with `kubectl describe`, because a wrong file name is an easy mistake to make.

> **Warning:** The certificate and key in this demo are public, so they provide no real security. Use them only to learn how Secrets work.

### Image pull secrets

`kubectl create secret docker-registry regcred --docker-server=... --docker-username=... --docker-password=...` produces a `kubernetes.io/dockerconfigjson` Secret. Attach it through `imagePullSecrets` on pods, or on the ServiceAccount with `kubectl patch serviceaccount default -p '{"imagePullSecrets":[{"name":"regcred"}]}'`. The better option avoids a stored password altogether. Node-level credential providers, which are kubelet image credential provider plugins for ECR, GCR and ACR, or workload identity, mean no long-lived password exists. Think of an image pull secret as a library card. The card lets the kubelet borrow images from a private shelf, and attaching it to a ServiceAccount means every Pod that uses that account can carry it.

### GitOps-safe secret management

![A table compares six GitOps secret patterns by how the value reaches the pod and what is left in etcd.](./img/p3-0516-gitops-where-lives.svg)

*Figure 5.16.5. Choose by where the plaintext may exist, since some patterns still create a native Secret in etcd.*

Never commit plaintext Secrets to Git. The approaches below keep the values out of the repository. Related options are covered in 4.12 and 4.26. The table lists the main patterns and notes for each. Notice which rows still create a native Secret in etcd, and which keep the value out of etcd entirely. A useful way to read the table is to ask one question per row: where does the plaintext value live, and who can fetch it? Sealed Secrets and SOPS keep the value encrypted in Git, but the cluster still produces a normal Secret at the end. Workload identity removes the value altogether, because there is nothing to store.

| Approach | How | Notes |
|---|---|---|
| **External Secrets Operator (ESO)** | `ExternalSecret`/`SecretStore` CRs reference Vault/AWS SM/GCP SM/Azure KV; ESO syncs into native Secrets | Secret values never in Git; native Secret still in etcd; refresh intervals handle rotation |
| **Secrets Store CSI Driver** (`secrets-store-csi-driver`, `SecretProviderClass`) | Mounts secrets from a vault as a volume via `driver: secrets-store.csi.k8s.io` and a `SecretProviderClass` (and optionally syncs to a Secret) | Avoids etcd persistence when not syncing; per-pod volume; provider pods needed |
| **Vault Agent Injector / Vault Secrets Operator** | Sidecar/operator renders secrets into the pod via Vault Kubernetes auth | Dynamic secrets and leases |
| **Sealed Secrets** (`SealedSecrets`, `kubeseal`) | Encrypt a Secret into a `SealedSecret` (`bitnami.com/v1alpha1`) with `kubeseal` using the cluster public key; controller decrypts to a Secret | Simple; cluster-bound key; rotate keys every 30 days |
| **SOPS** (age/KMS) with Flux/Argo plugins | Encrypted YAML in Git, decrypted at apply | Reviewable diffs (keys visible) |
| **CSI/Workload Identity** | Pods authenticate to cloud APIs with federated tokens, no secret at all | Best for cloud resources |

### Sealed Secrets in depth

![A flow showing a public key sealing a Secret into Git and the in-cluster controller decrypting it with the private key.](./img/p3-0516-sealed-flow.svg)

*Figure 5.16.6. Only the encrypted object lives in Git while the controller holds the key that turns it back into a Secret.*

Declarative workflows raise a hard question. Your manifests belong in Git, but the credentials and keys they use do not. Teams that want a pure GitOps model often keep secrets out of Git entirely, and that breaks the pattern. The other option is to seal the secret, so its committed form reveals nothing useful. Picture a locked box with a mail slot. Anyone can drop a letter through the slot, but only the holder of the key can open the box and read what is inside. Sealing works the same way, with the public key as the slot and the private key as the lock's key.

Asymmetric cryptography makes sealing possible. An encryption key, usually public, locks the secret. A decryption key, usually private, unlocks it. A secret sealed with the public key stays protected as long as the private key stays safe. You still need a cipher you trust, a safe private key, and rotation policies for both keys and secret data.

The Bitnami `sealed-secrets` project is a common open source choice. Its `sealed-secret-controller` runs in the cluster and generates the keys by default. Developers use the `kubeseal` command-line tool, which needs only the public key. To get started, deploy the controller:

```bash
kubectl apply -f
https://github.com/bitnami-labs/sealed-secrets/releases/\
download/v0.9.8/controller.yaml
```

You can bring your own certificates, but by default the controller creates them. The public and private keys sit in a Kubernetes Secret at `kube-system/sealed-secret-key`. Do not read that Secret directly. Instead, clients should fetch the encryption key from the controller's endpoint, with this command:

```bash
kubeseal --fetch-cert
```

How you expose that endpoint is up to you. Once `kubeseal` has the public key, it can turn a Secret into a SealedSecret. You can start with an ordinary Secret:

```
apiVersion: v1
kind: Secret
metadata:
name: mysecret
type: Opaque
data:
dbuser: aGVwdGlvCg==
dbkey: YmVhcmNhbm9lCg==
```

Run `kubeseal` against that file to produce encrypted JSON:

```bash
kubeseal mysecret.yaml
```

```
{
"kind": "SealedSecret",
"apiVersion": "bitnami.com/v1alpha1",
"metadata": {
"name": "mysecret",
"namespace": "default",
"creationTimestamp": null
},
"spec": {
"template": {
"metadata": {
"name": "mysecret",
"namespace": "default",
"creationTimestamp": null
},
"type": "Opaque"
},
"encryptedData": {
"dbkey": "gCHJL+3bTRLw6vL4Gf......",
"dbuser": "AgCHJL+3bT......"
}
},
"status": {
}
}
```

This object can go anywhere in your repository. As long as the sealing key held by the controller stays uncompromised, the data stays safe. Notice what the file contains and what it does not. The `encryptedData` values are ciphertext, so the file is safe to commit. The name and namespace are visible, though, so anyone who reads the repository can see that a secret called `mysecret` exists in `default`. The controller turns the SealedSecret into a standard Secret, and that Secret records the SealedSecret as its owner:

```
ownerReferences:
- apiVersion: bitnami.com/v1alpha1
controller: true
kind: SealedSecret
name: mysecret
uid: 49ce4ab0-3b48-4c8c-8450-d3c90aceb9ee
```

If you delete the SealedSecret, its corresponding Secret is garbage collected. That link keeps the cluster tidy. The sealed object is the source, and the plain Secret is a derived copy that the controller owns. Remove the source and the copy goes with it.

Key renewal deserves attention. If the sealing private key leaks, for example through an RBAC misconfiguration, treat every sealed secret as compromised. By default, the controller renews the key every 30 days. The new key does not replace the old ones. It joins the list of keys that can unseal data, and it is used for all new encryption. Existing SealedSecrets are not re-encrypted. If the key leaks, you should:

- Immediately rotate your encryption key.
- Rotate all existing secrets.

Re-encrypting alone is not good enough. Someone could go through Git history, find an old encrypted file, and use the compromised key on it. Keep a rotation strategy for passwords and a renewal strategy for keys. Consider the order that a leak demands. You rotate the sealing key first, then rotate every password that was sealed with the old key. Skipping the second step leaves a gap, because an attacker who still holds an old sealed file can unseal it with the leaked key.

Namespace binding comes next. A SealedSecret uses its Namespace during encryption, so it belongs to the Namespace where it was created and cannot simply be moved to another one. This default is the most secure choice, so leave it as is. The namespace binding works like a stamped envelope. The seal records the address it was sent to, so the envelope cannot be relabelled and delivered somewhere else. The sealed-secrets documentation covers configurable access policies.

Multicluster setups make sealed secrets harder. Many topologies treat clusters as ephemeral. Unless you share private keys among all of them, each cluster needs its own keys. Developers also need a place to fetch the encryption key, and that place multiplies from one cluster to many. The problem is solvable, but plan for it. Think of each cluster as a separate building with its own lock. A key cut for one building does not open the others, unless someone copies the key, and copying keys is exactly the risk you are trying to avoid.

Know the scope of this tool before you rely on it. A common misunderstanding is that SealedSecrets replaces encrypting etcd, or running an enterprise secret store such as Vault. It does not. The approach lets you encrypt data and store it safely in Git. The private key and unencrypted secrets still end up in Kubernetes. Without steps beyond the Secret API defaults, they sit unencrypted at the application layer. The gap is easy to miss, because the file looks protected. A sealed file in Git is protected. The Secret it becomes inside the cluster is an ordinary Secret, and it sits in etcd the way any Secret does unless you also enable encryption at rest. Know the scope of every tool you choose.

### Rotation

![Two-phase rotation adds the new credential, moves each consumer over, and only then removes the old credential.](./img/k16-two-phase-rotation.svg)

*Figure 5.16.7. Two-phase rotation adds the new credential first, moves every consumer, and removes the old one last.*

Rotation only works when consumers reload. File mounts update automatically through the kubelet refresh, but the application still has to re-read them. Environment-variable secrets need a pod restart. You can use a reloader controller keyed on the secret hash, or run `kubectl rollout restart`. For databases and tokens, use two-phase rotation: add the new credential, switch consumers over, and then remove the old one. You can automate this with ESO refresh and Reloader, Vault dynamic leases, or cert-manager for certificates (see 5.12). Consider the two-phase rule as a bridge. The new credential goes up first, so the old and the new both work for a while. Then every consumer moves over. Only after that does the old credential get removed. If you remove it first, any consumer you forgot to update fails at once.

### HashiCorp Vault Agent Injector and Kubernetes authentication

![Annotations cause a webhook to add Vault agent containers that authenticate with the pod token and write a secret file.](./img/p3-0516-vault-injector-flow.svg)

*Figure 5.16.8. The pod proves its identity with its ServiceAccount token and Vault checks it through TokenReview.*

Instead of syncing external secrets into etcd as Kubernetes `Secret` objects, you can let the HashiCorp Vault Agent Injector deliver them. The difference matters. A synced Secret lives in etcd and can be read through the API. An injected secret is rendered into a file inside the pod, so the value never becomes a Kubernetes object at all. The injector uses a `MutatingWebhookConfiguration`, named `vault-agent-injector-cfg`, to add two containers. The first is a `vault-agent-init` init container, which fetches initial secrets before the workload starts. The second is an optional `vault-agent` sidecar, which keeps secrets updated. Both write rendered files onto an in-memory volume mounted at `/vault/secrets`. As detailed in *Production Kubernetes* Chapter 7, the injector watches for Pod annotations:

- `vault.hashicorp.com/agent-inject: "true"` instructs the webhook to inject the `vault-agent-init` init container. The example in *Production Kubernetes* uses `vault:1.3.2` for it.
- `vault.hashicorp.com/agent-inject-status: "update"` is optional. It instructs the webhook to also inject the long-running `vault-agent` sidecar, which refreshes leased or rotated secrets.
- `vault.hashicorp.com/role: "<role>"` selects the Vault Kubernetes auth role. You can also bind the role in the agent configuration.
- `vault.hashicorp.com/agent-inject-secret-<filename>: "<vault-path>"` tells the agent which Vault secret to write to `/vault/secrets/<filename>`. For example, `vault.hashicorp.com/agent-inject-secret-db-creds: "secrets/db/creds"` or `vault.hashicorp.com/agent-inject-secret-config` works.
- `vault.hashicorp.com/agent-inject-template-<filename>` formats the rendered file with a Go template instead of the default Go map print format. In the example below, a Pod template formats database credentials into a JDBC connection string at `/vault/secrets/db-creds`. A `config` secret lands at `/vault/secrets/config` instead:

```yaml
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/agent-inject-status: "update"
        vault.hashicorp.com/role: "database"
        vault.hashicorp.com/agent-inject-secret-db-creds: "secrets/db/creds"
        vault.hashicorp.com/agent-inject-template-db-creds: |
          {{- with secret "secrets/db/creds" -}}
          jdbc:oracle:thin:{{ .Data.data.username }}/{{ .Data.data.password }}
          {{- end }}
```

Injection is the approach we highly recommend when it is possible. It decouples the secret store from the application entirely. Think of a delivery service. The platform signs for the package and places it at the door, so the application only opens the door and never needs the courier's phone number. The trade-off is that the platform now has to offer secret injection as a service, and that adds complexity.

The webhook runs on every Pod CREATE or UPDATE event, but it changes only the Pods that carry the annotations. By default, Vault writes each secret in the format of a printed Go map, and all secrets go into `/vault/secrets`:

```
key: map[k:v],
key: map[k:v]
```

Authentication and authorization are the hard part of this model. You can set Vault to authenticate Pods with their existing ServiceAccount tokens. Vault then validates the requester's identity through the TokenReview API. It must still decide whether that ServiceAccount is allowed to read the secret. Those policies and bindings live in Vault, and you must maintain them there. Two systems now share the trust decision, so a change in one can break the other. When a pod suddenly cannot read its secret, check both sides before you assume either one is at fault.

To let Pods authenticate to Vault with their Kubernetes ServiceAccount tokens, Vault validates those tokens against the Kubernetes `TokenReview` API. You enable and configure the Kubernetes auth method inside Vault. Then you write a policy and bind a Vault role to the Pod's ServiceAccount name and Namespace. The example below follows these steps:

```bash
# Enable Kubernetes authentication in Vault (untested here)
vault auth enable kubernetes

# Configure Vault to talk to the Kubernetes API server for TokenReview checks (untested here)
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"

# Create a read policy in Vault for team-a secrets (untested here)
vault policy write team-a - <<EOF
path "secret/data/team-a/*" {
  capabilities = ["read"]
}
EOF

# Bind the Kubernetes ServiceAccount 'webapp' in namespace 'team-a' to the policy (untested here)
vault write auth/kubernetes/role/database \
  bound_service_account_names=webapp \
  bound_service_account_namespaces=team-a \
  policies=team-a \
  ttl=20m
```

### Secrets Store CSI driver and CyberArk

CyberArk is another option that many clients already use. It offers a Credential Provider and a Dynamic Access Provider (DAP). Like Vault, it supports `initContainers` that run alongside your application to talk to DAP.

A newer approach is the `secrets-store-csi-driver`. At the time of writing, it is a Kubernetes subproject within `kubernetes-sigs`. It lets Pods use externally hosted secrets without a sidecar or an initContainer. Secret access starts to feel like a platform service instead of something each application integrates with. A simple picture helps. An application that uses a sidecar is like a tenant who hires a locksmith for each door. The CSI driver is more like a building that provides the locksmith for every tenant. The driver runs as a DaemonSet, with a driver Pod on every host, much like a storage CSI driver.

The driver relies on a provider to look up secrets in the external system. For Vault, that means installing the `vault-provider` binary on every host, in the location set by the driver's `provider-dir` mount. The binary may already exist on the host, or a DaemonSet-like process often installs it. This approach raises open questions. When a Pod does not request the secret itself, who handles identity? The driver or provider must work that out, because they make requests on the Pod's behalf.

The main API is the `SecretProviderClass`. For Vault, it looks like this:

```
apiVersion: secrets-store.csi.x-k8s.io/v1alpha1
kind: SecretProviderClass
metadata:
name: apitoken
spec:
provider: vault
parameters:
roleName: "teama"
vaultAddress: "https://vault.secret-store:8000"
objects: |
array:
- |
objectPath: "/secret/team-a"
objectName: "apitoken"
objectVersion: ""
```

The `vaultAddress` points to the Vault service, named `vault`, in the `secret-store` Namespace. The `objectPath` is the path in Vault where the key/value object was written, and `objectName` is the object to look up in `team-a`. With the SecretProviderClass in place, a Pod references it like this:

```
kind: Pod
apiVersion: v1
metadata:
name: busybox
spec:
containers:
- image:
name: busybox
volumeMounts:
- name: secrets-api
mountPath: "/etc/secrets/apitoken"
readOnly: true
volumes:
- name: secrets-api
csi:
driver: secrets-store.csi.k8s.com
readOnly: true
volumeAttributes:
secretProviderClass: "apitoken"
```

When this Pod starts, the driver and provider try to retrieve the secret. If authentication and authorization to the external provider succeed, the secret appears in a volume mount, like any Kubernetes Secret. From the driver Pod on the node, you can read the logs to see the command sent to the provider. A log line like this is useful when a Pod hangs on startup. It shows that the driver asked the provider for the secret and which path it asked to fill. The sensitive attributes are redacted on purpose, so the log does not leak the secret itself:

```
level=info msg="provider command invoked: /etc/kubernetes/
secrets-store-csi-providers/vault/provider-vault --attributes [REDACTED]
--secrets [REDACTED] [--targetPath /var/lib/kubelet/pods/
643d7d88-fa58-4f3f-a7eb-341c0adb5a88/volumes/kubernetes.io~csi/
secrets-store-inline/mount --permission 420]"
```

This approach is worth keeping an eye on. Its user experience and its ability to abstract secret providers look promising. If the project stabilizes and providers mature, it could become common for teams building application platforms on Kubernetes.

### Best practices for secrets

Application consumption of secrets depends heavily on the language and frameworks in use. The variance is high, but these practices apply broadly.

Always audit secret interaction. A Kubernetes cluster should run with auditing enabled. Audit events tell you which resources were touched, when, and by whom. For mutations, they also show what changed, and auditing secret events is critical when you react to access issues. The cluster audit documentation has the details.

Do not leak secrets. Leaking a secret is never desirable, and in multitenant clusters it is easy to do by accident. A common mistake is logging a secret. Engineers building operators often deal with secrets for the systems they manage, and during development they may log those values to debug. A useful habit is to treat every log line as published. If you would not paste a line in a public forum, do not let your application print it. Logs go to stdout and stderr, and many platforms forward them to a log analysis system. The secret can then travel in plain text through many environments. Manifests with test secrets can also slip into source control, so keep test values out of your repositories.

Prefer volumes over environment variables. Most applications should read secrets from volumes. Environment variables leak more easily, for example through an `echo` command during testing, or when a framework dumps them at startup or during a crash. Volumes do not solve every leak, though. Their key benefit for developers is that they update automatically when a secret changes, which supports hot-reloading of tokens. A change to an environment variable requires a Pod restart. Consider the difference during a crash. A crash handler that prints the environment prints the secret with it, while a file mount shows only a path.

Keep secret store providers unknown to your application. Applications can fetch secrets in many ways, from a call inside business logic to an environment variable set at startup. Separation of concerns says the application should not care whether Kubernetes, Vault or another provider manages the secret. That keeps the app portable and reduces its complexity. To fetch from a provider, an app must know how to talk to it and must authenticate to it. Prefer environment variables or volumes, with volumes as the ideal. An app can watch the filesystem for changes, and it does not matter which store is behind the files. Framework libraries that talk to the API server directly, such as Spring's, are convenient. Still, weigh the points above before you use them.

### Choosing how an application reads ConfigMaps and Secrets

![Config should come from the platform at runtime, with a mounted file preferred over environment variables or a client API call, and baked-in config rejected.](./img/p2-0516-config-doors.svg)

*Figure 5.16.9. Config should come from the platform at runtime, and a ConfigMap or Secret mounted as a file is the preferred way to read it.*

Config should come from the platform at runtime, not from inside the container image. A baked-in setting ties the binary to one environment. It also exposes secrets to anyone who can pull the image. Imagine a config file baked into an image that is pushed to a shared registry. Anyone with pull access to that registry now holds the database password, even if they never had access to the cluster. Kubernetes offers three ways to deliver config to a Pod, and they differ in how well they suit each app.

Mounting a ConfigMap or Secret as a file is the preferred method. The Pod spec names the volume and the path where it appears. This example mounts the `my-config` ConfigMap at `/etc/my-app/config.json`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
  - image: my-app
    name: my-app:v0.1.0
    volumeMounts:
    - name: my-config
      mountPath: /etc/my-app/config.json
  volumes:
  - name: my-config
    configMap:
      name: my-config
```

Files in a volume update in place, so you can change config without restarting the app or re-creating the Pod. The app has to notice the change, though. It must watch the file and reload its settings. Many libraries do this for you. When an app cannot, a sidecar container can watch the file and send the main process a signal, such as `SIGHUP`, when new config appears. To test whether your app reloads, edit the ConfigMap, wait a minute or two, and check whether the app's behavior changed. If it did not change, the app is not reloading, and the problem is in the app rather than in Kubernetes.

Environment variables are the natural choice when the app reads its settings from the environment or from command-line flags. This Pod sets `DEBUG` from the `debug` key in `my-config`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
  - name: my-app
    image: my-app:v0.1.0
    env:
    - name: DEBUG
      valueFrom:
        configMapKeyRef:
          name: my-config
          key: debug
```

Environment variables have two downsides. A change to the ConfigMap or Secret does not reach a running Pod until it restarts. Also, some frameworks print their whole environment at startup or during a crash. For a Secret, that can leak the password into a log file. Consider a web framework that logs its startup environment at debug level. A database password held in an environment variable then lands in the log store, where many people can read it. A volume mount would not have put the password into that line.

The third option is to have the app call the Kubernetes API directly. It reads ConfigMaps and Secrets from the API server and can watch them for changes. Client libraries and some frameworks, such as Spring Cloud Kubernetes, offer this. The convenience comes at a cost. The app is now tied to Kubernetes, and it needs a ServiceAccount with RBAC permissions. Each app that polls the API also adds load to the control plane. Those issues are why volume mounts and environment variables are the usual choice. They keep the application decoupled from the platform. Picture a large fleet of pods, each polling the API server for its settings. The control plane spends its effort answering those reads, and every application is now tied to Kubernetes. That is the cost the paragraph above describes.

### Injecting workload metadata with the Downward API

Some workloads need to know facts about themselves. They may need their Namespace, their labels, or their resource limits. The Downward API provides those facts without the app having to talk to Kubernetes. As with ConfigMaps and Secrets, you can deliver the values as environment variables or as files.

This Pod receives its memory limit in the `MEM_LIMIT` environment variable:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
  - name: my-app
    image: my-app:0.1.0
    command: [ "my-app" ]
    env:
    - name: MEM_LIMIT
      valueFrom:
        resourceFieldRef:
          containerName: my-app
          resource: limits.memory
```

The app reads `MEM_LIMIT` like any other setting. It can then size its heap or worker pool to fit inside the container. The Downward API keeps the application free of Kubernetes calls while still letting it see facts that only the platform knows.

### Offloading external secret systems to the platform

Kubernetes Secrets are not the only option. External systems such as HashiCorp Vault offer features that Kubernetes Secrets lack. Vault provides dynamic secrets, secret rotation and time-based tokens. If your app already uses Vault, keep using it on Kubernetes. Even if you do not use Vault yet, it is worth comparing it with Kubernetes Secrets.

Teams that run an external system get the most value when the platform handles the integration. The platform can expose a Vault secret to a Pod as a volume or as an environment variable. The application then consumes a plain file or variable and does not need to know where the secret came from. This keeps each application simpler, and it standardizes how every team gets its secrets. Think of the platform as the post office. It knows the addresses and delivers to the door, while each application only needs its own mailbox.

## 3. Projected volumes and ServiceAccount tokens

![Three sources, a token, a CA bundle and pod labels, are merged into one directory by a projected volume.](./img/p3-0516-projected-volume.svg)

*Figure 5.16.10. A projected volume gathers identity, trust and self-description into a single mount.*

A pod often needs a token, a CA bundle and its own labels at the same time. A projected volume gathers those in one directory. A projected volume combines several sources in one directory. The sources are `secret`, `configMap`, `downwardAPI`, `serviceAccountToken`, and `clusterTrustBundle`, which holds CA bundles. The example below combines three of them.

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

Notice the `serviceAccountToken` source. Its token is valid only for the `vault` audience. `expirationSeconds: 3600` means the kubelet refreshes the token before it expires.

The three sources each do a different job. The token proves who the pod is. The CA bundle lets the pod trust the server it talks to. The labels describe the pod itself. All three land in one directory, so the application reads everything from one place and does not need to know which source a file came from.

### ServiceAccounts

Every namespace has a `default` ServiceAccount, and pods use it unless `serviceAccountName` is set. Since 1.22+, pods receive a bound ServiceAccount token. The token is a JWT signed by the API server, and it is audience-bound to the API server. It is time-limited, with a default of about 1 h, and it is refreshed automatically. It is also bound to the pod, node and Secret object, and it becomes invalid when the pod is deleted. The token is mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token` through a projected volume. It replaces legacy token Secrets, which never expired. Those are no longer auto-created since 1.24. Create an explicit `type: kubernetes.io/service-account-token` Secret only when you truly need one. For short-lived tokens, use `kubectl create token <sa> --duration=...` instead. A simple way to tell the two apart is to look at how the token was made. A bound token is created for the pod at start time, and the kubelet refreshes it. A token from `kubectl create token` lasts for the duration you asked for, and then it stops working.

Follow these practices when you set up ServiceAccounts:

- Use one ServiceAccount per workload, with least-privilege RBAC. Never use `default` for anything privileged.
- Set `automountServiceAccountToken: false` on the ServiceAccount or the pod if the workload does not call the API.
- For external systems such as Vault, cloud federation, SPIFFE-like identities or OIDC discovery, use projected tokens with custom audiences instead of passing long-lived keys.

Read the three bullets as one habit. Each workload gets its own identity, it gets no more permission than it needs, and it does not carry a key that someone could copy and reuse elsewhere.

Workload identity federation maps Kubernetes ServiceAccounts to cloud IAM identities without keys. Examples are GKE Workload Identity, EKS IAM Roles for Service Accounts (IRSA), EKS Pod Identity, and Azure Workload Identity. The cluster's OIDC issuer URL is registered with cloud IAM, which trusts tokens for specific `namespace/serviceaccount` subjects. Training pods then reach buckets and registries with short-lived credentials. See 4.22 and 5.34 for more. For bare-metal clusters, expose the cluster's OIDC issuer with `--service-account-issuer` and `--service-account-jwks-uri`, and trust it from Vault, AWS or GCP.

Give each workload its own ServiceAccount, and grant it only the RBAC it needs. Workload identity works like a hotel key card issued at check-in. The cloud provider trusts the cluster's signature, so it can hand the pod a card that expires, and nobody has to store a master key inside the hotel.

### Service Account tokens and TokenReview

![A pod sends its ServiceAccount token to a receiving service, which posts a TokenReview to the API server and gets back the authenticated user.](./img/k16-tokenreview.svg)

*Figure 5.16.11. A receiving service asks the API server through TokenReview whether a pod's ServiceAccount token is genuine and whose account it is.*

Every pod runs under a ServiceAccount, and the account gives a group of pods one identity. If no account is assigned, the pod gets the default ServiceAccount of its namespace. Each ServiceAccount has a Secret that holds a JSON Web Token (JWT). Unless you say otherwise, that token is mounted into each pod that uses the account. The pod can then call the Kubernetes API, or other services, with it. The example from *Production Kubernetes* shows the account pointing at its token Secret:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: default
  namespace: default
secrets:
- name: default-token-mf9v2
```

The Secret holds the signed token and a CA certificate, plus annotations that name the account and its unique ID:

```yaml
apiVersion: v1
data:
  ca.crt: <.. SNIP ...>
  namespace: ZGVmYXVsdA==
  token: <.. SNIP ...>
kind: Secret
metadata:
  annotations:
    kubernetes.io/service-account.name: default
    kubernetes.io/service-account.uid: 59aee446-b36e-420f-99eb-a68895084c98
  name: default-token-mf9v2
  namespace: default
type: kubernetes.io/service-account-token
```

Set `serviceAccountName` in the pod spec to choose an account. The Secret's token is then mounted at `/var/run/secrets/kubernetes.io/serviceaccount/`. The application reads it and sends it to other services in the cluster. The receiving service should not trust the token blindly. It checks the token by calling the TokenReview API:

```bash
curl -X "POST" "https://<kubernetes API IP>:<kubernetes API Port>\
/apis/authentication.k8s.io/v1/tokenreviews" \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d $'{
  "kind": "TokenReview",
  "apiVersion": "authentication.k8s.io/v1",
  "spec": {
    "token": "<token to verify>"
  }
}'
```

Think of TokenReview as a bank teller who checks a signature against the account on file. The receiving service hands over the token, and the API server answers two questions: is the token genuine, and whose account does it belong to. The API server replies with the token's metadata and whether it authenticated. A valid token returns something like this:

```json
{
  "kind": "TokenReview",
  "apiVersion": "authentication.k8s.io/v1",
  "metadata": {
    "creationTimestamp": null
  },
  "spec": {
    "token": "<token to verify>"
  },
  "status": {
    "authenticated": true,
    "user": {
      "username": "system:serviceaccount:default:default",
      "uid": "4afdf4d0-46d2-11e9-8716-005056bf4b40",
      "groups": [
        "system:serviceaccounts",
        "system:serviceaccounts:default",
        "system:authenticated"
      ]
    }
  }
}
```

Read the `username` field closely. The prefix tells you the identity is a ServiceAccount. The next two parts are the namespace and the account name, so this caller is the `default` account in the `default` namespace.

Service Account tokens have been part of Kubernetes since early on, and they fit the platform well. The operator keeps tight control, because a token stops working when its ServiceAccount or Secret is deleted. They are a weak identifier in three ways, though. First, a token is scoped to a ServiceAccount. It cannot prove anything finer, such as one pod or one container. Second, your application must call TokenReview through a custom component to verify a caller. Third, a token belongs to one cluster. Using a token from cluster A to identify callers in cluster B means exposing each cluster's TokenReview API and encoding extra cluster metadata. *Production Kubernetes* does not recommend that path for cross-cluster identity.

Create a unique ServiceAccount for each workload that needs API access, so you can grant permissions precisely. If a workload never calls the API, set `automountServiceAccountToken: false` on its ServiceAccount. You can set the same field on the Pod. When both are set, the Pod field wins. Setting it on the namespace's default ServiceAccount is a sound baseline.

### Projected service account tokens (PSAT)

![Two columns compare the long-lived ServiceAccount token with a short-lived audience-bound projected token.](./img/p3-0516-sat-vs-psat.svg)

*Figure 5.16.12. Projected tokens add an expiry, an audience and pod details to the same TokenReview flow.*

*Production Kubernetes* dates projected service account tokens to Kubernetes v1.12. They build on ordinary tokens and fix three weak points: no time to live (TTL), wide scope and long persistence. Before they work, the API server needs a few flags:

```yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --service-account-signing-key-file=/etc/kubernetes/pki/sa.key
    - --service-account-key-file=/etc/kubernetes/pki/sa.pub
    - --service-account-issuer=api
    - --service-account-api-audiences=api
    # Additional flags removed for brevity
    image: k8s.gcr.io/kube-apiserver:v1.17.3
```

The flow for checking identity looks much like the SAT flow. The difference is how the pod gets its token. Instead of reading the automounted token, the pod reads a projected token mounted as a volume. You can set a TTL and a custom audience on that token:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test
  labels:
    app: test
spec:
  serviceAccountName: test
  containers:
  - name: test
    image: ubuntu:bionic
    command: ['sh', '-c', 'echo Hello Kubernetes! && sleep 3600']
    volumeMounts:
    - mountPath: /var/run/secrets/tokens
      name: app-token
  volumes:
  - name: app-token
    projected:
      sources:
      - serviceAccountToken:
          audience: api
          expirationSeconds: 600
          path: app-token
```

The `audience` field stops a receiving application from reusing the token to pose as the caller. The audience should match the destination. Here the destination is the API server itself. Think of the audience as the name written on a ticket. A ticket for one concert does not get you into a different stadium. A PSAT needs a dedicated ServiceAccount. Kubernetes does not mount PSATs for a namespace's default account.

Receiving services still verify the token with TokenReview. With a PSAT, the review also checks that the TTL has not expired. It returns extra data about the calling pod, including its name and UID. That scope is tighter than an ordinary token, which only names the account:

```json
"extra": {
  "authentication.kubernetes.io/pod-name": ["test"],
  "authentication.kubernetes.io/pod-uid":
  ["8b9bc1be-c71f-4551-aeb9-2759887cbde0"]
}
```

The SAT and PSAT flows are nearly the same. The only real differences are the validity and granularity of the identity. The API server also checks the audience, and it rejects a token whose audience does not match its configuration. Projected tokens give you tight integration, configurable TTLs and scope down to individual pods. They also serve as building blocks for stronger patterns. Put simply, a SAT tells you which account is calling, and a PSAT tells you which pod is calling and for how long the token is good.

## 4. Authentication

![A table maps humans, machines and robots to the recommended authentication method and flags static files as avoided.](./img/p3-0516-auth-methods.svg)

*Figure 5.16.13. Use OIDC for people, ServiceAccount tokens for workloads and avoid static credential files.*

A request arrives at the API server from a caller it has never seen before. Before it can decide anything, it needs to know who is asking. Think of authentication as the front desk asking for ID, and authorization as the rules that decide which rooms that ID opens. The API server answers the first question with the methods below. Section 5.5 covers the basics.

Client certificates are one option. The certificate's CN sets the user, and its O field sets the groups. Kubelets use them, and so does the admin kubeconfig from kubeadm. Avoid long-lived admin certificates for humans.

Bearer tokens are another option. These include ServiceAccount JWTs. Static token files are deprecated.

OIDC tokens come from an identity provider such as Dex, Keycloak, Okta or Entra. The `id_token` claims map to a username and groups, through the `--oidc-*` flags or the structured `AuthenticationConfiguration`.

Webhook token authentication hands the check to a cloud IAM authenticator, such as `aws-iam-authenticator` or `gke-gcloud-auth-plugin`. An authenticating proxy relies on front proxy headers, and aggregated APIs use it. Anonymous requests are the last case. Anonymous is the name for a caller that presented no credential. What it can do depends on the RBAC rules you have written for the `system:unauthenticated` group, which is why the warning in section 5 matters.

Humans should authenticate through OIDC SSO with MFA and short-lived tokens. Tools such as `kubelogin`, `kubectl oidc-login` or `kubectl --token` handle that, and the groups from the token map to the groups used by RBAC. Machines use ServiceAccount tokens or federated workload identities. Run `kubectl auth whoami` to see the identity the API server resolved. Run it after any login change. If it shows the identity you expect, the token and the group mapping are working. If it shows an unexpected name, fix that before you start debugging RBAC.

Give humans OIDC login with MFA, and keep machines on ServiceAccount tokens or workload identities.

### Shared secrets: static token and password files

A shared secret is a value that both the caller and the server hold. A database password is one example. Kubernetes offers two static options that use this model for API access. In the first, you give the API server a CSV file that maps usernames, and optionally groups, to static tokens. A client sends the token as a Bearer token in the `Authorization` header. In the second, the CSV maps usernames and optional groups to passwords. The client sends them base64-encoded in the HTTP Basic `Authorization` header. Picture two people holding the same photocopy of a house key. Either one can open the door, and the lock cannot tell them apart. That is the core weakness of a shared secret.

Kubernetes has no User or Group object. Those names exist only for identification in RBAC RoleBindings. The method that authenticates a caller decides who the user is. A static file can map a token to a name, a client certificate can carry the name in its CN, and an OAuth request can supply it as a field. *Production Kubernetes* treats that design as a strength, because it lets the cluster plug in different systems and hand the job to the tool built for it.

*Production Kubernetes* does not recommend either static option. Its reasons are these:

- The token and password files sit in plain text where the API server can read them. A compromised API server node is a bigger problem anyway. The real risk is the repository that holds the setup assets, because it must be secured, audited and kept current.
- Neither the static tokens nor the username and password pairs expire. If one leaks, you must find the breach quickly, remove the credential and restart the API server.
- Any change to these files needs an API server restart. One restart is simple, but many organizations now rebuild and redeploy instead of editing running machines. That makes a restart a heavier action.

The shared secret model has one more problem, outside Kubernetes. An untrusted entity cannot authenticate to a secret store to get an identity in the first place. *Production Kubernetes* calls this the secure introduction problem, and it returns to it later. Put simply, the first credential is the hardest to hand out safely. Every credential after it can be fetched once something is trusted, but something has to be trusted first.

### Client certificates from the CSR flow

![A five-step flow from key and request to an approved certificate in a kubeconfig, with its drawbacks.](./img/p3-0516-csr-lifecycle.svg)

*Figure 5.16.14. Certificates identify users well but cannot be revoked early, so they are not the main login method.*

The PKI model uses certificates and keys to identify users. kubeadm builds that PKI when it creates a cluster, and it gives you a kubeconfig, usually called `admin.conf`, that holds the `kubernetes-admin` user. That file is essentially the root key to the cluster. To see which user it logs in as, decode the `client-certificate-data` field and read it with `openssl`. The output shows the subject `O=system:masters, CN=kubernetes-admin`. The `CN` is the username. Any `O` (Organization) value becomes a group the user belongs to. Think of the `CN` as the name on a badge, and the `O` field as the department printed under it.

To let other users get certificates, the controller manager needs a cluster signing certificate and key. You set `--cluster-signing-cert-file` and `--cluster-signing-key-file` to point at the cluster CA:

```yaml
spec:
  containers:
  - command:
    - kube-controller-manager
    - --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt
    - --cluster-signing-key-file=/etc/kubernetes/pki/ca.key
    # Additional flags removed for brevity
    image: k8s.gcr.io/kube-controller-manager:v1.17.3
```

Any entity with the right RBAC can submit a CertificateSigningRequest (CSR) object to the API. If users should submit their own requests, you need a path for them. Some teams grant the `system:anonymous` user or the `system:unauthenticated` group permission to submit and read CSRs. That is risky. Never let unauthenticated users reach the API server in general. A safer pattern is a thin self-service portal. The portal runs with the permissions it needs, users log in to it with SSO, and it starts the CSR flow for them.

The user can create the private key locally, or the portal can generate it for them. The CSR carries the metadata to encode in the certificate, including the username and any groups. *Production Kubernetes* walks through a request for a user named `john`:

```bash
$ openssl req -new -key john.key -out john.csr -subj "/CN=john"
$ openssl req -in john.csr -text
Certificate Request:
    Data:
        Version: 0 (0x0)
        Subject: CN=john
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (1024 bit)
```

The portal then submits the request as a CertificateSigningRequest object, usually through the API rather than by hand:

```yaml
apiVersion: certificates.k8s.io/v1beta1
kind: CertificateSigningRequest
metadata:
  name: john
spec:
  request: $(cat john.csr | base64 | tr -d '\n')
  usages:
  - client auth
```

The object starts in a `pending` state. It records the base64-encoded request and the requestor. For an automated flow using a pod's ServiceAccount token, the requestor is that ServiceAccount. A portal shows the account it runs under. The request stays unissued until an administrator, or an automated check, approves it. Approval needs care, because it issues a certificate that proves identity. The check must confirm that the submitter is who they claim to be, either with extra identifying metadata or an out-of-band process.

After approval, the portal retrieves the certificate from the CSR `status` field. The user logs back in to pick it up. The approved request looks like this:

```yaml
apiVersion: certificates.k8s.io/v1beta1
kind: CertificateSigningRequest
metadata:
  name: my-app
status:
  certificate: <.. SNIP ...>
  conditions:
  - lastUpdateTime: "2020-03-04T15:45:30Z"
    message: This CSR was approved by kubectl certificate approve.
    reason: KubectlApprove
    type: Approved
```

The decoded certificate carries the identity in its `CN` field, here `john`. You then build a kubeconfig that pairs your private key with the approved certificate in the `client-certificate-data` field. That kubeconfig lets you talk to the API server as `john`.

Some teams automate this, with a system that issues certificates from SSO logins. *Production Kubernetes* has seen teams do this, but it does not recommend this as the main authentication method, for several reasons:

- Certificates from the CSR flow cannot be revoked before they expire. Kubernetes has no certificate revocation list or OCSP stapling support.
- You must run and maintain extra PKI, plus a component that issues certificates from external logins.
- Certificates should have short lifetimes, so that a leaked key-and-certificate pair does not last long. Short lifetimes cause high churn, and new certificates must reach users regularly.
- You must verify who is asking for each certificate. Automation can do that with external metadata. Without it, out-of-band checks are too slow, especially with short lifetimes.
- Each certificate works in one cluster only. Teams often run 10 to 100 clusters, so unique credentials per cluster multiply the work and degrade the user experience.

Keep `admin.conf` in a secure place even when you use other login methods. If those methods fail, it is the break-glass path into the cluster. Think of it as the spare key kept under the mat. You hope you never need it, and you keep it safe so you can get back in when every other door is locked.

### OIDC for robot users and kubeconfig generation

OIDC is the preferred choice for humans. Most organizations already run an SSO system, such as Okta, Auth0, Google or an internal LDAP or AD directory. Using it gives one place to manage accounts and remove access. It also lets users reach downstream applications without exposing their credentials to them. Many clusters can share one identity provider, which reduces differences between them.

Kubernetes accepts OIDC directly, and configuring it is straightforward when your provider exposes the standard endpoints. Some cases need more tooling. If you have several identity providers, you need an OIDC aggregator, because Kubernetes supports only one provider in its configuration. Dex, a sandbox project of the Cloud Native Computing Foundation, appears in many of these setups. Keycloak and UAA offer similar features. Authentication sits on the critical path to the cluster, so optimize for availability and stability. Each of these tools is one more component to configure, update and secure.

OIDC gives you a token, not a kubeconfig. Someone has to turn that token into a usable kubeconfig. The *Production Kubernetes* authors built a web UI called Gangway for this. It logs in through an OIDC provider and generates a valid kubeconfig from the returned token, with the right endpoints and certificates.

OIDC also has a limit. The specification requires users to log in through the provider's own web page, so the credentials never reach the consuming application. Think of a web login as a doorman who checks a face. A robot cannot stand at that door, so it needs a different kind of pass. Robot users, such as CI/CD systems, cannot answer a web login challenge. *Production Kubernetes* describes three answers:

- If robot users are tied to centrally managed accounts, write a `kubectl` authentication plug-in. It logs in to the external system and receives a token. Kubernetes then verifies that token through the webhook token authenticator. This takes custom code for the token generator and webhook server.
- For robot accounts that need no central management, use certificate-based authentication. You must then manage certificate issuance and rotation yourself, but no custom component is needed.
- The simplest option is a ServiceAccount for the tool. Use the token it generates. In-cluster tools receive that credential mounted in their pod. Tools outside the cluster need the token copied to a secure location they can read. ServiceAccounts are covered in more detail above.

## 5. RBAC

![A Role with four rules and a RoleBinding naming a group and a ServiceAccount, with allowed and denied examples.](./img/p3-0516-trainer-runner-walk.svg)

*Figure 5.16.15. The Role lists permissions and the binding gives them to subjects only in its own namespace.*

A new engineer joins team A and needs to read training logs, but must not be able to delete another team's jobs. Writing that rule is what RBAC is for. Each rule answers one question: who can do which verb to which resource, and where. RBAC decides whether a request proceeds. It authorises requests by verbs on resources within namespaces. Four API objects do the work, and the table compares them.

| Object | Scope | Meaning |
|---|---|---|
| `Role` | Namespace | Set of allowed rules in that namespace |
| `ClusterRole` | Cluster | Rules for cluster-scoped resources (nodes, PVs, CRDs), non-resource URLs (`/healthz`, `/metrics`), or reusable across namespaces |
| `RoleBinding` | Namespace | Grants a Role or ClusterRole's permissions to subjects **within that namespace** |
| `ClusterRoleBinding` | Cluster | Grants a ClusterRole's permissions cluster-wide |

A binding's subjects can be a `User`, a `Group` or a `ServiceAccount`. Each rule names `apiGroups`, `resources`, and `verbs`. It can add `resourceNames` to restrict it to specific objects, or `nonResourceURLs`. Resources can include subresources such as `pods/exec`, `pods/log`, `pods/eviction`, `nodes/proxy` and `deployments/scale`. The verbs are `get`, `list`, `watch`, `create`, `update`, `patch`, `delete` and `deletecollection`. The special verbs are `impersonate`, `bind`, `escalate`, `approve`, `sign` and `use`.

Think of a Role as a list of allowed actions, and a RoleBinding as the act of handing that list to someone. The list does nothing until someone holds it. The Role and RoleBinding below show how those parts fit together.

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

Notice that the RoleBinding names an OIDC group and a ServiceAccount from another namespace.

Read the Role rule by rule. The first rule lets the trainer read pods and their logs, which covers debugging a stuck run. The second lets it manage Jobs. The third gives full control over PyTorchJobs, because the verb `*` means every verb. The fourth allows only one named ConfigMap, `trainer-config`, and nothing else. The binding then hands that role to one OIDC group and to a CI ServiceAccount in another namespace. The rule set is short, but its effect is precise, and precision is the goal.

### Why RBAC matters and how a request is checked

![A request is first authenticated to establish who is calling, then authorized by RBAC on identity, resource and verb, with a 403 for a failed check.](./img/p2-0516-rbac-check.svg)

*Figure 5.16.16. A request first passes authentication to find the caller, then RBAC checks the identity, resource and verb, and a failed check returns HTTP 403.*

Think of RBAC as the badge reader at each door of a lab. Every request has to show a card, which is authentication. The reader then checks whether that card opens that room for that action, which is authorization. Role-based access control, or RBAC, is a mechanism for restricting both access to and actions on Kubernetes APIs. Its job is to make sure only authorized users get through. It is a critical part of hardening the cluster where you deploy your application. It also prevents unexpected accidents. Picture one person working in the wrong namespace who mistakenly takes down production while believing they are clearing out their test cluster.

Every request to the API passes through two checks. Authentication comes first, and it establishes who is calling. The caller might be a user, a ServiceAccount, or no identity at all. Authorization comes second. It combines the identity, the resource (the HTTP path) and the verb, then decides whether the action may proceed. If the check fails, the caller gets an HTTP 403 error.

A simple way to say it is that RBAC decides who can ask, not what the answer does. A pod that is allowed to run may still run code that reaches further than its author meant, which is why isolation and admission rules sit beside RBAC. RBAC is one layer of defense, not the whole defense. Anyone who can run arbitrary code inside the cluster can effectively gain root on the entire cluster. A correct RBAC setup makes that harder and more expensive. For hostile multitenant workloads, you must also isolate the Pods themselves, usually with hypervisor-isolated containers or a container sandbox.

> **Warning:** By default, the API server installs a ClusterRole that lets `system:unauthenticated` users reach API discovery. On a cluster exposed to the public internet, that is a poor choice, and at least one serious vulnerability has come from it. If your cluster faces a hostile environment, set `--anonymous-auth=false` on the API server.

### Verbs and HTTP methods

![A Role grants a set of verbs on a resource, so a monitoring agent that holds only list and watch is denied when it tries to create a Pod.](./img/p2-0516-rbac-verbs-rule.svg)

*Figure 5.16.17. A monitoring agent with only list and watch on pods is refused when it tries to create a pod, because a Role grants only the verbs it names.*

![RBAC verbs mapped to HTTP methods, where get, list and watch all use GET, and a monitoring agent needs only list and watch.](./img/p2-0516-verb-map.svg)

*Figure 5.16.18. RBAC verbs roughly match HTTP methods, but get, list and watch all use GET, so a monitoring agent needs only list and watch.*

A Role grants a verb on a resource. Verbs match HTTP methods roughly, so you can reason about them from the API calls you already know. The commonly used verbs appear in this lookup table.

| Verb | HTTP method | Meaning |
|---|---|---|
| `create` | `POST` | Create a new resource. |
| `delete` | `DELETE` | Delete an existing resource. |
| `get` | `GET` | Get a resource. |
| `list` | `GET` | List a collection of resources. |
| `patch` | `PATCH` | Modify an existing resource via a partial change. |
| `update` | `PUT` | Modify an existing resource via a complete object. |
| `watch` | `GET` | Watch for streaming updates to a resource. |
| `proxy` | `GET` | Connect to a resource via a streaming WebSocket proxy. |

Notice that `get`, `list` and `watch` all show up as `GET`. The HTTP method alone does not tell you what the caller can see. Start each Role from the smallest verb set the workload needs. A monitoring agent, for example, needs `list` and `watch` on pods to see what is running. It does not need `create`, `update` or `delete`. Writing down only the verbs you need makes a later audit short.

### Properties

![A grid shows how Role and ClusterRole combine with RoleBinding and ClusterRoleBinding to set scope.](./img/p3-0516-role-binding-scope.svg)

*Figure 5.16.19. A RoleBinding limits even a ClusterRole to one namespace.*

RBAC is additive only. There are no deny rules, so the permissions are the union of all bindings. A user with `edit` cannot be denied one verb, except by removing the binding or by using an admission policy. Think of RBAC bindings as keys on a ring. Adding a key only opens more doors, and no key says "not this door." If you need to take access away, you take a key off the ring.

A binding's `roleRef` cannot be changed. To point a binding at a different role, delete it and create it again.

The default roles are `cluster-admin`, which can do everything, and `admin`, which is a namespace admin including RBAC within the namespace. `edit` reads and writes most objects, but not roles or bindings. It can read secrets and run pods, so in practice it gives access to namespace ServiceAccount tokens. `view` reads most objects but not secrets. System roles include `system:node`, `system:kube-scheduler`, `system:discovery`, `system:public-info-viewer` and `system:basic-user`.

*Kubernetes: Up and Running* (3rd edition, Chapter 14) notes that `kube-apiserver` automatically reconciles built-in `ClusterRole` objects on startup. It overwrites any manual edit, unless you first set the annotation `rbac.authorization.kubernetes.io/autoupdate: "false"` on the `ClusterRole`.

Aggregation works through labels. ClusterRoles with an `aggregationRule` collect rules from other ClusterRoles that carry a matching label, such as `rbac.authorization.k8s.io/aggregate-to-edit: "true"`. CRD authors ship ClusterRoles with those labels to extend `view/edit/admin` with their custom resources, such as Kueue or Argo.

Several built-in groups exist: `system:authenticated`, `system:unauthenticated`, `system:serviceaccounts`, `system:serviceaccounts:<ns>` and `system:masters`. `system:masters` is unrestricted and bypasses RBAC, so avoid it in certificates.

Escalation prevention is the next concern. You cannot create or update a Role or binding that grants permissions you do not hold, unless you have the `escalate` or `bind` verb on roles. The `impersonate` verb lets you act as someone else. A `create` on `pods` is powerful. It implies reading any Secret or ServiceAccount token in that namespace by mounting it, and it can reach node access through hostPath or privileged pods. A `create` on `pods/exec` gives you a shell in pods. `nodes/proxy` gives you kubelet API access, which means exec on any pod on the node. A `get` on `secrets` gives you credentials, and a `create` on `serviceaccounts/token` mints tokens. A practical reading of this list is that creating a Pod in a namespace is close to owning that namespace. You can usually reach whatever that Pod can mount or run as, which is why a grant on `pods` deserves the same review as a grant on `secrets`. Wildcard verbs or resources, and `cluster-admin` bindings to groups such as `system:authenticated`, are never appropriate. Updating `validatingwebhookconfigurations` or `mutatingwebhookconfigurations`, or CRDs, can disrupt the cluster. A `get` or `list` on `secrets` cluster-wide amounts to a cluster compromise.

### Design patterns for AI platforms

The patterns below cover the common cases on a shared GPU cluster. Decide who owns each namespace and each CRD before you write any role. Picture a shared GPU cluster with many research teams. The question is not "what can a role do?" but "who owns what, and what is the smallest set of roles that lets each team work?" The list below answers that question one pattern at a time.

1. Give each team a namespace per team or project. Bind OIDC groups to `edit` or custom roles per namespace. Only platform admins should get cluster-scoped write access.
2. Tailor roles to each workflow. Examples include `job-submitter`, which can create and delete Jobs, PyTorchJobs and LocalQueue workloads. It can read pods, logs and events, but it gets no secrets and no exec in prod. Other examples are `notebook-user`; `inference-deployer`, which manages Deployments, Services, HPA and InferenceService objects; `viewer`, which gets view and metrics; and `queue-admin`, which edits Kueue ClusterQueues for team leads through a ClusterRole and a RoleBinding that scope the access.
3. Give operators and controllers only the minimum cluster permissions they need. Generate those from kubebuilder markers and review them. Use a separate ServiceAccount for each controller, and use `resourceNames` wherever you can.
4. CI/CD identities should be namespaced ServiceAccounts or federated identities, which apply only into their own namespaces. Pipelines should never get cluster-admin. Argo CD and Flux projects restrict destinations (4.26).
5. Break-glass access should be time-bound and granted through a controlled process. An example is a temporary RoleBinding made by an access broker, or `kubectl create token` for a break-glass ServiceAccount, with audit logging. Humans should not hold permanent cluster-admin.
6. Separate duties clearly. The platform team owns CRDs, webhooks, policies and nodes. App teams own namespace content.
7. Pod Security and admission policy complement RBAC. RBAC says who can create pods. Pod Security Admission (PSA), Kyverno or ValidatingAdmissionPolicy says what pods may look like (5.21).
8. Give observability its own read access. A dedicated ClusterRole for Prometheus can `get`, `list` and `watch` pods, nodes, endpoints and services, plus the `/metrics` non-resource URL. Avoid `nodes/proxy` where possible. Use dedicated metrics endpoints, or the kubelet `/metrics` with `nodes/metrics` only.
9. Multi-tenant inference platforms usually give end users no Kubernetes RBAC at all. Users call an API gateway with API keys or JWTs (5.12). Kubernetes RBAC is for engineers and automation.
10. Store RBAC as code with owners, using CODEOWNERS. Review diffs before they merge. Reconcile declaratively with `kubectl auth reconcile -f some-rbac-config.yaml`, which supports `--dry-run`, as shown in *Kubernetes: Up and Running* Chapter 14. Run an access review regularly with `kubectl-who-can`, `rbac-tool`, `rakkess`, `kubectl auth can-i --list`, `rbac-lookup`, KubiScan, or the Kubescape, Polaris and Trivy RBAC checks.

### Least-privilege admin elevation via RBAC `impersonate` (`sudo`-style workflow)

![An ops-team operator reads by default, is refused a write, and gains cluster-admin rights for one command with --as=cluster-admin.](./img/k16-impersonate-sudo.svg)

*Figure 5.16.20. Operators get read-only rights by default and raise to cluster-admin for one command with the impersonation flag, which the audit log records.*

Binding `cluster-admin` straight to an operator's daily identity invites accidents. An engineer with the wrong `kubeconfig` context active can run destructive commands with full rights. *Production Kubernetes* Chapter 10 recommends a `sudo`-style privilege-elevation pattern, built on Kubernetes user impersonation. It works in three steps:

1. By default, bind the operations group, `ops-team` in this example, to the built-in read-only `view` `ClusterRole`, through `cluster-admin-view`.
2. Bind the `cluster-admin` `ClusterRole` to a synthetic `User` named `cluster-admin`, through `cluster-admin-crb`. No human can log in as that user directly.
3. Grant `ops-team` a `cluster-admin-impersonator` `ClusterRole`. It has `verbs: ["impersonate"]` on `resources: ["users"]`, restricted to `resourceNames: ["cluster-admin"]`.

Think of this as a `sudo` rule for the cluster. Daily work runs with reader rights, and a deliberate command raises the rights for one action. The three RBAC manifests look like this:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-admin-view
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: Group
    name: ops-team
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-admin-crb
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: User
    name: cluster-admin
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-admin-impersonator
rules:
  - apiGroups: [""]
    resources: ["users"]
    verbs: ["impersonate"]
    resourceNames: ["cluster-admin"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-admin-impersonate
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin-impersonator
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: Group
    name: ops-team
```

With this in place, an operator named `john`, who belongs to `ops-team`, has read-only access by default. A write requires an explicit `--as=cluster-admin`. Both the real user and `impersonatedUser` then appear in the Kubernetes audit log:

```bash
kubectl get configmaps
# No resources found.
kubectl create configmap my-config --from-literal=test=test
# Error from server (Forbidden): configmaps is forbidden: User "john" cannot create resource "configmaps" in API group "" in the namespace "default"
kubectl --as=cluster-admin create configmap my-config --from-literal=test=test
# configmap/my-config created
```

Read those four commands as a short story. The first read returns nothing, which is not an error, because the namespace is empty. The second write is refused, because `john` has only read rights. The third succeeds, because `--as` asks the API server to act as `cluster-admin`, and the impersonation rule allows that. Each step leaves a line in the audit log, so the trail shows who asked for the elevation and what they did with it.

Kubernetes has no group object. The `ops-team` group is a set of attributes that the identity carries, such as an x509 certificate field or an OIDC claim. Because of that, the three steps above work with whatever identity method you chose. Give every team the same shape: a group, a read-only view role, and a separate admin user that only members can impersonate. This removes many costly mistakes. Impersonation also shows up in the audit log. You can see the original user log in, impersonate `cluster-admin`, and then act. That gives you a trail of who actually did what.

Impersonation needs its own permission. An impersonated user is denied when the caller lacks the `impersonate` verb on users, groups or service accounts. The impersonation pattern resembles `sudo` on Linux. Users see everything by default, and they must elevate on purpose to write. That deliberate step cuts the chance of an accident from the wrong kubeconfig.

### Testing and auditing RBAC

![A ladder of RBAC questions each paired with the kubectl or plugin command that answers it.](./img/p3-0516-rbac-testing-ladder.svg)

*Figure 5.16.21. Run these checks on a quiet day so an overbroad role is found before an incident.*

These commands test what an identity can do, and they help reveal bindings that grant too much access.

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

Run these commands before you need them. A `can-i` check on a quiet afternoon is cheap. Finding out that a role is too broad in the middle of an incident is not. Audit logging, covered in 5.5, records `authorization.k8s.io/decision` and the reasons for it. Alert on `create` of ClusterRoleBindings, `exec` into production pods, secret reads by unusual identities, and token creation.

### Managing RBAC at scale

Once you orient to the basics of role-based access control, managing access to a cluster becomes relatively easy. But when you manage a large number of users or roles, you need additional advanced capabilities to manage RBAC at scale. Testing, aggregation and version control keep the rules readable as the team grows.

Some actions are subresources, such as reading logs or opening a port-forward. You can test them with the `--subresource` flag. The check below asks whether the current user may read logs from Pods:

```bash
$ kubectl auth can-i get pods --subresource=logs
```

RBAC objects are YAML, just like every other Kubernetes resource. Store them in version control, and you gain accountability, auditability and rollback. The `kubectl auth reconcile` command works somewhat like `kubectl apply`. It reconciles a set of roles and role bindings with the cluster state:

```bash
$ kubectl auth reconcile -f some-rbac-config.yaml
```

To see changes before they happen, add `--dry-run`. The command then prints what it would change, but it does not apply the changes. Run this check in your pipeline before any RBAC change merges.

## 6. Configuration management patterns for AI workloads

## 6. Configuration management patterns for AI workloads

A training job's settings come from several places at once: the image, a ConfigMap, the job spec and a Secret. Knowing how they stack saves a lot of debugging. Picture a training run that starts with one learning rate but behaves as if it had another. The cause is usually a setting in a layer that nobody checked. Working through the layers below, from the bottom up, is the fastest way to find it.

- Settings stack from image defaults, to a ConfigMap at the cluster or environment level, to per-job overrides through env or args, and finally to secrets for credentials. Keep model hyperparameters in versioned config files, in Git, MLflow or W&B, rather than in ad-hoc env vars. Mount them at read-only paths.
- Operators such as the Training Operator and MPI Operator write hostfiles and env. Avoid per-pod ConfigMaps at scale. If you need them, use `immutable` and TTL cleanup. A Job's `ttlSecondsAfterFinished` cleans up its pods, but owned ConfigMaps need ownerReferences.
- Feature flags live in a ConfigMap and drive rollouts. Trigger those rollouts with a hash, and keep the flags in GitOps.
- Large artefacts, such as model weights and tokenizers, belong on a PVC, in object storage or in an OCI image volume, not in ConfigMaps.
- Use Kustomize overlays or Helm values for each environment. Secrets come through ESO references that differ per environment, while the manifests stay identical.
- Schema-validate your config with JSON Schema, or with pydantic in the app. Run `kubeconform` on manifests (4.13). Add startup self-checks that fail fast with clear messages.
- `LimitRange`, `ResourceQuota`, default `PriorityClass` and default `StorageClass` mean some config choices come from the platform (5.22).

Decide which layer owns each setting before you add one more env var.

## 7. Failure modes and troubleshooting

![A table maps eight symptoms in configuration, secrets and RBAC to causes and fixes.](./img/p3-0516-failure-ladder.svg)

*Figure 5.16.22. Start from the symptom column to decide which command to run next.*

Your first sign of trouble is usually a symptom, not a cause. The table maps common symptoms to their likely causes and fixes. Check the symptom column first, because it tells you which command to run next. Read each row as a short diagnosis: the symptom you see, the cause that usually produces it, and the first fix to try. If the cause is not obvious, go back to the symptom and inspect the object it names with `describe` or `auth can-i`.

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

## 8. Lab

Start with the self-checking Python lab, `code/part05/rbac_secrets_validator_lab.py`, and run it locally. Run it before you touch a cluster. It checks the logic of the key validator, the rotation simulator and the escalation auditor on your own machine, so a failure there points at the code, not at the cluster. It checks three things. It verifies the `ConfigMap`/`Secret` key syntax validator, `validate_configmap_or_secret_key`, which follows *Kubernetes: Up and Running* Chapter 13. It verifies the `EncryptionConfiguration` key-rotation simulator, `simulate_etcd_encryption_key_rotation`, which follows *Production Kubernetes* Chapter 7. It also verifies the RBAC `impersonate` `sudo`-workflow and privilege-escalation auditor, `evaluate_rbac_and_audit_escalations`, which follows *Kubernetes: Up and Running* Chapter 14 and *Production Kubernetes* Chapter 10.

```bash
python3 code/part05/rbac_secrets_validator_lab.py
```

Next, work through these exercises on a `kind` or `kubeadm` cluster. The interactive shell steps below were not run on live hardware.

1. Mount a ConfigMap as an env var, as a volume, and with `subPath`. Change it, and measure which mounts update and how long they take. Then use `immutable` and a hashed-name generator to roll deployments.
2. Create a Secret and read it back with `kubectl get -o yaml | base64 -d`. Then read it from etcd with `etcdctl`, where it appears in plaintext. Enable `EncryptionConfiguration` with a local `aescbc` key for the lab, or with a KMS plugin. Verify the `k8s:enc:` prefix, and re-encrypt the existing secrets.
3. Show a Secret read through an env var in `/proc/1/environ`, through `kubectl exec`, through the `pods/exec` permission, and through the node at `/var/lib/kubelet/pods/*/volumes`. Then decide on mitigations.
4. Deploy Vault dev and External Secrets Operator. Sync a Vault KV into a Secret, rotate the value in Vault, and observe the refresh and the consumer reload with Reloader. Try the Secrets Store CSI driver as an alternative.
5. Encrypt a Secret for Git with Sealed Secrets or with SOPS and age. Deploy it through GitOps, then verify that the plaintext never appears in Git or logs.
6. Inspect a pod's projected token and decode the JWT claims: `aud`, `exp` and `kubernetes.io`. Create a token with a custom audience, and call the API with it. Delete the pod and show that the token is invalidated. Then show `automountServiceAccountToken: false`.
7. Configure the cluster OIDC issuer and trust it from a cloud provider or Vault. Have a pod obtain short-lived cloud credentials without secrets. Verify bucket access, then revoke it by removing the binding.
8. Create a `job-submitter` Role and bind it to a test user or group, using certificates or impersonation. Verify `can-i` for allowed and denied actions. Add aggregation through a labelled ClusterRole that extends `view` with a CRD.
9. As a user with `create pods` in a namespace, mount another ServiceAccount's token, or run privileged if PSA is absent. Demonstrate it. Then block it with Pod Security Admission and RBAC tightening.
10. Run `rbac-tool`, `rakkess`, `kubectl-who-can` or Kubescape against the cluster. List dangerous bindings, such as `system:authenticated`, wildcards and `nodes/proxy`, and then remediate them.
11. Enable an audit policy. Perform secret reads, exec and RoleBinding changes, then query the logs to reconstruct what happened. Write alerts from what you find.
12. Implement a time-bound elevation, such as a temporary RoleBinding created by a controller or script that expires. Test it, then review the audit trail.
13. Clean up.

## 9. Common mistakes

![Six RBAC grants radiate toward cluster-admin with the reason each one is an escalation path.](./img/p3-0516-escalation-paths.svg)

*Figure 5.16.23. Create pods, exec, secret reads, nodes proxy, escalate, bind and impersonate can each lead to full control.*

Most secret and RBAC incidents are not exotic. Someone copied a convenient setting from an old example, and it stayed in place for months. This list collects the mistakes the chapter has warned about.

- Believing that Secrets are encrypted is a mistake, and so is storing real secrets in Git or ConfigMaps. Printing secrets from env vars into logs is another.
- Granting `list/watch` on secrets cluster-wide, to monitoring or `view` roles, is a mistake.
- Using `cluster-admin` for CI/CD, operators or developers is a mistake. So is binding roles to `system:authenticated`.
- Forgetting that `create pods` is roughly equivalent to reading secrets and tokens in the namespace leads to trouble. So does allowing `pods/exec` in prod.
- Using the `default` ServiceAccount with extra permissions is a mistake, and so is leaving token automount on everywhere.
- Relying on env-var ConfigMap changes to propagate is a mistake. Using `subPath` for configs that must reload is another.
- Using long-lived static credentials instead of workload identity is a mistake, and so is sharing credentials across teams.
- Not rotating secrets or keys is a mistake. So is skipping re-encryption after you enable KMS.
- Skipping audit review of RBAC lets roles accumulate wildcards over time.
- Treating RBAC as sufficient, without an admission policy for pod security or namespace quotas, leaves gaps.

Pick the bullet that matches your cluster, and check it first.

## 10. Interview angles

Interviewers often start with a simple question and listen for the follow-up. Each question below has a short answer and a longer one hiding behind it. Use these questions to test your understanding of the chapter.

- "Are Kubernetes Secrets secure? How do you protect them?"
- "ConfigMap env vs volume: update behaviour? What is `immutable`?"
- "Explain Role, ClusterRole, RoleBinding, ClusterRoleBinding; can a RoleBinding reference a ClusterRole?"
- "What ServiceAccount token changed in 1.22/1.24? What is a bound token?"
- "How do pods access cloud storage without keys?" (workload identity.)
- "Name RBAC permissions that are effectively cluster-admin."
- "How would you design access for 20 research teams on a shared GPU cluster?"
- "How do you keep secrets out of Git and rotate them safely?"

## Exercises

1. A team's trainer picks up some config changes and misses others. Work through the cause, using the key naming rules from *Kubernetes: Up and Running* Chapter 13 and the live-update behavior of each mount type.
Using `validate_configmap_or_secret_key()` in `code/part05/rbac_secrets_validator.py`, explain why `.auth_token`, `Key.pem` and `config_file` are valid keys.
Then explain why `Token..properties`, `auth file.json` and `_password.txt` are rejected.
Explain how `$(VAR)` substitution works in `command` and `args`.
Explain why volume-mounted ConfigMaps update through the `..data` symlink swap.
Explain why env vars and `subPath` mounts do not update.
Finally, explain why `immutable: true` reduces kubelet and API server watch load.
2. A cluster owner plans to rotate an encryption key. Before the change, work through the reasoning with *Production Kubernetes* Chapter 7 in hand.
Compare KMS v2 with `secretbox` in `EncryptionConfiguration`, and review safe key rotation.
Using `simulate_etcd_encryption_key_rotation()` in `code/part05/rbac_secrets_validator.py`, explain why Secrets are stored as plaintext base64 in `etcd` by default.
Explain how `EncryptionConfiguration` orders providers and keys.
Then explain why removing `secret-key-1` before running `kubectl get secrets -A -o json | kubectl replace -f -` breaks existing Secrets.
Include the error text `unable to transform key` in your answer.
3. Your team is choosing how to get secrets into GitOps safely. Work through the options before you pick one.
Compare the 6 GitOps-safe secret patterns in Section 2.
Trace the `vault.hashicorp.com/agent-inject-*` annotations and the Go template from *Production Kubernetes* Chapter 7.
Then write the 4 `vault` CLI commands that configure Vault's Kubernetes `TokenReview` auth method for ServiceAccount `team-a/webapp`.
4. A pod needs a token, a CA bundle and its labels, and the platform team wants no static keys at all. Trace how the pieces fit together.
Trace the `projected` volume from Section 3, including the `serviceAccountToken` source with `audience: vault` and `expirationSeconds: 3600`.
Then trace the `configMap` source and the `downwardAPI` source in the same volume.
Explain how bound JWT tokens from the `TokenRequest` API differ from the legacy never-expiring Secret tokens removed in 1.24.
Then explain how OIDC workload identity federation eliminates static cloud keys.
5. Many research teams share one cluster, and each team needs its own boundaries. Design the RBAC with the pieces from *Kubernetes: Up and Running* Chapter 14.
Design multi-tenant RBAC using `Role`, `ClusterRole`, `RoleBinding`, `ClusterRoleBinding`, aggregation and `autoupdate: "false"`.
Explain how a `RoleBinding` in `team-a` that references a `ClusterRole` keeps permissions strictly inside `team-a`.
Explain how an `aggregationRule` extends built-in roles with CRDs such as `PyTorchJob` and `LocalQueue`, using the label `rbac.authorization.k8s.io/aggregate-to-edit: "true"`.
Explain how `kubectl auth reconcile -f` works.
Explain how `kubectl auth can-i --subresource=logs` works.
Finally, explain why `rbac.authorization.kubernetes.io/autoupdate: "false"` is needed when you customize built-in ClusterRoles.
6. A security reviewer asks which RBAC grants could lead to cluster-admin. Work through the answer.
Audit the RBAC escalation paths: `create pods`, `pods/exec`, `nodes/proxy`, `escalate`, `bind` and `impersonate`.
Also study the `sudo`-style impersonation pattern from *Production Kubernetes* Chapter 10.
Using `evaluate_rbac_and_audit_escalations()` in `code/part05/rbac_secrets_validator.py`, explain why `create` on `pods` is an escalation vector.
Explain why `get/list/watch` on `secrets` is one too.
Explain why `nodes/proxy` is one as well.
Then trace the 4 RBAC manifests: `cluster-admin-view`, `cluster-admin-crb`, `cluster-admin-impersonator` and `cluster-admin-impersonate`.
Explain why they require engineers to pass `--as=cluster-admin` for write operations.

## Checkpoint questions (20)

<details>
<summary>1. In *Kubernetes: Up and Running* Chapter 13, what are the syntax rules for keys inside a `ConfigMap` or `Secret`, and how do you reference a ConfigMap env var inside a container's `command` or `args`?</summary>

- **Key syntax rules:** A key may start with one optional dot (`.`). It then needs a letter or number (`[a-zA-Z0-9]`), followed by any mix of letters, numbers, dots, dashes (`-`) and underscores (`_`). Keys cannot contain spaces (`auth file.json`) or double dots (`Token..properties`), and they cannot start with an underscore (`_password.txt`).
- **Referencing env vars in `command` / `args`:** Use Kubernetes's own `$(VAR_NAME)` syntax. It is not `$VAR_NAME` or `${VAR_NAME}`, which need a shell. For example: `args: ["--log-level=$(LOG_LEVEL)"]`.
</details>

<details>
<summary>2. Compare what happens when you update a `ConfigMap` or `Secret` that is consumed via (a) `env` / `envFrom`, (b) a directory `volumeMount`, and (c) a `subPath` `volumeMount`.</summary>

1. **`env` / `envFrom`:** Environment variables are injected only when the container is created. They never update while the container runs, so the pod needs a rollout or restart.
2. **Directory `volumeMount` (`mountPath: /etc/trainer`):** The kubelet syncs the volume within ~60–120 seconds. It performs an atomic symlink swap of the `..data` directory, which updates all mounted files in place without restarting the container.
3. **`subPath` `volumeMount` (`subPath: hparams.yaml`):** Linux bind-mounts the original file inode directly, so a `subPath` mount never receives updates when the ConfigMap or Secret changes.
</details>

<details>
<summary>3. What are the two benefits of setting `immutable: true` on a `ConfigMap` or `Secret`?</summary>

1. **Safety against accidental live mutation:** `kube-apiserver` rejects any `PUT` or `PATCH` that tries to modify `data`, `binaryData` or `immutable`. To change the config, create a new versioned ConfigMap name, such as `trainer-config-v2`, and roll the Deployment.
2. **Control-plane scalability on 5,000-node clusters:** Once `kubelet` sees `immutable: true` on a mounted ConfigMap or Secret, it closes its watch or poll on that object. That cuts `kube-apiserver` watch load across thousands of nodes.
</details>

<details>
<summary>4. Why is a default Kubernetes `Secret` no more confidential in `etcd` than a `ConfigMap`, and what five controls actually protect Secrets?</summary>

Base64 is only an encoding. `Secret.data` values are merely base64-encoded (`echo "..." | base64 -d`), so binary bytes can be represented in JSON and YAML. They are persisted in `etcd` as unencrypted cleartext. Real protection takes five controls:
1. Encryption at rest in `etcd`, using `EncryptionConfiguration` with a KMS v2 provider.
2. Least-privilege RBAC. Never grant cluster-wide `get`, `list` or `watch` on `secrets` to `view` or monitoring roles, because `list` or `watch` on `secrets` returns the full secret payloads of every Secret.
3. Read-only file mounts, with `defaultMode: 0400` and a `tmpfs` memory volume, rather than environment variables. Env vars leak into `/proc/<pid>/environ`, crash dumps and child processes.
4. External secret stores (`ESO`, `Secrets Store CSI Driver`, `Vault Agent Injector`), so plaintext secrets never enter Git.
5. Keyless, short-lived identities (`Workload Identity` or projected tokens) whenever the target service supports OIDC or IAM.
</details>

<details>
<summary>5. In *Production Kubernetes* Chapter 7, how does `EncryptionConfiguration` order providers and keys, and what is the exact procedure to rotate an encryption key without breaking existing Secrets?</summary>

`kube-apiserver` always uses the first provider, and the first key inside it, to encrypt new writes. It uses all listed providers and keys, in order, to decrypt existing objects on read. To rotate from `secret-key-1` to `secret-key-2`, follow these steps from *Production Kubernetes* Chapter 7:
1. Add `secret-key-2` below `secret-key-1` on all API servers. If the API servers restart one at a time, every server can already decrypt `secret-key-2` before any server starts writing with it.
2. Move `secret-key-2` to the first position, keep `secret-key-1` second so existing Secrets stay readable, and restart the `kube-apiserver` instances.
3. Re-encrypt all existing Secrets in `etcd` with `secret-key-2`: `kubectl get secrets --all-namespaces -o json | kubectl replace -f -`
4. Remove `secret-key-1` from `EncryptionConfiguration`.
</details>

<details>
<summary>6. Compare the `External Secrets Operator` (`ESO`), the `Secrets Store CSI Driver`, and the `HashiCorp Vault Agent Injector` in *Production Kubernetes* Chapter 7.</summary>

- **External Secrets Operator (`ESO`):** A controller watches `ExternalSecret` CRs and fetches secret values from AWS, GCP or Azure Secret Manager, or from Vault. It creates native Kubernetes `Secret` objects. Consumption is simple, through standard `secretKeyRef` or volumes. The secret payload is still stored in `etcd`.
- **Secrets Store CSI Driver (`secrets-store.csi.k8s.io` with `SecretProviderClass`):** A node-level CSI driver fetches secrets straight from Vault or a cloud KMS, and mounts them into the pod as an in-memory volume. It creates no Kubernetes `Secret` in `etcd`, unless secret syncing is enabled.
- **HashiCorp Vault Agent Injector:** A mutating admission webhook adds a `vault-agent-init` init container and a `vault-agent` sidecar, based on `vault.hashicorp.com/agent-inject-*` annotations. The pod authenticates with its ServiceAccount JWT, checked through the `TokenReview` API. Dynamic or leased templates, such as JDBC strings, are rendered into an in-memory `emptyDir` at `/vault/secrets/`, without touching `etcd`.
</details>

<details>
<summary>7. How did Kubernetes `ServiceAccount` tokens change in Kubernetes 1.22 and 1.24 (`TokenRequest` bound tokens vs. legacy Secret tokens)?</summary>

- **Legacy tokens (before 1.22, with auto-creation removed in 1.24):** Creating a `ServiceAccount` also created a `Secret` of type `kubernetes.io/service-account-token`. That Secret held a static JWT with no expiration (`exp` omitted) and no audience restriction, stored permanently in `etcd`. If it leaked, it stayed valid until someone deleted the Secret.
- **Bound ServiceAccount tokens (the default from 1.22 onward, through the `TokenRequest` API and a `projected` volume):** The token mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token` is a short-lived JWT, lasting ~1 hour. The kubelet rotates it automatically at 80% of its lifetime. It is audience-bound, and its claims include the pod's `name` and `uid` (`kubernetes.io.pod.uid`). It is never stored in `etcd`, and it becomes invalid as soon as the pod is deleted or the time expires.
</details>

<details>
<summary>8. How do you generate a short-lived `ServiceAccount` token on the CLI (e.g., for testing or break-glass access), and how do you mount a token scoped to a custom audience (`vault`) inside a Pod?</summary>

- **CLI (`TokenRequest` API):**
  `kubectl create token trainer-sa -n team-a --duration=30m --audience=vault`
- **Pod `projected` volume:**
  ```yaml
  volumes:
    - name: vault-token
      projected:
        sources:
          - serviceAccountToken:
              path: token
              audience: vault
              expirationSeconds: 3600
  ```
</details>

<details>
<summary>9. Explain the four RBAC object types (`Role`, `ClusterRole`, `RoleBinding`, `ClusterRoleBinding`) and what happens when a `RoleBinding` references a `ClusterRole`.</summary>

- **`Role` (namespaced):** Defines permissions (`rules`) within a single namespace.
- **`ClusterRole` (cluster-scoped):** Defines permissions on cluster-scoped resources such as `nodes`, `persistentvolumes` and `customresourcedefinitions`. It can also cover non-resource URLs such as `/healthz` and `/metrics`, or hold reusable namespaced rules for `pods`, `deployments` and `jobs`.
- **`ClusterRoleBinding` (cluster-scoped):** Binds a `ClusterRole` to subjects across every namespace in the cluster.
- **`RoleBinding` (namespaced) referencing a `ClusterRole`:** This is a powerful reuse pattern. A `RoleBinding` inside namespace `team-a` that binds the reusable `edit`, `admin` or `trainer-runner` `ClusterRole` grants the subject those permissions strictly inside `team-a`. You avoid duplicating identical `Role` definitions across 50 team namespaces.
</details>

<details>
<summary>10. What is the difference between the built-in `view`, `edit`, `admin`, and `cluster-admin` ClusterRoles regarding `Secret`s and `RoleBinding`s?</summary>

- **`view`:** Read-only (`get`, `list`, `watch`) on most namespaced resources. It explicitly excludes `secrets`, to prevent credential leaks, and it excludes `roles` and `rolebindings`.
- **`edit`:** Read and write on workloads such as `pods`, `deployments`, `jobs`, `services` and `configmaps`. It also includes read and write on `secrets`, plus `pods/exec`. It excludes `roles` and `rolebindings`.
- **`admin`:** Everything in `edit`, plus read and write on `roles` and `rolebindings` within that namespace. A team lead can manage namespace access this way, though not `ResourceQuota` or the `Namespace` itself.
- **`cluster-admin`:** An unrestricted superuser, with `verbs: ["*"]`, `resources: ["*"]` and `nonResourceURLs: ["*"]` across the entire cluster.
</details>

<details>
<summary>11. How do Aggregated ClusterRoles (`aggregationRule`) work when you install a new Operator like `Kueue` or the `Kubeflow Training Operator`?</summary>

The built-in `view`, `edit` and `admin` ClusterRoles use an `aggregationRule.clusterRoleSelectors` block. It matches labels such as `rbac.authorization.k8s.io/aggregate-to-edit: "true"`. When you install the Kubeflow Training Operator, its Helm chart adds a small ClusterRole, `kubeflow-pytorchjobs-edit`. That role carries the label and grants `create`, `get`, `list`, `watch` and `delete` on `pytorchjobs`. The `kube-controller-manager`'s clusterrole-aggregation controller merges those rules into `edit` and `admin` automatically. So every team bound to `edit` can submit `PyTorchJob`s right away, without anyone editing the core `edit` ClusterRole.
</details>

<details>
<summary>12. In *Kubernetes: Up and Running* Chapter 14, why do manual edits to a built-in `ClusterRole` disappear when `kube-apiserver` restarts, and what annotation prevents this?</summary>

On startup, `kube-apiserver` runs a bootstrap reconciliation loop. It resets the built-in `system:*`, `view`, `edit`, `admin` and `cluster-admin` ClusterRoles and ClusterRoleBindings to their default rules when `rbac.authorization.kubernetes.io/autoupdate` is `"true"`, which is the default. To keep a deliberate customization, set this in the role's `metadata.annotations`:
**`rbac.authorization.kubernetes.io/autoupdate: "false"`**
Creating a separate custom ClusterRole is almost always cleaner, though.
</details>

<details>
<summary>13. Why is granting `create` on `pods` in a namespace practically equivalent to granting `get` on every `Secret` and `ServiceAccount` token in that namespace?</summary>

Even if an engineer's `Role` has zero permissions on `secrets`, `create` on `pods` in namespace `team-a` is enough to reach them. That engineer can create a Pod that mounts any Secret in `team-a` as a volume, or sets `serviceAccountName: privileged-sa` in `team-a`. The Pod can then print the secret or token to `stdout`, where `kubectl logs` shows it, or send it over the network. Treat `create` on `pods` and other workloads as full read access to every secret and ServiceAccount in that namespace. If a namespace holds sensitive operator credentials, restrict arbitrary Pod creation.
</details>

<details>
<summary>14. Name six RBAC permissions that allow an attacker to escalate privileges to `cluster-admin` if granted at cluster scope.</summary>

1. `get`, `list` or `watch` on `secrets` cluster-wide reads every operator, webhook and controller ServiceAccount token, or TLS private key, in `kube-system`.
2. `create` or `patch` on `pods` (or `daemonsets`) in `kube-system`, or on any node without Pod Security restrictions, allows `hostPath: /` and `privileged: true`.
3. `create` or `get` on `nodes/proxy` gives direct access to every kubelet API (`:10250/exec`). That allows command execution inside any Pod on any node, without audit logs on `kube-apiserver`.
4. `escalate` and `bind` on `clusterroles` or `clusterrolebindings` bypass the built-in RBAC privilege-escalation check. The user can bind themselves to `cluster-admin`.
5. `impersonate` on `users`, `groups` (`system:masters`), or `serviceaccounts`.
6. `create` on `serviceaccounts/token`, or `update` on `validatingwebhookconfigurations` or `mutatingwebhookconfigurations`. The first mints tokens for any ServiceAccount. The second can inject a malicious container into `kube-system` Pods.
</details>

<details>
<summary>15. Why is using a client certificate with `O = system:masters` dangerous for day-to-day human administration, and how can you revoke it if leaked?</summary>

The `system:masters` group is hardcoded into `kube-apiserver`'s authentication layer. It is an unconditional superuser that completely bypasses the RBAC authorizer. No ClusterRoleBinding deletion or webhook can block it. Kubernetes also does not support X.509 certificate revocation lists (`CRL`s) or OCSP for client certificates. So the only way to revoke a leaked `system:masters` client certificate, such as `/etc/kubernetes/admin.conf`, is to rotate the entire cluster Root CA (`ca.crt` and `ca.key`) and re-issue every certificate in the cluster. Humans should authenticate with short-lived OIDC tokens, never with `system:masters` certificates.
</details>

<details>
<summary>16. Walk through the `sudo`-style RBAC Impersonation pattern from *Production Kubernetes* Chapter 10.</summary>

Instead of binding the `ops-team` group straight to `cluster-admin`, the pattern uses three bindings:
1. Bind `Group: ops-team` to the read-only `view` ClusterRole, through `cluster-admin-view`. Routine `kubectl` commands then cannot accidentally delete or change production objects.
2. Bind `User: cluster-admin`, a synthetic username that no human logs in as directly, to the `cluster-admin` ClusterRole.
3. Grant `Group: ops-team` a ClusterRole, `cluster-admin-impersonator`, with `verbs: ["impersonate"]`, `resources: ["users"]` and `resourceNames: ["cluster-admin"]`.

When an on-call engineer intentionally needs admin rights, they pass `kubectl --as=cluster-admin ...`. The API server audit log then records both the real human identity (`user.username: "john"`) and `impersonatedUser.username: "cluster-admin"`.
</details>

<details>
<summary>17. In *Kubernetes: Up and Running* Chapter 14, how do you test RBAC permissions for a specific subresource (such as `pods/logs` or `pods/exec`) or another ServiceAccount using `kubectl auth can-i`, and what does `kubectl auth reconcile` do?</summary>

- **Test a subresource or an impersonated ServiceAccount:**
  `kubectl auth can-i get pods --subresource=logs -n team-a --as=system:serviceaccount:team-a:trainer`
  `kubectl auth can-i create pods --subresource=exec -n team-a --as=jane@example.com`
- **Reconcile RBAC manifests from Git declaratively (`kubectl auth reconcile`):**
  `kubectl auth reconcile -f rbac-roles.yaml --dry-run=client`. It synchronizes `Role`, `ClusterRole`, `RoleBinding` and `ClusterRoleBinding` objects safely.
</details>

<details>
<summary>18. Why is `roleRef` immutable on a `RoleBinding` and `ClusterRoleBinding`?</summary>

Kubernetes makes `roleRef` immutable so that someone who can only `update` or `patch` a binding's `subjects` cannot change `roleRef.name` from `view` to `admin` or `cluster-admin`. To change which Role or ClusterRole a binding points to, delete the binding and apply the new one, or run `kubectl replace --force -f binding.yaml`.
</details>

<details>
<summary>19. How do you trigger an automatic rolling restart of a `Deployment` whenever its mounted `ConfigMap` or `Secret` changes in GitOps?</summary>

Use one of three standard patterns:
1. **Kustomize `configMapGenerator` / `secretGenerator`:** The generator appends a content hash to the generated name, such as `trainer-config-8g2m9k4f`, and rewrites every Deployment reference to that hashed name. Any change creates a new immutable ConfigMap and triggers a standard Deployment rolling update.
2. **Helm checksum annotation on the Pod template:**
   `annotations: { checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }} }`
3. **Stakater `Reloader` controller:** It watches `reloader.stakater.com/auto: "true"` annotations on Deployments, and triggers a rolling update whenever a referenced ConfigMap or Secret changes.
</details>

<details>
<summary>20. How do RBAC and Admission Policy (`Pod Security Admission` / `Kyverno` / `ValidatingAdmissionPolicy`) complement each other?</summary>

- **RBAC (authorization):** RBAC inspects only the API request envelope: the caller identity, the verb `create`, the resource `pods` and the namespace `team-a`. It cannot look inside the YAML body. If RBAC allows `create` on `pods`, RBAC alone cannot stop `privileged: true`, `hostNetwork: true` or a `hostPath: /` mount.
- **Admission control (Pod Security Admission, ValidatingAdmissionPolicy, Kyverno, Gatekeeper):** Admission control inspects the actual `spec` of the object after RBAC passes. It rejects pods that request `privileged: true`, `hostPath`, unauthorized registries or excessive GPUs. Both layers are mandatory in a multi-tenant AI cluster.
</details>

## Sources and review notes

- **Sources read in full:**
  - `kubernetes-up-and-running-3rd-edition` — Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, *Kubernetes: Up and Running*, 3rd ed., **Chapter 13: ConfigMaps and Secrets** (read in full: ConfigMaps, `kuard-config` Pod consuming env vars, `$(EXTRA_PARAM)` CLI substitution, and volume mounts, Secrets, `kuard-tls`, key naming constraints `Table 13-1`, and live updates via `create --dry-run -o yaml | replace`) and **Chapter 14: Role-Based Access Control for Kubernetes** (read in full: identity and auth, `Role`/`ClusterRole` and `RoleBinding`/`ClusterRoleBinding`, built-in roles and `rbac.authorization.kubernetes.io/autoupdate: "false"`, `kubectl auth can-i --subresource`, `kubectl auth reconcile`, and ClusterRole aggregation).
  - `production-kubernetes` — Josh Rosso, Rich Lander, Alexander Brand & John Harris, *Production Kubernetes*, **Chapter 7: Secret Management** (read in full: defense in depth, etcd threat model, `EncryptionConfiguration` with `secretbox` and `kms` providers and safe 2-key rotation, `tmpfs` secret mounts, Sealed Secrets, HashiCorp Vault `TokenReview` Kubernetes auth, Vault Agent Injector `MutatingWebhookConfiguration` and Go template annotations, and `secrets-store-csi-driver` `SecretProviderClass`) and **Chapter 10: Identity** (read in full: OIDC authentication and RBAC `cluster-admin-impersonator` `sudo`-style privilege elevation).
- `production-kubernetes` — Josh Rosso, Rich Lander, Alexander Brand & John Harris, *Production Kubernetes*, **Chapter 10: Identity** (read for the shared secret and static token files, the CSR client certificate flow with `CertificateSigningRequest`, OIDC with Dex and Gangway, and the Service Account token and PSAT sections).
- `production-kubernetes` — Josh Rosso, Rich Lander, Alexander Brand & John Harris, *Production Kubernetes*, **Chapter 14: Application Considerations** (read in full: ConfigMap and Secret consumption by volume, environment variable and API, the Downward API `MEM_LIMIT` example, and the external secrets platform-service guidance).
- **Run here:** `python3 code/part05/rbac_secrets_validator_lab.py` (3 passed, 0 failed).
- **Explicitly labelled inferences:** The `validate_configmap_or_secret_key`, `simulate_etcd_encryption_key_rotation`, and `evaluate_rbac_and_audit_escalations` models in `code/part05/rbac_secrets_validator.py` and the `trainer-config`, `hf-token`, `creds` projected volume, and `trainer-runner` RBAC manifests are the author's constructions synthesizing *Kubernetes: Up and Running* Chapters 13 & 14 and *Production Kubernetes* Chapters 7 & 10 (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, and 40).
- **Not verified on live hardware:** Live `kubectl`, `etcdctl`, `vault`, and `kubeseal` executions (`~1 MiB`, `0444`, `0400`, `30 days`, `vault:1.3.2`, `ttl=20m`, `expirationSeconds: 3600`, `1.22+` / `1.24`, `401`) are marked (`untested here`) where not executed by `rbac_secrets_validator_lab.py`.
