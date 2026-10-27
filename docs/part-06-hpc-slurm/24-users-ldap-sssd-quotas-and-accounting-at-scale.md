---
id: "c06-24"
title: "6.24 Users, LDAP, SSSD, quotas and accounting at scale"
sidebar_label: "6.24 Users, LDAP, SSSD, quotas and accounting at scale"
sidebar_position: 24
description: "Identity and accounting for clusters: consistent UIDs/GIDs, NIS/NIS+ history, LDAP schema and operation, SSSD and nsswitch/PAM configuration, SSH keys and MFA, home directory provisioning, storage and CPU quotas, Slurm account synchronisation, onboarding and offboarding, scaling and security, with a tested generator that derives LDIF, Slurm accounts and home setup from one validated user list"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.24 Users, LDAP, SSSD, quotas and accounting at scale

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 2 |
| Lab venue | VMs (OpenLDAP or 389-ds or FreeIPA, plus an SSSD client) |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. `code/part06/identity_gen.py` was run on a valid and an invalid user list (outputs shown); its LDIF and `sacctmgr` command forms follow standard schemas and the Slurm man page but were **not** loaded into a real LDAP server or Slurm. SSSD/PAM/OpenLDAP configuration is from general knowledge and the SCL book (chapters 11 and 28), unverified here. Labs **untested** |

## Why this matters for AI infrastructure

A GPU cluster is a multi-user, multi-team system holding valuable data and compute. Every node must agree on who a user is (same numeric UID and GID everywhere, or file permissions on shared storage are meaningless), users must be added and removed quickly and auditably, resources must be charged to the right project, and none of it can slow login or job launch at thousands of nodes. Identity mistakes cause incidents ranging from "permission denied on my own files" to unauthorised access after an employee leaves. Containers, Kubernetes and Slurm add further identity layers that must stay consistent.

## Prerequisites and outcomes

Needs Part 1 (users, permissions, PAM, nsswitch), Part 2 (DNS, TLS basics), 6.9 (Slurm accounts), 6.18 and 6.19 (quotas). After this chapter you can:

- Explain account synchronisation options (NIS/NIS+, LDAP, FreeIPA/AD, file push) and why a single directory plus SSSD is the modern default.
- Design a UID/GID scheme and an LDAP tree for a cluster; read an LDIF entry for `posixAccount`.
- Configure (conceptually) SSSD, `nsswitch.conf`, PAM and SSH so that logins, `getent` and file ownership agree on every node.
- Provision homes and storage quotas, and keep Slurm accounting in step with the directory.
- Plan onboarding, offboarding, group/project access, service accounts, and audit.
- Diagnose slow logins, missing users, UID mismatches, and cache problems.

## 1. Account synchronisation: the problem and the options

The SCL book (chapter 11) states the issue: "account management becomes a challenge in a supercomputer environment", and the most important requirement is account synchronisation between all nodes, achieved either with a **single data source over the network** (LDAP or NIS+) or by **periodic or event-driven synchronisation of static information**. Basic data (uid, gid, home directory, shell) must match everywhere; quotas, access limits and similar information can be stored and synchronised separately and may legitimately differ by node type. The book gives a pointed example: CPU time limits should not apply on compute nodes but may on login nodes, and users generally should not log in to service nodes (backup servers), although the service nodes still need to know the users' identities for file ownership.

| Method | How | Status and notes |
|---|---|---|
| **Local files pushed by config management** (Ansible/Puppet/BCM) | `/etc/passwd`, `/etc/group`, `/etc/shadow` generated centrally and copied | Simple, no network dependency at login, fine for small and medium clusters; no instant propagation; drift risk if edited locally |
| **NIS / NIS+** | Sun-era directory (YP). NIS is plaintext and weak; NIS+ added security and was deprecated by Sun | Historical; the book covers install steps. Do not choose for new clusters |
| **LDAP (OpenLDAP, 389 Directory Server)** | Hierarchical directory with the RFC 2307/2307bis POSIX schema (`posixAccount`, `posixGroup`, `shadowAccount`) | The long-standing standard; clients via `nss_ldap`/`pam_ldap` (old) or **SSSD** (modern) |
| **FreeIPA / Red Hat IdM** | LDAP + Kerberos + DNS + CA + sudo rules + SSH key distribution + host-based access control as one product | Common in enterprises and larger clusters; strong policy features; adds Kerberos and PKI to operate |
| **Active Directory / Entra ID** (via SSSD `ad` provider, Samba/winbind) | Corporate directory as identity source | Common when the company mandates it; mapping UID/GID from AD attributes (RFC2307 attributes) or algorithmically (SSSD `ldap_id_mapping`) |
| **SSO via OIDC/SAML for web portals** | Open OnDemand, JupyterHub, Kubernetes dashboards | Complements POSIX identity; the portal still maps to a POSIX user (6.25) |

Mixed approach in practice: corporate directory or IdP is authoritative for people; the cluster has its own LDAP/IPA tree (or SSSD mapping) giving POSIX attributes and groups; local system and service accounts stay in local files with UIDs below a reserved range.

### Pull-based file synchronization and timeout wrappers

When synchronising `/etc/passwd`, `/etc/shadow`, and `/etc/group` directly instead of running a network directory, the book recommends a pull model rather than pushing blindly from the master node. Each compute node runs a local script at boot—and on demand when triggered from the master—so that a replaced or temporarily offline node automatically catches up when it boots. In the book's example, `/usr/sbin/master-sync` on each node pulls the three files over `rsync` and SSH `(untested here)`:

```bash
#!/usr/bin/env bash
# (untested here)
SYNC="rsync -e 'ssh -i /root/secret_key'"
SRC_ADDR=root@master.cluster
$SYNC $SRC_ADDR:/etc/passwd /etc/passwd
$SYNC $SRC_ADDR:/etc/shadow /etc/shadow
$SYNC $SRC_ADDR:/etc/group /etc/group
```

To trigger `/usr/sbin/master-sync` across the cluster from the master after batch account edits without overloading the network or hanging indefinitely on a dead node, the book uses a wrapper script with a `0.1`- to `0.5`-second delay between nodes (or `pdsh`/`clush`) and a self-targeted `ALRM` signal timer `(untested here)`:

```bash
#!/usr/bin/env bash
# (untested here)
TIMEOUT=600
CT=3
# exit the script after getting ALRM signal
trap 'exit' ALRM
# schedule ALRM signal to self
(sleep $TIMEOUT && kill -ALRM "$$") &
# do the sync
for i in $(grep -v \# /etc/nodes); do
  ssh -o connecttimeout=$CT $i /usr/sbin/master-sync
  echo -n .
  sleep 0.1
done
echo
```

Here `connecttimeout=3` avoids waiting on unreachable hosts, while the background subshell sends `SIGALRM` to the script's own PID (`$$`) after `600` seconds so the `trap 'exit' ALRM` handler terminates the entire run if stuck.

### Legacy NIS / NIS+ architecture and setup

NIS (Network Information System, originally Sun Yellow Pages, hence the `yp` prefix on its commands) and its successor NIS+ (which is protocol-incompatible with original NIS despite sharing utility names) distribute account and host tables over RPC. The book notes that a single NIS server begins to struggle when serving more than `30–40` clients because of concurrent RPC load, and NIS/NIS+ lack modern security. You may still encounter them on older small clusters. Three server daemons run on the master:

- `ypserv` — the main NIS/NIS+ query server.
- `yppasswdd` — the daemon that processes user password updates.
- `ypxfrd` — the daemon that transfers updated database maps to secondary (slave) servers.
- `ypbind` — the client daemon that binds a node to a server in the NIS domain.

In the book's 8-step setup and Chapter 28 recipe `(untested here)`:

1. Configure `rpcbind` (or `portmap`), `ypserv`, `yppasswdd`, and `ypxfrd` to start at boot (`systemctl enable rpcbind ypserv yppasswdd ypxfrd`).
2. Open the firewall for `rpcbind`, `portmap`, `ypserv`, `yppasswdd`, and `ypxfrd`.
3. Set the NIS domain name (`NISDOMAIN="MYCLUSTER"` in `/etc/sysconfig/network` on Red Hat systems, `NISSERVER=master` in `/etc/default/nis` on Debian systems, and `MYCLUSTER` in `/etc/defaultdomain` on both server and clients).
4. Configure `/etc/ypserv.conf` and `/etc/sysconfig/ypserv` with the database directory (`/var/yp`) and client subnet rules.
5. Create the `/var/yp/Makefile` and restrict allowed client subnets in `/etc/ypserv.securenets` (for example `255.255.255.0 192.168.123.0` and `host 192.168.111.222`), then initialise the master database with `/usr/lib/yp/ypinit -m` `(untested here)`.
6. On each client, set the domain in `/etc/defaultdomain` and point `/etc/yp.conf` to the server (`domain MYCLUSTER my-nis-server-ip-address`).
7. Start `ypbind` on the clients (and on the master node if it also resolves cluster users via NIS).
8. Add `nis` or `nis+` to `/etc/nsswitch.conf` (`passwd: compat nis`, `group: compat nis`, `shadow: compat nis`, `hosts: files dns nis`). Whenever `/etc/passwd`, `/etc/shadow`, or `/etc/group` changes on the master, run `cd /var/yp; make` `(untested here)` to rebuild and push the maps.

## 2. UID/GID design

- **Consistency is the contract.** File ownership on shared storage is numeric. If `alice` is 10001 on login nodes and 10005 on compute nodes, her files appear to belong to someone else. A mismatch also breaks Kubernetes volume ownership and container user mapping.
- **Reserved ranges**: system accounts below 1000 (distribution-defined), local service accounts 1000 to 9999 (for example `slurm`, `munge` must have the **same numeric id on every node**, a classic cause of munge failures), people from 10000 upward (this chapter's generator enforces a site minimum), groups for projects from a separate range (the generator starts at 20000). Never reuse a UID after offboarding: reuse lets a new user inherit a leaver's old files.
- **Primary group**: choose user-private groups (UID=GID per user) or a project/team primary group. Private groups plus project groups for sharing (with set-gid directories) is flexible.
- **Stability of generated IDs**: IDs must not depend on file ordering. (The generator assigns group GIDs in order of first appearance, which is fine for a demo but would change numbers if the CSV is reordered; real systems store allocated IDs in the directory and allocate from a counter.)
- **AD/IdP mapping**: if SSSD generates IDs algorithmically from SIDs, ensure the same SSSD ID-mapping configuration on every node, or the IDs differ.

## 3. LDAP in practice

### Directory layout

```text
dc=cluster,dc=example,dc=org
  ou=People    uid=alice (posixAccount, shadowAccount, inetOrgPerson, ldapPublicKey)
  ou=Groups    cn=research (posixGroup, memberUid: alice, bob)
  ou=Hosts / ou=Netgroups / ou=Sudoers (optional)
```

### An entry and the generator

LDIF (LDAP Data Interchange Format) is the text form used to load entries (`ldapadd -x -D cn=admin,... -W -f users.ldif`). `code/part06/identity_gen.py` takes a user list CSV (`user,uid,fullname,group,project,shell,quota_gb,sshkey`), **validates** it, and generates three artefacts from the same source of truth: `users.ldif`, `slurm_accounts.sh` and `homes.sh`. Validation rules: user-name pattern, no duplicates, numeric UID at or above the site minimum, unique UIDs, absolute shell path, integer quota. Output for three users (excerpt):

```text
dn: cn=research,ou=Groups,dc=cluster,dc=example,dc=org
objectClass: posixGroup
cn: research
gidNumber: 20000
memberUid: alice
memberUid: bob
...
dn: uid=alice,ou=People,dc=cluster,dc=example,dc=org
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
objectClass: ldapPublicKey
uid: alice
cn: Alice Nguyen
...
```

and `slurm_accounts.sh`:

```text
sacctmgr -i add account infra Description='infra' Organization='infra' || true
sacctmgr -i add account llm-pretrain Description='llm-pretrain' Organization='llm-pretrain' || true
sacctmgr -i add user alice account=llm-pretrain defaultaccount=llm-pretrain || true
...
```

A broken list (UID 500, relative shell path, non-integer quota, duplicate user) was rejected with five errors and no output written:

```text
ERROR root2: uid 500 below site minimum 10000 (collides with system/local ranges)
ERROR root2: shell must be an absolute path
ERROR root2: quota_gb must be an integer
ERROR bob: duplicate user
ERROR bob: uid 10002 already used by bob
```

Real directories need more: password/credential policy (or Kerberos/SSO instead of passwords), `memberOf` overlays, indexes on `uid`, `uidNumber`, `gidNumber`, `memberUid`, `cn`, access control lists, replication (multi-master or provider-consumer), backups (`slapcat`), TLS (LDAPS or StartTLS with a private CA), audit logging. The book's chapter 28 lists the OpenLDAP install steps for Red Hat family systems in "do one, two, three" style. Use the vendor/distribution documentation for current commands; many sites use 389 Directory Server or FreeIPA instead of hand-built OpenLDAP.

### OpenLDAP setup and flat-file migration recipe

In the book's Chapter 28 recipe for Red Hat-based systems (`openldap-servers`, `openldap-clients`, `nss_ldap`), you first generate an administrator password hash with `slappasswd` `(untested here)`:

```bash
# (untested here)
slappasswd
# >>> {SSHA}ABCDEF1234567890
```

In the book's example, `/etc/openldap/slapd.conf` configures the database backend (`bdb`), directory suffix, administrator DN (`rootdn`), password hash (`rootpw`), and schema files `(untested here)`:

```text
database bdb
suffix "dc=ldap,dc=server,dc=org"
rootdn "cn=Manager,dc=ldap,dc=server,dc=org"
rootpw {SSHA}ABCDEF1234567890

include /etc/openldap/schema/core.schema
include /etc/openldap/schema/cosine.schema
include /etc/openldap/schema/inetorgperson.schema
include /etc/openldap/schema/nis.schema
include /etc/openldap/schema/redhat/autofs.schema
include /etc/openldap/schema/openldap.schema
include /etc/openldap/schema/misc.schema
```

Next, copy `/etc/openldap/DB_CONFIG.example` to `/var/lib/ldap/DB_CONFIG` (owned by `ldap:ldap`, mode `600`), set `BASE dc=ldap, dc=server, dc=org` in `/etc/openldap/ldap.conf`, start the daemon, and load the base entry and `Manager` role from `/etc/openldap/ldap-init.ldif` using `/usr/bin/ldapadd -a -x -D 'cn=Manager,dc=ldap,dc=server,dc=org' -W -f ldap-init.ldif` `(untested here)` (verifying with `ldapsearch -h 127.0.0.1 -x -b "dc=ldap,dc=server,dc=org"`).

To migrate existing `/etc/passwd` and `/etc/group` entries into OpenLDAP, edit `/usr/share/migrationtools/migrate_common.ph` (`$DEFAULT_MAIL_DOMAIN = "ldap.server.org";` and `$DEFAULT_BASE = "dc=ldap,dc=server,dc=org";`) and run the migration Perl scripts `(untested here)`:

```bash
# (untested here)
/usr/share/migrationtools/migrate_passwd.pl /etc/passwd people.ldif
ldapadd -x -W -D "cn=Manager,dc=ldap,dc=server,dc=org" -f people.ldif

/usr/share/migrationtools/migrate_group.pl /etc/group group.ldif
ldapadd -x -W -D "cn=Manager,dc=ldap,dc=server,dc=org" -f group.ldif
```

On legacy `nss_ldap`/`pam_ldap` clients (before SSSD), the book's recipe configures `/etc/openldap/ldap.conf` (`base`, `rootbinddn`, `port 389`, `scope sub`, `pam_filter objectclass=posixAccount`, `pam_login_attribute uid`, `nss_base_passwd`, `nss_base_shadow`, `nss_base_group`, `pam_password SSHA`), stores the bind secret in `/etc/ldap.secret` (`chmod 600`, `chown root:root`), sets `files ldap` in `/etc/nsswitch.conf`, and appends `pam_ldap.so` lines (`auth sufficient /lib/security/pam_ldap.so use_first_pass`, `account sufficient`, `password sufficient ... use_authtok`, `session optional`) to `/etc/pam.d/system-auth` without removing the local Unix PAM entries so `root` can still log in during network outages.

## 4. SSSD, nsswitch and PAM on the nodes

**SSSD** (System Security Services Daemon) is the standard client: it talks to LDAP/IPA/AD, **caches** identities and credentials (so logins survive a directory outage and the directory is not queried for every `ls -l`), and exposes them through NSS and PAM. Key files (general knowledge):

```ini
# /etc/sssd/sssd.conf  (mode 600)
[sssd]
services = nss, pam, ssh
domains = cluster

[domain/cluster]
id_provider = ldap
auth_provider = ldap
ldap_uri = ldaps://ldap1.cluster.example.org, ldaps://ldap2.cluster.example.org
ldap_search_base = dc=cluster,dc=example,dc=org
ldap_tls_cacert = /etc/pki/tls/certs/cluster-ca.pem
ldap_default_bind_dn = cn=readonly,dc=cluster,dc=example,dc=org
ldap_default_authtok = <secret>
cache_credentials = true
enumerate = false
entry_cache_timeout = 5400
ldap_user_ssh_public_key = sshPublicKey
access_provider = simple
simple_allow_groups = research, platform
```

```text
# /etc/nsswitch.conf
passwd: files sss
group:  files sss
shadow: files sss
```

PAM (`system-auth`/`password-auth` via `authselect` on RHEL, `pam-auth-update` on Debian) uses `pam_sss.so`. Also relevant: `pam_mkhomedir` or `oddjob-mkhomedir` to create home directories on first login (avoid on compute nodes with shared homes; create homes at onboarding), `pam_slurm_adopt` (SSH to a node only while the user has a job there; 6.8), and `pam_limits`.

Important settings and why:

- `enumerate = false`: do not list all users on every lookup; enumeration at tens of thousands of users hurts; `getent passwd` shows only cached users.
- **Cache timeouts** and `sss_cache -E` to invalidate; stale caches explain "I was added to the group an hour ago".
- **`access_provider`** or host-based access control: restrict who can log in where (people to login nodes; no direct login on compute nodes except via a job).
- **SSH keys from the directory**: `sshd_config`: `AuthorizedKeysCommand /usr/bin/sss_ssh_authorizedkeys` and `AuthorizedKeysCommandUser nobody`; or FreeIPA's key distribution. Disable password SSH login where possible (keys or Kerberos/certificates plus MFA, Part 18).
- **Time**: Kerberos and LDAP TLS depend on clocks (6.18).
- Multiple LDAP URIs for failover; `ldap_network_timeout`, `ldap_opt_timeout` tuned so that a dead server does not stall logins for minutes.

Test on every node type: `id alice`, `getent passwd alice`, `getent group research`, `su - alice -c id`, `ssh alice@node`, `sssctl domain-status cluster`, `sssctl user-checks alice`, logs in `/var/log/sssd/`.

### Compute nodes

Stateless nodes (6.22) should come up with SSSD configured in the image and the host key/identity injected; ensure the first job does not wait on directory lookups. Consider a **local cached subset**: for Slurm, `slurmd`/`slurmstepd` calls `getpwnam` when launching tasks; slow LDAP means slow job starts, and a directory outage can fail launches (Slurm also offers an option to cache user information: `LaunchParameters=enable_nss_slurm` makes `slurmstepd` provide passwd/group data from information sent by the controller; verify support and semantics on your version). Alternatively push a generated passwd/group subset to compute nodes via the provisioning system (the "static synchronisation" approach).

### Restricting and blocking user access

When you need to block a user from logging in or restrict access during maintenance (Chapter 12 of the book), four host-level mechanisms are commonly used alongside SSSD `access_provider` and scheduler-level blocks:

1. **OpenSSH `DenyUsers` / `AllowUsers`**: in `/etc/ssh/sshd_config`, add `DenyUsers user1,user2` (or `AllowUsers` during maintenance windows) and reload `sshd` `(untested here)`. Existing sessions stay open until terminated. Do not mix `AllowUsers` and `DenyUsers` in the same scope because only one of them will take effect.
2. **PAM `pam_access.so`**: insert `account required pam_access.so` at the top of `/etc/pam.d/sshd` or `/etc/pam.d/system-auth`, then define sequential rules in `/etc/security/access.conf` using the format `permission:users/groups:origins` (`+` to allow, `-` to deny, `@group` for groups, `EXCEPT` for exclusions, and `ALL`, `LOCAL`, IP/subnet, or TTY names for origins). The book recommends placing administrator access first and a catch-all deny last `(untested here)`:
   ```text
   +:@admins:ALL
   # ... other access rules
   -:ALL:ALL
   ```
3. **Login shell replacement (`chsh`)**: change the user's shell to a non-interactive binary such as `/sbin/nologin` or `/bin/false` (for example `chsh -s /bin/false user1` `(untested here)`, ensuring `/bin/false` is listed in `/etc/shells`). Because SSH executes remote commands through the user's login shell, this blocks both interactive logins and `ssh remotehost command`.
4. **File-transfer-only shell (`scponly`)**: when a user must copy files via `scp` or `sftp` without interactive shell access, install the `scponly` package and set the user's shell to `/usr/bin/scponly` `(untested here)`.

## 5. Homes, storage quotas and CPU limits

- **Home directories**: created at onboarding by a script on the file server (`install -d -m 0700 -o UID -g GID /home/user`, as emitted by `homes.sh`), populated from `/etc/skel`, with ACL/ownership right; avoid per-login creation on compute nodes.
- **Storage quotas**: user and project quotas on the file systems that matter. Lustre: `lfs setquota -u USER -b SOFT -B HARD -i ISOFT -I IHARD /lustre` and project quotas for directories (6.19); GPFS fileset quotas; XFS project quotas on NFS servers (`xfs_quota -x -c 'limit -p bhard=1t projname'`); ZFS dataset quotas; object-store bucket quotas. The generator's `homes.sh` emits the `lfs setquota` line as a comment: soft limit at 90 percent of hard in this example. On traditional local ext3/ext4 file systems (and NFS servers running `rpc.rquotad`), the book outlines mounting with `usrquota`/`grpquota` in `/etc/fstab`, building the quota database in read-only or single-user mode (`quotacheck -vugc /dev/sda6` or `quotacheck -a -M`), enabling enforcement (`quotaon -va`), and managing block/inode soft and hard limits and grace periods with `setquota`, `edquota`, `setquota -p foo -u bar -a` (to copy user `foo`'s quota to `bar`), and `repquota -s` `(untested here)`.
- **Inode quotas** matter as much as bytes (millions of tiny files, 6.18).
- **CPU/memory limits on login nodes**: `pam_limits`/`/etc/security/limits.conf` (`nproc`, `cpu`, `as`, `memlock`, `nofile`, `stack`, `maxlogins`), systemd `user-.slice` resource controls (`UserTasksMax`, `CPUQuota`, `MemoryMax` in `user-*.slice.d/`) so one user cannot saturate a shared login node (6.2); different from compute nodes where Slurm cgroups apply (6.8) and where `nofile` (open file descriptors for SSH/MPI sockets) and `memlock` (locked RAM for RDMA buffers) must be raised. In the book's login-node example, limiting ordinary users to `50` to `100` processes (`max user processes`, `-u`) prevents fork bombs, and setting a `cpu` time limit (for example `100` seconds of processor time) stops accidental calculation runs on the head node. However, the book warns that setting the hard `cpu` time limit too small in `/etc/security/limits.conf` on login nodes will kill large `scp` or `sftp` file transfers mid-copy once the SSH/sftp process accumulates that much CPU time encrypting and checksumming data.
- **Group data areas**: project directories with set-gid bit and default ACLs (`setfacl -d`, `setfacl -m u:user1:rw mydir`, `getfacl`) so files inherit the group or per-user access list.
- **Reporting**: `lfs quota`, `repquota`, nightly usage reports per user/project, alert at 80 percent, purge policy for scratch (document it).

## 6. Slurm accounting alignment

Slurm users and accounts (6.9) are separate from POSIX users: `sacctmgr add user` is keyed by user name and must match the name the system resolves. Keep them aligned:

1. The same inventory source feeds LDAP and `sacctmgr` (the generator shows how).
2. Slurm needs the user to exist on the controller and compute nodes (`getpwnam`) to submit and run; a user created in `sacctmgr` but missing in LDAP fails at launch with "invalid user".
3. Map **projects/teams** to Slurm accounts (fair-share and limits) and to POSIX groups (file access); these two tree structures are related but not identical.
4. On offboarding: disable LDAP login first, then `sacctmgr modify user ... set` limits to zero or remove associations (accounting history is kept), reassign or archive files, remove SSH keys, revoke tokens (API keys, container registry, object store, Slurm REST JWT), disable cloud and Kubernetes access.
5. Reconciliation job: nightly diff of LDAP users vs Slurm associations vs home directories vs quotas; report orphans.

## 7. Lifecycle: onboarding and offboarding

| Step | Onboarding | Offboarding |
|---|---|---|
| Request | Ticket with sponsor, project, resource needs | HR/sponsor notification |
| Identity | Create directory entry (UID/GID allocated), SSH key/MFA enrolment | Disable account (lock, remove keys), keep UID reserved |
| Access | Add to groups/projects; Slurm association, QOS | Remove from groups; cancel jobs; remove Slurm associations or set to zero |
| Storage | Home, quotas, project dirs | Transfer ownership of shared data; archive/delete home per policy; keep UID |
| Audit | Log who approved | Verify no remaining keys, tokens, cron/at jobs |
| Training | Cluster etiquette, support channel | Exit checklist |

Automate with a workflow tool (ticket to Ansible/AWX or an internal API), keep the inventory under review, and run periodic recertification (do these people still need access?).

## 8. Scale, security and troubleshooting

**Scale**: tens of thousands of nodes asking for `getpwnam` at job start can hammer LDAP: use SSSD caching, read replicas, local `nscd`/`sssd` memory caches, indexes, connection pooling, rate-limit enumeration, and `enable_nss_slurm`-style approaches; monitor LDAP latency and connection counts. Pre-warm or push static data for jobs starting on thousands of nodes.

**Security**: LDAPS/StartTLS only; read-only bind account for clients with minimal ACLs; protect `sssd.conf` (mode 600); no anonymous binds; password hashes (use SSHA512/PBKDF2 or avoid local passwords via Kerberos/SSO); MFA for logins to bastions; audit logging of admin changes; rotate bind passwords; segment the directory network; backup and tested restore. Service accounts: no interactive shell, key-only, minimal scope; tokens with expiry.

| Symptom | Likely cause | Check |
|---|---|---|
| `id alice` fails on some nodes | SSSD down/misconfigured, TLS CA missing, directory unreachable, wrong search base | `systemctl status sssd`, `sssctl domain-status`, `/var/log/sssd/`, `ldapsearch -H ldaps://... -x -D ... -b ...` |
| Files owned by numeric IDs | UID mapping differs across nodes, user deleted | `getent passwd 10001` on both nodes, ID-mapping config |
| Login takes 30+ seconds | DNS/LDAP timeouts, failover to dead server first, enumerate=true, slow PAM modules | `strace -f -tt ssh`, SSSD debug level, timeouts |
| New user cannot submit jobs | Not in `sacctmgr`, or not resolvable on controller | `sacctmgr show assoc user=...`, `getent` on controller |
| Group change not effective | Cache | `sss_cache -E`, wait for timeouts, new login session |
| SSH key not accepted | `AuthorizedKeysCommand` not configured, attribute name mismatch, sssd ssh service off | `sss_ssh_authorizedkeys alice`, `sshd -T`, logs |
| Munge failures | `munge` UID/GID differs across nodes, time skew | `id munge` on all nodes (6.7) |
| Jobs fail to start on all nodes after directory outage | `slurmstepd` cannot resolve user | cache settings, `enable_nss_slurm`, restore directory |

## 9. Containers and Kubernetes note

Containers run with the invoking user's numeric UID (enroot/pyxis, Apptainer), so host identity must be consistent (6.13); user namespaces can remap IDs, which breaks assumptions about file ownership on shared mounts. In Kubernetes, pod `runAsUser`/`fsGroup` interplay with volume ownership (5.12 and 5.21); give training pods the user's UID/GID explicitly, or use a service identity with a project group. Do not run jobs as root to "avoid permission problems".

## 10. Lab

Tested: 1) run `identity_gen.py` on a ten-user list with two projects; read the three outputs. 2) Break the list in each rule and confirm the error message. 3) Extend the script to read an existing UID allocation file so UIDs/GIDs are stable.

Untested (VMs): 4) install OpenLDAP or 389-ds, load `users.ldif`, query with `ldapsearch`. 5) Configure an SSSD client, verify `id`, `getent`, SSH login with a key from LDAP. 6) Stop the LDAP server and observe cached logins; set short/long cache timeouts. 7) Run `slurm_accounts.sh` on a test Slurm; verify `sacctmgr show assoc`. 8) Create project quotas on an XFS or Lustre test file system. 9) Measure login time with `enumerate = true` versus false and with a dead primary LDAP URI.

## 11. Interview angles

- Why must UIDs be identical on every node and how do you guarantee it?
- LDAP versus FreeIPA versus AD-integrated SSSD for a new GPU cluster?
- What does SSSD cache and what happens if the directory is down?
- How do you onboard 200 students quickly and securely? How do you offboard one?
- A user's job fails with "invalid user" on one partition. What do you check?
- How do you keep Slurm accounts and Unix users in sync?
- How would you protect SSH access to login nodes?
- Why can LDAP become a bottleneck at job start and how do you mitigate it?
- What quotas do you set and where are they enforced?

## 12. Checkpoint questions (30)

1. What must be synchronised across nodes?
2. List five synchronisation methods.
3. Why is NIS discouraged?
4. What POSIX schema classes does LDAP use for users and groups?
5. What is an LDIF file?
6. State UID range conventions for system, service and people accounts.
7. Why never reuse a UID?
8. What breaks if `munge` UID differs?
9. What is user-private-group vs project group?
10. What does SSSD provide over `nss_ldap`?
11. What does `enumerate=false` do?
12. What do `passwd: files sss` mean?
13. How do SSH keys come from LDAP via SSSD?
14. What is `pam_slurm_adopt`?
15. Why avoid `pam_mkhomedir` on compute nodes?
16. How do you create project quotas on Lustre?
17. Why set inode quotas?
18. How do you limit a user's CPU time on a login node via `/etc/security/limits.conf`, and why does setting the `cpu` limit too small break large `scp` or `sftp` transfers? (Answer: `pam_limits` enforces cumulative processor seconds via the `cpu` item; if set too low, the `scp`/`sftp` server process exceeds the CPU time limit while encrypting/transferring a large file and is killed mid-copy.)
19. How do you keep `sacctmgr` and LDAP in step?
20. What happens when a user exists in Slurm but not on the node?
21. List offboarding steps.
22. How do you detect orphan accounts?
23. What does the generator validate?
24. Why must group GIDs not depend on CSV ordering?
25. How do you secure LDAP traffic?
26. Name three causes of slow logins.
27. What does `sss_cache -E` do?
28. How does `enable_nss_slurm` help (conceptually)?
29. How do containers interact with host UIDs?
30. What belongs in a nightly reconciliation?

## 13. Sources and review notes

- Book source (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`):
  - Chapter `11. Users – Accounting Management` (read in full): pull-based `/usr/sbin/master-sync` over `rsync`/SSH, `trap 'exit' ALRM` timeout wrapper loop, NIS/NIS+ daemon roles (`ypserv`, `yppasswdd`, `ypxfrd`, `ypbind`), `30–40` client RPC load limit, and 8-step NIS+ setup.
  - Chapter `12. Users – Quotas and Access Rights` (read in full): traditional Linux file system quotas (`usrquota`/`grpquota`, `quotacheck`, `quotaon`, `setquota`, `edquota`, `repquota`, `rpc.rquotad`), `ulimit` and `/etc/security/limits.conf` (`50–100` processes and `100` seconds CPU time on login nodes, and why a small `cpu` limit kills large `scp`/`sftp` transfers), POSIX ACLs (`setfacl`/`getfacl`), and user blocking methods (`DenyUsers`/`AllowUsers`, `pam_access.so` with `/etc/security/access.conf`, `chsh -s /bin/false`, and `scponly`).
  - Chapter `28. One-Two-Three Instructions` (read in full): NIS+ server/client recipes (`ypinit -m`, `/etc/ypserv.securenets`, `/var/yp/Makefile`) and OpenLDAP server/client setup (`slappasswd`, `/etc/openldap/slapd.conf`, `ldap-init.ldif`, `migrate_passwd.pl`, `migrate_group.pl`, `/etc/ldap.secret`, and `pam_ldap.so`).
- Original and run: `identity_gen.py`.
- Unverified: all SSSD/LDAP/PAM/NIS+ configuration lines, `/usr/sbin/master-sync` and wrapper scripts, `enable_nss_slurm` semantics, `sacctmgr` option spellings for your version, FreeIPA/AD details, ext3/XFS/ZFS/Lustre quota commands, scale figures. The generated LDIF was not loaded into a directory.
