---
id: "c04-12"
title: "4.12 Ansible Vault and secrets management"
sidebar_label: "4.12 Ansible Vault and secrets management"
sidebar_position: 12
description: "Handling secrets in automation: Ansible Vault (files, strings, vault IDs), keeping secrets out of logs and diffs, HashiCorp Vault and cloud secret managers, SOPS, CI integration, rotation and incident response"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 4.12 Ansible Vault and secrets management

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | ansible-core; optional `vault server -dev` in Docker; `sops` and `age` for the SOPS exercises |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Automation needs the keys to everything: SSH keys and sudo passwords for every node, BMC (Redfish/IPMI) credentials that are root-equivalent over the hardware, registry tokens, cloud service-account keys, database passwords, Slurm and Munge keys, TLS private keys, Hugging Face and API tokens. A leaked automation repository or CI log is a fleet-wide compromise. At the same time, secrets must be available non-interactively to pipelines at 3 a.m. This chapter teaches layered handling: keep secrets out of plaintext Git, encrypt what must live in Git (Ansible Vault, SOPS), fetch dynamic secrets at run time from a secret manager (HashiCorp Vault, cloud managers), prevent leakage through logs and diffs, and rotate when something leaks.

## Prerequisites and outcomes

Needs 4.3 to 4.8 and 4.1 (secrets in Git history). After this chapter you can:

- Encrypt files and individual values with `ansible-vault`, use vault IDs for multiple environments/passwords, edit, rekey, and decrypt safely.
- Structure variables so secrets are discoverable but not exposed (`vault_` prefix pattern), and use them in playbooks with `no_log`.
- Pass vault passwords non-interactively (password files, scripts, client scripts using a secret manager) without weakening security.
- Use HashiCorp Vault, cloud secret managers and SOPS from Ansible and CI; compare approaches.
- Prevent leaks through `--diff`, `-v`, registered variables, templates and shell history; scan for secrets; respond to leaks.
- Design rotation for SSH keys, passwords, tokens and certificates.

## 1. Threat model

| Asset | Where it hides | Typical leak |
|---|---|---|
| SSH private keys, `ansible_password`, sudo passwords | Inventory, group_vars, CI variables | Committed in Git; printed with `-vvv` |
| BMC/IPMI/Redfish credentials | host_vars, role defaults | Shared default passwords; plaintext vars |
| Cloud keys, registry tokens, DB passwords | `.env`, templates, task args | Logs, `--diff`, `debug` output, registered results |
| TLS private keys, Munge/Slurm keys | Files copied by roles | World-readable modes; backups |
| API tokens (Hugging Face, W&B) | Env files, systemd units | `ps` output, unit files readable by all |
| Vault password itself | `.vault_pass` in repo or home | Committed or shared in chat |

Principles: **least privilege** (each pipeline and role gets only needed secrets), **short-lived credentials** where possible (OIDC, dynamic secrets), **encryption at rest** for anything stored, **never in logs**, **auditability** (who read what), and **rotation as a routine** rather than an emergency.

## 2. Ansible Vault

Ansible Vault encrypts files or values with AES-256 (symmetric; the password derives the key via PBKDF2/HMAC). Encrypted content is stored in Git; the password is supplied at run time.

### Files

```bash
ansible-vault create inventories/prod/group_vars/all/vault.yml     # opens $EDITOR on a new encrypted file
ansible-vault encrypt inventories/prod/group_vars/all/vault.yml    # encrypt an existing plaintext file
ansible-vault edit    inventories/prod/group_vars/all/vault.yml
ansible-vault view    inventories/prod/group_vars/all/vault.yml
ansible-vault decrypt inventories/prod/group_vars/all/vault.yml    # avoid; if you do, re-encrypt before commit
ansible-vault rekey   inventories/prod/group_vars/all/vault.yml    # change the password
ansible-playbook site.yml --ask-vault-pass                         # prompt
ansible-playbook site.yml --vault-password-file ~/.vault_pass_prod # file or executable script
```

An encrypted file begins with `$ANSIBLE_VAULT;1.1;AES256` (or `1.2` with a vault ID label) followed by hex ciphertext. Whole-file encryption hides the variable names too, so reviewers cannot see what changed (diffs show opaque blobs).

### The `vault_` indirection pattern

Keep names reviewable by separating **plaintext references** from **encrypted values**:

```yaml
# group_vars/all/vars.yml (plaintext, reviewed in PRs)
db_password: "{{ vault_db_password }}"
registry_token: "{{ vault_registry_token }}"
slurm_munge_key_b64: "{{ vault_munge_key_b64 }}"

# group_vars/all/vault.yml (encrypted)
vault_db_password: "s3cr3t..."
vault_registry_token: "ghp_..."
vault_munge_key_b64: "..."
```

A `grep -r db_password` then shows where the secret is used while the value remains encrypted; `ansible-vault view` shows the vault names. Directory-style `group_vars/all/` (4.5) allows `vars.yml` and `vault.yml` side by side.

### Encrypting single values

```bash
ansible-vault encrypt_string --vault-id prod@prompt 'actual-secret' --name 'vault_db_password'
```

produces an inline `!vault |` block pasted into a vars file; the file stays plaintext and diff-able while the secret value is encrypted. Trade-offs: inline strings are convenient but easy to scatter, harder to rekey (each value must be re-encrypted), and multi-line values need care; many teams prefer one encrypted file per scope.

### Vault IDs: multiple passwords

Use labels to separate environments or roles of access:

```bash
ansible-vault encrypt --vault-id prod@prompt group_vars/prod/vault.yml
ansible-vault encrypt --vault-id dev@~/.vault_pass_dev group_vars/dev/vault.yml
ansible-playbook site.yml --vault-id dev@~/.vault_pass_dev --vault-id prod@prompt
```

Ansible tries the supplied passwords against each vault label. Configure defaults in `ansible.cfg` (`vault_identity_list = dev@~/.vault_pass_dev, prod@~/.vault_pass_prod`). Separate passwords per environment mean a developer with dev access cannot decrypt prod; prod's password is held by fewer people or only by the CI/AAP credential store.

### Providing the vault password without a human

- **Password file** (`--vault-password-file`): simple; protect with `chmod 600`, keep it out of the repository (`.gitignore`), and out of backups and shared drives.
- **Executable script/client script** (any executable file named `*-client` or passed as the password file that prints the password to stdout): fetch the password from your secret manager at run time (macOS Keychain, `pass`, 1Password CLI, AWS/GCP Secret Manager, HashiCorp Vault). This removes the plaintext password from disk. Vault-ID client scripts receive `--vault-id label` and can select per-label passwords.
- **CI/AAP**: store the vault password as a masked CI secret or an AAP "Vault" credential; scope it to protected branches/environments.

Limits and cautions: Vault is **symmetric and static**: everyone with the password can decrypt everything it protects, there is no per-secret access control or audit log, and rotation means re-encrypting. It is excellent for small teams and bootstrap secrets; at scale or for dynamic secrets, combine with a secret manager (section 4).

## 3. Keeping secrets out of output

```yaml
- name: Create database user
  community.postgresql.postgresql_user:
    name: "{{ db_user }}"
    password: "{{ db_password }}"
  no_log: true                       # hide args and results from output, logs and callbacks

- name: Render config containing secrets
  ansible.builtin.template:
    src: app.env.j2
    dest: /etc/fleetapp/app.env
    owner: root
    group: fleetapp
    mode: "0640"
  diff: false                        # do not print the rendered diff
  no_log: true
```

Leak paths to close:

- **`--diff` and `-v/-vvv`** print module arguments and rendered content: set `diff: false` and `no_log: true` on sensitive tasks; avoid running CI at `-vvv`.
- **`register`** on sensitive tasks and later `debug` of the result; also callback plugins that write results to files or services (`log_path`).
- **`command`/`shell` with secrets in arguments** appear in `ps`, shell history, audit logs (`auditd`) and the Ansible task args; pass via files (mode 0600), stdin, or `environment:` (visible in `/proc/PID/environ` to the same user and root).
- **Templates for env files and systemd units**: use `EnvironmentFile=` with mode 0600/0640 and the right owner; avoid `Environment=SECRET=...` in world-readable unit files.
- **Failed task output** in CI logs: `no_log` hides it, which also hinders debugging; temporarily disable only in a controlled session and never in shared logs.
- **Facts caching** (`fact_caching`) can persist secrets that were set as facts: use `cacheable: false` and protect the cache directory.
- **Error messages** from modules sometimes echo arguments: prefer `no_log` over trusting the module.
- **Ansible Vault temp files**: editors may leave swap/backup files (`.swp`, `~`): configure `$EDITOR` and `.gitignore`.
- **Shell history** when using `encrypt_string` with the secret on the command line: use stdin (`--stdin-name`) or prompts.

## 4. External secret managers

### HashiCorp Vault (or OpenBao)

Vault provides authentication (AppRole, JWT/OIDC for CI, Kubernetes, cloud IAM), per-secret ACL policies, audit logs, leases, **dynamic secrets** (short-lived database credentials, cloud tokens, SSH certificates) and encryption as a service.

```yaml
- name: Read a secret at run time
  ansible.builtin.set_fact:
    db_password: "{{ lookup('community.hashi_vault.hashi_vault',
                     'secret=kv/data/prod/fleetapp:db_password',
                     url=vault_url, auth_method='jwt', role_id=..., ) }}"
  no_log: true
  delegate_to: localhost
  run_once: true
```

(Real configuration uses environment variables `VAULT_ADDR`, `VAULT_TOKEN` or the auth-specific parameters; keep tokens out of playbooks.) Considerations: lookups run on the **control node** with the controller's identity; CI authenticates with OIDC so no static token exists; each secret fetch should be least-privilege (policies per pipeline); values you pass into tasks still pass through templates and can leak, so keep `no_log`; for host-side use consider **Vault Agent** or SSH CA to issue short-lived SSH certificates instead of distributing static keys.

### Cloud secret managers

AWS Secrets Manager/SSM Parameter Store (`amazon.aws.aws_secret`, `aws_ssm` lookup), GCP Secret Manager (`google.cloud.gcp_secret_manager` lookup/module), Azure Key Vault (`azure.azcollection`). Authenticate through workload identity (CI OIDC) rather than static keys. Advantages: IAM-based access, audit logs, rotation hooks, regional availability. Pattern: bootstrap a minimal identity, fetch secrets, write them to hosts with strict modes, never persist in logs.

### SOPS (Secrets OPerationS)

SOPS encrypts the **values** in YAML/JSON/ENV/INI files while leaving keys readable, using KMS (AWS/GCP/Azure), age or PGP keys; each file records which recipients can decrypt. It gives reviewable diffs ("`db_password` changed") and per-recipient access control without a shared password.

```yaml
# .sops.yaml
creation_rules:
  - path_regex: inventories/prod/.*secrets\.sops\.yml$
    kms: projects/my-proj/locations/global/keyRings/infra/cryptoKeys/sops
  - path_regex: inventories/lab/.*secrets\.sops\.yml$
    age: age1examplepublickey...
```

```bash
sops inventories/lab/group_vars/all/secrets.sops.yml          # edit in place (decrypts to editor, re-encrypts on save)
sops -d file > /dev/null                                       # verify decryption works
```

Ansible integration: the `community.sops` collection provides a vars plugin (auto-decrypts `*.sops.yml` in `group_vars`), lookup (`community.sops.sops`) and an action to decrypt on the controller. Compared with Ansible Vault: no single shared password, KMS-backed access control and audit trail, partial-file encryption; cost: dependency on KMS/age tooling and a different workflow. SOPS is also the standard for GitOps secrets (Flux integrates natively; Argo CD via plugins), which is why it recurs in Kubernetes automation (4.26).

### Other options

`pass`/`gopass`, 1Password/Bitwarden CLI lookups (`community.general.onepassword`), Kubernetes External Secrets Operator and Sealed Secrets (for cluster secrets), CyberArk/Conjur. Choose one **source of truth** per secret class and avoid copying values between systems.

### Comparison

| | Ansible Vault | SOPS | HashiCorp Vault / cloud manager |
|---|---|---|---|
| Storage | Encrypted in Git | Encrypted in Git (values only) | Central service |
| Access control | Anyone with the password | Per-key/KMS recipients | Fine-grained policies, audit |
| Diffs | Opaque (file) or opaque values | Readable keys | N/A (central) |
| Dynamic/short-lived secrets | No | No | Yes |
| Rotation | Re-encrypt files | Re-encrypt / key rotation | Native leases and rotation |
| Operational weight | Very low | Low to medium | Medium to high |
| Best for | Small teams, bootstrap, labs | Teams wanting Git-stored secrets with real access control; GitOps | Production fleets, dynamic credentials, compliance |

A common production blend: Ansible Vault (or SOPS) holds only the **bootstrap** secrets (the identity needed to reach the secret manager); everything else is fetched at run time.

## 5. SSH keys, sudo and BMC credentials

- **SSH**: prefer SSH certificates from a CA (Vault SSH secrets engine, `step-ca`, Teleport) with short lifetimes over distributing static keys; if using keys, use ed25519, per-user keys, `authorized_key` management via Ansible, passphrases with agent forwarding avoided on bastions, and rotation schedules. Never commit private keys; generate them on the controller or host and distribute only public keys.
- **sudo**: passwordless sudo for the automation account scoped to needed commands (managed by a role validated with `visudo -cf`) beats storing a sudo password; if passwords are required use Vault and `ansible_become_password`.
- **BMC credentials**: Redfish/IPMI users are root-equivalent over the hardware. Use a dedicated automation BMC account with a role limited to needed actions, unique passwords per BMC (rotate with automation; BCM and vendor tools support this), network isolation for the management plane, and fetch credentials from the secret manager at run time (`community.general.redfish_*` modules accept `username`/`password`). Default vendor passwords must be changed at provisioning (Part 7).
- **Munge and Slurm keys, kubeadm tokens, etcd certificates**: generate once, distribute with mode 0400, rotate on schedule; a role should refuse to overwrite an existing key unless forced.
- **Registry and API tokens**: use scoped, read-only, expiring tokens; per-environment tokens; revoke on leak.

## 6. CI/CD integration

- Provide vault passwords or secret-manager identities as **masked, protected** CI secrets scoped to protected branches and environments (4.2); fork PRs get none.
- Prefer OIDC to fetch short-lived credentials at job start; never write secrets to artefacts or caches.
- Run secret scanners (gitleaks, trufflehog, detect-secrets) in pre-commit and CI; enable platform push protection.
- Fail the pipeline if any file matching `vault*`/`*secret*` patterns is plaintext (a `pre-commit` hook can check the `$ANSIBLE_VAULT` header): 

```bash
# pre-commit local hook sketch: ensure vault files are encrypted
for f in $(git ls-files | grep -E '(^|/)vault(\.|_)'); do head -1 "$f" | grep -q '^\$ANSIBLE_VAULT;' || { echo "NOT ENCRYPTED: $f"; exit 1; }; done
```

- Mask secrets in CI logs, restrict who can re-run jobs or read logs, and expire logs.
- Separate duties: the person who can change a playbook should not automatically read the prod vault password; the CI environment protects it.

## 7. Rotation and incident response

**Routine rotation** (design for it from the start):

1. Make every secret replaceable by configuration (no hard-coded values); store a *version* or *created* date beside it.
2. Use overlap: add the new credential, deploy consumers, remove the old (two-phase rotation) to avoid downtime.
3. Automate: playbooks that rotate DB passwords, regenerate SSH host/user certificates, renew TLS certificates (ACME), update BMC passwords across racks, re-encrypt vault files after `rekey`.
4. Record rotations in the change log; alert on credentials approaching expiry.

**When a secret leaks** (Git commit, CI log, chat):

1. Treat as compromised: **revoke/rotate immediately**, before cleaning history.
2. Determine exposure window and use (audit logs, access logs); rotate dependent credentials if the leaked secret could mint others.
3. Remove from current code; purge history only after rotation (4.1: `git filter-repo`); invalidate forks/caches; notify per policy.
4. Add the detection that would have caught it (hook, scanner, policy), and write a short post-incident note.

**Rekeying Ansible Vault**: `ansible-vault rekey` all files with the old password, update password stores and CI secrets, and remove departed members' access by rotating the password (history in Git still contains old ciphertext decryptable with the old password, so also rotate the underlying secrets when someone with access leaves).

## 8. Lab (untested)

1. **Vault basics**: create, view, edit, rekey and decrypt an encrypted file; inspect the header; try running a playbook without the password and read the error; commit the encrypted file and examine the Git diff.
2. **Indirection pattern**: restructure variables with `vault_` names; prove `grep` finds usage; run a playbook that uses `db_password` with `no_log`.
3. **Vault IDs**: create `dev` and `prod` vaults with different passwords; show that supplying only the dev password cannot decrypt prod; configure `vault_identity_list`.
4. **Non-interactive passwords**: use a password file (mode 0600, ignored by Git), then a client script that fetches the password from `pass`, Keychain or a Vault KV; remove the plaintext password file.
5. **Leak hunting**: deliberately leak a secret through `--diff`, `-vvv`, `register` + `debug`, `command` args and `Environment=` in a unit; then plug each leak with `no_log`, `diff: false`, file modes and `EnvironmentFile`.
6. **encrypt_string**: create an inline encrypted variable from stdin; compare diff readability and rekey effort with whole-file encryption.
7. **SOPS + age**: install sops/age; encrypt a vars file; configure `community.sops`; use it in a playbook; add a second recipient; show per-recipient access and readable diffs.
8. **HashiCorp Vault**: run `vault server -dev` in Docker; store a KV secret; read it with the `hashi_vault` lookup via a token, then via AppRole; restrict a policy and confirm denial.
9. **Dynamic secret (optional)**: configure the database secrets engine and have Ansible fetch short-lived DB credentials for a deployment.
10. **CI guard**: add gitleaks plus the "vault file must be encrypted" hook to pre-commit/CI; try to commit an unencrypted vault file and a fake token.
11. **Rotation drill**: rotate a DB password and an SSH key using two-phase overlap with zero downtime; record steps and verification.
12. **Leak drill**: simulate a committed token: revoke, rotate, purge history (4.1), verify with `git log -S`, and write the five-line incident note.
13. **Clean up.**

Mark tested only after execution.

## 9. Common mistakes

- Vault password committed or stored beside the vault file; shared in chat; one password for every environment.
- Encrypting a file and then leaking its contents through `-v`, `--diff`, `debug` or `register`.
- Putting secrets in CLI arguments or `Environment=` lines readable by other users.
- Treating Ansible Vault as access control or audit (it is neither).
- Never rotating; rotating without overlap and causing outages; leaving former employees' access in place.
- Long-lived cloud keys in CI instead of OIDC.
- Copying secrets between systems until the source of truth is unclear.
- Cleaning Git history without revoking first.
- Using default or shared BMC/IPMI passwords across the fleet.
- Disabling `no_log` permanently to debug and forgetting to restore it.

## 10. Interview angles

- "How do you manage secrets in Ansible? Ansible Vault vs HashiCorp Vault vs SOPS." 
- "How do you use vault IDs and non-interactive vault passwords in CI?" 
- "How do you prevent secrets from showing up in logs and diffs?" (`no_log`, `diff: false`, modes, EnvironmentFile.)
- "A token was committed. What do you do?" (revoke, rotate, assess, purge, prevent.)
- "How do you manage BMC credentials for 1,000 servers?" (unique per device, secret manager, dedicated accounts, isolation, rotation.)
- "How do you give CI cloud access without static keys?" (OIDC.)
- "What are dynamic secrets and why do they matter?" 
- "How do you rotate a credential without downtime?" (overlap.)

## 11. Checkpoint questions (30)

1. What cipher does Ansible Vault use? **A:** AES-256.
2. Is Ansible Vault public-key based? **A:** No, symmetric password-based.
3. Header of vault files? **A:** `$ANSIBLE_VAULT;1.1;AES256` (or 1.2).
4. Command to change vault password? **A:** `ansible-vault rekey`.
5. What are vault IDs? **A:** Labels for multiple vault passwords.
6. Purpose of the `vault_` pattern? **A:** Reviewable names with encrypted values.
7. How supply password non-interactively? **A:** Password file or client script.
8. Why avoid committing the password file? **A:** It decrypts everything.
9. What does `no_log` do? **A:** Hides task data from output/logs.
10. What does `diff: false` do? **A:** Suppresses diff output for the task.
11. Why does `--diff` leak secrets? **A:** It prints rendered file content.
12. What is `encrypt_string` for? **A:** Inline encrypted values.
13. Limitation of Ansible Vault? **A:** No per-secret ACL or audit; shared password.
14. What does SOPS encrypt? **A:** Values, leaving keys readable.
15. SOPS key backends? **A:** KMS, age, PGP.
16. Ansible collection for SOPS? **A:** `community.sops`.
17. What are dynamic secrets? **A:** Short-lived credentials generated on demand.
18. What auth should CI use with Vault? **A:** OIDC/JWT or AppRole, not static tokens.
19. Where do lookups run? **A:** Control node.
20. How protect env files? **A:** Mode 0600/0640, correct owner, `EnvironmentFile`.
21. Why not secrets in command args? **A:** Visible in process lists and logs.
22. Why prefer SSH CA certificates? **A:** Short-lived, no key distribution.
23. How handle BMC passwords? **A:** Unique, rotated, from a secret manager.
24. First step after a leak? **A:** Revoke/rotate.
25. Then? **A:** Assess use, remove, purge history, add prevention.
26. What is two-phase rotation? **A:** Overlap old and new credentials.
27. How block unencrypted vault commits? **A:** Pre-commit check of the vault header.
28. What tools scan for secrets? **A:** gitleaks, trufflehog, detect-secrets.
29. Why separate vault passwords per environment? **A:** Limit blast radius and access.
30. Best use of Ansible Vault in prod? **A:** Bootstrap secrets only, with a secret manager for the rest.

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Rene Moser and Lorin Hochstein, *Ansible: Up and Running*, 3rd edition (Ansible Vault and handling secrets in playbooks, with the chapters on advanced playbooks and CI integration).
- The author's `nvidia-devops` repository, volume 10 chapter 11 section on secrets management in infrastructure pipelines (Vault, SOPS, BMC credentials).
- Ansible Vault documentation, HashiCorp Vault and `community.hashi_vault` documentation, SOPS and `community.sops` documentation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** `ansible-vault` option names and vault-ID behaviour for your ansible-core version, `community.hashi_vault` lookup parameters, `community.sops` plugin names, vault format version strings, and every command listing; all labs are **untested**.
