---
id: "c02-21"
title: "2.21 Network security: threat models, firewalls, SSH, zero trust and securing AI clusters"
sidebar_label: "2.21 Network security: threat models, firewalls, SSH, zero trust and securing AI clusters"
sidebar_position: 21
description: "Network security from threat models and defense in depth to SSH, scanning, DDoS, control-plane and AI-cluster security"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 2.21 Network security: threat models, firewalls, SSH, zero trust and securing AI clusters

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Linux VMs / namespaces; Kubernetes for NetworkPolicy |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

GPU clusters concentrate three things attackers want: very expensive compute (cryptomining, resale), very valuable data (training sets, model weights, customer prompts), and privileged access paths (BMCs, schedulers, registries, CI). They are also unusual networks: flat high-speed RDMA fabrics that bypass the host kernel, management planes with out-of-band controllers that run their own firmware, multi-tenant environments where tenants share switches, and fast-moving software stacks (drivers, container runtimes, serving frameworks) with a steady stream of CVEs. Network security here is not only firewalls; it is segmentation, identity, key management, least privilege, monitoring, and the discipline to apply them without strangling performance. This chapter covers the security model (definitions, defense in depth, access control, data protection, availability, the OODA loop), the practical network toolkit (packet filters, stateful firewalls, SSH hardening, scanning, DDoS and control-plane protections, L2 security), and what changes in AI clusters (BMC and management isolation, RDMA/IB partitioning, tenant isolation, secrets, zero trust). Linux firewall mechanics (nftables, conntrack) are in chapter 2.23; TLS/PKI in chapter 2.10; kernel-level hardening in chapter 1.21.

## Prerequisites and outcomes

You should know TCP/IP (2.4 to 2.7), TLS and PKI (2.10), NAT and DHCP (2.9) and Linux user/permission basics.

After this chapter you can:

- Define threat actor, exploit, attack, vulnerability, attack surface, asset and risk, and build a simple threat model for a network or a cluster.
- Apply defense in depth: layered filters, route validation, telemetry, stateful inspection, exfiltration monitoring, per-service access control.
- Explain AAA (authentication, authorisation, accounting), RADIUS/TACACS+, 802.1X, MFA, and where access control is enforced (before network, before service, per resource).
- Explain data protection (encryption in transit/at rest, key management) and the limits of biometrics and data-exhaust privacy.
- Explain DoS/DDoS types and mitigations (rate limiting, SYN cookies, anycast and scrubbing, RTBH, BCP38/uRPF, capacity).
- Harden SSH (keys, certificates, `sshd_config`, bastions/ProxyJump, agent forwarding, tunnels, fail2ban), explain host key verification and MITM warnings.
- Use nmap and related tools responsibly to audit exposure; interpret results; reduce attack surface (run few services, firewall by default).
- Secure the control plane and L2 (routing protocol authentication, CoPP, GTSM, DHCP snooping, DAI, port security, 802.1X).
- Apply zero-trust and segmentation (VLAN/VRF/VXLAN, Kubernetes NetworkPolicy, mTLS, microsegmentation) and secure AI-specific surfaces (BMC/Redfish, IB partition keys, RoCE tenancy, registries, model artifacts).
- Use the OODA loop for detection and response and know basic incident handling.

## 1. Vocabulary and threat modelling

| Term | Meaning |
|---|---|
| **Threat actor** | Who attacks: individual, criminal group, insider, state actor; identity hints at motive, skill and likely plan |
| **Vulnerability** | A weakness: missing filter, default password, unpatched service, misconfiguration, a social-engineerable person |
| **Exploit** | The method/tool that uses a vulnerability |
| **Attack / threat** | The potential or actual use of an exploit by an actor |
| **Attack surface** | Everything reachable by an attacker: hosts, ports, services, APIs, people, supply chain |
| **Asset** | What matters: data, models, credentials, compute, availability |
| **Risk** | Likelihood × impact of a negative outcome (breach, downtime, reputational damage) |

Three problem areas from a network perspective: (1) **access**: how users and processes legitimately reach the data they need while others can't; (2) **confidentiality/integrity**: how data in transit and at rest stays private and unmodified; (3) **availability**: how the network and services stay usable against denial-of-service. Threat modelling asks, for a given system: What are we protecting? Who might attack and why? How could they get in (entry points, trust boundaries)? What would the impact be? What controls reduce likelihood or impact? Use a simple data-flow diagram and the STRIDE categories (spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege) as a checklist; revisit when architecture changes.

**A caution on biometrics and "secrets you cannot change".** Fingerprints and other biometrics are convenient but are not secret (left on every surface) and, once digitised and stored online, they are a permanent credential that cannot be rotated after a breach. Use them as a convenience factor on a device (local, hardware-protected), not as a sole, remotely verifiable identity. Likewise, treat **data exhaust** (metadata such as who talks to whom, when, how much) as sensitive: it can reveal behaviour even when payloads are encrypted (chapter 2.10).

## 2. Defense in depth

No single control stops a determined attacker; layered, overlapping controls give multiple chances to detect and contain an intrusion and make attacks costly.

```mermaid
flowchart TB
  I["Internet / untrusted"] --> E["Edge: packet filters, rate limits, route validation (BCP38/RPKI), DDoS protection"]
  E --> F["Stateful firewall / NGFW / WAF: only established or permitted flows"]
  F --> S["Segmentation: VLAN/VRF/VXLAN zones, microsegmentation, NetworkPolicy"]
  S --> A["Per-service access control: authN/authZ, mTLS, RBAC"]
  A --> D["Data protection: encryption at rest and in transit, key management"]
  T["Telemetry across all layers: flows, logs, IDS/IPS, exfiltration monitoring"] -. "observes" .-> E & F & S & A & D
```

Examples of layers: packet filters/ACLs and rate limits at the routed edge; route validation (prefix filters, RPKI) against hijacked space; telemetry for top talkers and anomalies; stateful packet filters allowing only responses to internal connections; exfiltration monitoring (alert on large unusual transfers out of sensitive databases); access control on each service/server. The time an attacker needs to cross each layer is time for defenders to notice; the "layers of grids" an attacker must pass also let each layer apply more specific controls. Think of the *whole network as a defensive system*: routers, switches, load balancers, hosts and applications each contribute controls.

## 3. Access control and AAA

Access control ensures that users and processes are who they claim to be (**authentication**), may do what they request (**authorisation**), and that their actions are recorded (**accounting**). Together: **AAA**.

- **Where enforced**: before connecting to the network (port-based access control with **802.1X**, Wi-Fi WPA-Enterprise, VPN login); after connecting but before reaching any service (network ACLs, segmentation); before each service (application auth, mTLS); before sensitive resources (privileged access management). Combine these, with stronger factors for more sensitive resources.
- **Protocols**: **RADIUS** (UDP 1812/1813; network access AAA; shared secret; encrypts only the password field, so protect with IPsec/RadSec), **TACACS+** (TCP 49; device administration; encrypts the whole body; per-command authorisation and accounting), **LDAP/AD/Kerberos** for directory-backed identity, **SAML/OIDC/OAuth2** for web/API identity, **SPIFFE/SPIRE** for workload identity.
- **MFA** (something you know + have + are) for administrative access and VPNs; hardware keys (FIDO2) resist phishing.
- **Least privilege and just-in-time access**; separate admin accounts; session recording for privileged access; no shared accounts; break-glass procedures with audit.
- **Accounting and logging**: central logs (syslog, journald forwarding), command accounting on network devices, immutable storage, time sync (NTP) so logs correlate.

## 4. Firewalls and filtering (overview)

| Type | What it does | Notes |
|---|---|---|
| **Stateless ACL / packet filter** | Matches header fields per packet (src/dst IP, ports, flags) | Fast, in switch hardware; no memory of connections; use at edges and between zones |
| **Stateful firewall** | Tracks connections (conntrack); allows return traffic of permitted flows automatically; drops unsolicited inbound | Linux nftables/iptables with `ct state`; default for host and perimeter firewalls |
| **NGFW / proxy / WAF** | Application awareness, IPS signatures, TLS inspection, URL filtering; WAF protects web apps from injection | More CPU, TLS-inspection privacy/operational trade-offs |
| **Host-based firewall** | Policy on each server (nftables, firewalld, ufw), cloud security groups | Protects against lateral movement; enforce by configuration management |
| **Microsegmentation / NetworkPolicy** | Per-workload policies enforced in the data plane (Kubernetes NetworkPolicy via Calico/Cilium, VXLAN GBP, NSX) | Identity-based rather than IP-based rules |

**Strategy**: default-deny inbound; explicitly allow required services; restrict outbound too (egress filtering limits exfiltration and command-and-control); log drops of interest; separate zones (user, server, management, storage, fabric); put management interfaces (SSH, BMC, switch consoles) only on a dedicated management network; review rules regularly and remove unused ones; test with scans from outside and inside. Detailed mechanics and rule examples: chapter 2.23.

## 5. Data protection: encryption and keys

Systems and access controls fail; encryption is the last line of defence. Use **encryption in transit** (TLS/mTLS, SSH, IPsec/WireGuard, MACsec for links) and **at rest** (disk/volume encryption, object-store encryption, database encryption), and manage keys properly: generate on the device or in an HSM/KMS, rotate, separate duties, restrict access, never embed in images or repositories, and audit use. Protect model weights and datasets like source code and credentials: signed artifacts, access-controlled registries, immutable versions, and provenance (supply-chain security: software bill of materials, signature verification of containers and packages).

For performance-sensitive AI traffic: encryption of RDMA fabrics is a trade-off. Options: MACsec on links (line-rate in hardware on some switches/NICs), IPsec offload on NICs/DPUs, or logical isolation plus physical security. Do not assume TLS inside the fabric is feasible for GPUDirect traffic; make the threat-model decision explicitly (shared tenants → stronger isolation and encryption; single-tenant locked cage → segmentation and physical controls).

## 6. Availability: denial of service

A **denial-of-service (DoS)** attack tries to make a service or network unusable; **distributed (DDoS)** uses many sources. Classes:

| Type | Mechanism | Mitigation |
|---|---|---|
| **Volumetric** | Saturate bandwidth (UDP floods, amplification via DNS/NTP/memcached reflection) | Upstream scrubbing/anycast absorb, ISP/CDN protection, BCP38 anti-spoofing, RTBH |
| **Protocol/state exhaustion** | SYN floods, connection table exhaustion, fragment attacks | SYN cookies, connection limits, stateless filtering, larger tables, proxies |
| **Application layer** | HTTP floods, slow-loris, expensive queries, API abuse | Rate limiting, WAF, caching, CAPTCHA/auth, request cost limits, autoscaling with caps |
| **Control-plane** | Flood routers' CPUs with ICMP/ARP/routing packets | CoPP, ICMP rate limiting, routing protocol authentication |

Defensive techniques: **rate limiting and policing**, **SYN cookies** and sensible backlogs (chapter 2.6), **anycast** to spread load across sites, **blackhole routing (RTBH)** of attacked destinations via BGP community or selective BGP traffic diversion using `NO_PEER` and `NO_ADVERTISE` communities to steer traffic away from saturated peering links (`CN` Chapter 21), **BCP 38 / uRPF** (drop packets with spoofed sources, preventing reflection), **traffic scrubbing services**, **overprovisioning** and autoscaling with budget caps, **separating critical services** (management plane on its own network), and **runbooks** rehearsed in advance. Inference APIs are attractive targets because each request can consume GPU seconds (resource-exhaustion DoS): use authentication, per-key quotas, token-based rate limits, and admission control (chapter 2.20).

## 7. SSH in depth (and hardening)

SSH is the de facto remote-administration protocol: encrypted shell and command execution, file transfer (scp/sftp), port forwarding and tunnelling (including X11), and key-based authentication, replacing telnet/rlogin. Understanding it is non-negotiable for infrastructure engineers.

### Public-key cryptography in a paragraph

Symmetric ciphers need both sides to share a secret key; stealing it breaks everything. In public-key schemes each party has a **key pair**: the public key may be shared freely; only the holder of the private key can decrypt what was encrypted to the public key, or produce a signature the public key verifies. SSH uses public keys to authenticate the server to the client (host keys) and the client to the server (user keys), then negotiates a symmetric session key for bulk encryption. The private key must never be exposed.

### Host keys and trust

- Each server has host key pairs (`/etc/ssh/ssh_host_ed25519_key`, `_rsa_key`, `_ecdsa_key`; `.pub` public parts), generated at install (`ssh-keygen -A`). On first connection the client receives the server's public key and stores it in `~/.ssh/known_hosts` (**trust on first use**); on later connections a mismatch triggers the **"REMOTE HOST IDENTIFICATION HAS CHANGED"** warning: it can be benign (reinstall, cloud instance replaced, keys regenerated) or a **man-in-the-middle** attack. Verify the fingerprint out of band (`ssh-keygen -lf`; cloud serial console output; configuration-managed `known_hosts`), then remove the stale line (`ssh-keygen -R host`). When replacing a machine, copy the old host keys so users see no mismatch; in clouds, publish host keys via metadata or use **SSH host certificates** (below).
- Prefer **ed25519** keys (and ECDSA/RSA ≥ 3072 where necessary); disable DSA (obsolete).

### Client

```bash
ssh user@host                          # login ; use -p for another port ; -i key ; -J jump
ssh user@host 'uptime'                 # run a command
tar zcf - dir | ssh host 'tar zxf -'   # pipeline over SSH
scp file user@host:/path ; sftp user@host ; rsync -a -e ssh dir/ host:/dest/
ssh -L 8888:localhost:8888 user@gpu01  # local forward (e.g. Jupyter on a GPU node): browse http://localhost:8888
ssh -R 2222:localhost:22 user@pub      # remote forward ; -D 1080 SOCKS proxy
ssh -J bastion.example.com user@10.0.0.45        # ProxyJump through a bastion
ssh-keygen -t ed25519 -a 100 -C "alice@laptop"    # create a key (use a passphrase)
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@host    # install public key into authorized_keys
ssh-add ~/.ssh/id_ed25519 ; ssh-add -l            # use ssh-agent so the passphrase is entered once
```

`~/.ssh/config` example:

```text
Host bastion
  HostName bastion.example.com
  User alice
  IdentityFile ~/.ssh/id_ed25519
Host gpu-*
  ProxyJump bastion
  User alice
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h:%p
  ControlPersist 10m
  ServerAliveInterval 30
```

### Server (`sshd_config`) hardening

Note `sshd_config` (server) versus `ssh_config` (client). Key directives (verify with `man sshd_config`; apply via `/etc/ssh/sshd_config.d/*.conf` and test with `sshd -t` and a second session open):

```text
Port 22
PermitRootLogin no                 # or prohibit-password for break-glass
PasswordAuthentication no          # keys (or certificates) only
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey    # or publickey,keyboard-interactive for MFA
AllowGroups ssh-users              # explicit allow-list
MaxAuthTries 3
LoginGraceTime 20
X11Forwarding no
AllowAgentForwarding no            # agent forwarding lets a compromised host use your keys
AllowTcpForwarding no              # enable selectively per Match block
ClientAliveInterval 300
ClientAliveCountMax 2
LogLevel VERBOSE                   # logs key fingerprints used
HostKey /etc/ssh/ssh_host_ed25519_key
KexAlgorithms ...                  # use the distro's modern defaults; only remove weak legacy items
```

Operational practices:

- Restrict by network: SSH only from bastions/management networks (security groups, nftables, `ListenAddress`), never expose to the Internet unless required; if exposed, rate limit and use fail2ban.
- **Bastion/jump host** design: single audited entry point, MFA, session logging; use `ProxyJump` rather than agent forwarding.
- **SSH certificates** (`ssh-keygen -s ca -I id -n user -V +1d key.pub`): a trusted SSH CA signs short-lived user and host certificates; servers trust the CA (`TrustedUserCAKeys`, `@cert-authority` in `known_hosts`), eliminating per-key distribution and TOFU. Strong pattern for clusters (HashiCorp Vault SSH, Smallstep step-ca, Teleport, cloud-native OS Login/IAP).
- Rotate and revoke keys (`RevokedKeys`), prefer hardware-backed keys (FIDO2 `ed25519-sk`, YubiKey), protect private keys with passphrases and agent timeouts, audit `authorized_keys`.
- Configuration management for `sshd_config`, `known_hosts`, and authorised keys; monitor logins (`last`, `journalctl -u ssh`, auditd, central logs).
- Remember `sshd` is a prime target: keep OpenSSH updated, limit versions/algorithms, consider moving it behind a VPN/zero-trust proxy.
- Standalone sshd is the norm; socket-activated sshd (`ssh.socket`) can delay first logins while keys are generated; handle systemd units per distribution.

### fail2ban

On an Internet-facing host, SSH brute force is constant. `fail2ban` watches logs (journald/auth.log), and after N failures from an address within a window adds a firewall rule banning it for a period, then removes it. Configure jails in `/etc/fail2ban/jail.d/*.local` (`[sshd] enabled = true`, `maxretry`, `findtime`, `bantime`), prefer nftables actions; it reduces log noise and CPU load but is not a substitute for keys-only authentication and network restriction (it only slows brute force, and shared NAT addresses can lock out legitimate users). Check with `fail2ban-client status sshd`.

### Legacy services

`inetd/xinetd` (superservers that listened on many ports and spawned handlers) and TCP wrappers (`/etc/hosts.allow`, `/etc/hosts.deny`, `tcpd`) are largely replaced by systemd socket units and firewalls; you will meet them on old systems. Avoid exposing `telnetd`, `rlogind`, `rexecd` and FTP (cleartext credentials, chronic vulnerabilities); replace with SSH/SFTP/rsync, or wrap legacy cleartext services in TLS (Stunnel) if unavoidable.

## 8. Scanning and auditing exposure

Know what you expose. **nmap** discovers hosts and ports and fingerprints services:

```bash
nmap -sn 10.0.0.0/24                  # host discovery only (ping/ARP sweep)
nmap -p- -T4 10.0.0.45                # all TCP ports
nmap -sV -O 10.0.0.45                 # service versions, OS guess
nmap -sU --top-ports 50 10.0.0.45     # common UDP ports
nmap -6 fe80::1%eth0                  # IPv6
nmap --script ssl-enum-ciphers -p 443 host     # TLS protocol/cipher audit
ss -tulpn                             # compare with what the host itself says it listens on
```

Run scans from at least two vantage points (the host itself and another network, ideally outside your perimeter) to see what the firewall actually blocks. **Only scan networks you own or have written permission to test**; scans are logged, can disrupt fragile devices, and may violate policy or law. Complement with vulnerability scanners (OpenVAS/Nessus, Trivy for images), configuration baselines (CIS benchmarks, Lynis), and continuous asset inventory. `rpcbind` (port 111) and NFS/NIS are common unwanted exposures: disable if unused. Typical findings: forgotten dev servers, default credentials, management ports (BMC 623/443, Redis 6379, Docker API 2375, Kubernetes kubelet 10250, etcd 2379, Jupyter 8888, TensorBoard 6006, Triton 8000-8002, Ray dashboard 8265, MLflow 5000) exposed beyond need.

## 9. Basic rules and typical vulnerabilities

Rules of thumb: **run as few services as possible**; **block everything you do not need** with a firewall at the host and the perimeter; **track and patch every service you expose** (subscribe to security advisories; use LTS releases for servers); **give accounts only to those who need them** (local access makes privilege escalation far easier than remote attack); **don't install dubious binaries**; verify signatures and hashes of downloads.

Attack classes: **full compromise** (root via service exploit or a poorly protected account plus a privilege-escalation bug; mitigated by ASLR, stack protections, least privilege, SELinux/AppArmor, containers/seccomp), **denial of service**, **malware** (Linux malware exists: cryptominers, botnet agents; common entry: exposed Docker/Kubernetes/Jupyter APIs and stolen cloud keys). **Cleartext password sniffing** and credential reuse from breach databases: use MFA and unique secrets. Resources: SANS newsletters, CISA/US-CERT and national CERT advisories, vendor security bulletins (NVIDIA Security Bulletins for drivers/DCGM/Triton/Container Toolkit), distro security trackers, NVD/CVE feeds, MITRE ATT&CK.

## 10. Securing routing and the control plane

Data-plane security is useless if the control plane can be hijacked. Controls:

- **Authenticate routing protocols**: OSPF/IS-IS HMAC-SHA, BGP TCP-AO/MD5; GTSM (TTL 255) for eBGP; restrict BGP/OSPF to specific interfaces and peers (passive-interface default).
- **Filter routes**: prefix-lists/max-prefix on every peer; RPKI origin validation; reject bogons, default routes from the wrong peer, overly specific prefixes; no accidental transit.
- **Control-plane policing (CoPP)** and hardware rate limits for traffic punted to the CPU (ARP, ICMP, routing, SSH, SNMP, NTP); restrict management protocols by ACL; disable unused services on network devices (HTTP management, SNMPv1/2c, CDP/LLDP on untrusted ports, IP source routing, redirects).
- **Anti-spoofing**: BCP 38 ingress filtering, uRPF (strict at edges, loose on transit), DHCP snooping + IP source guard.
- **Management plane isolation**: out-of-band management network, jump hosts, SSH/NETCONF/gNMI with strong auth, AAA/TACACS+, config backups with diffs, signed images, secure boot where available.
- **Logging and change control**: all changes via automation with review (chapters 2.28, 2.29); config drift detection.

## 11. Layer-2 security

| Attack | Control |
|---|---|
| MAC flooding / CAM overflow | Port security (limit MACs per port), storm control |
| Rogue DHCP server | **DHCP snooping** (trust only uplink/server ports), IP source guard |
| ARP/ND spoofing | **Dynamic ARP Inspection**, ND inspection/RA guard, static entries for critical gateways |
| Rogue switch / STP manipulation | BPDU guard, root guard, disable unused ports |
| VLAN hopping (double tagging, DTP) | Disable DTP, no VLAN 1 native, set native VLAN to an unused ID, prune trunks |
| Unauthorised device attach | **802.1X** (EAP-TLS) or MAB, per-port authentication, dynamic VLAN assignment |
| Link eavesdropping | **MACsec (802.1AE)** on sensitive links |

## 12. Zero trust and segmentation

**Zero trust** replaces "inside the perimeter is trusted" with: authenticate and authorise every request based on identity, device posture and context; assume breach; least privilege; encrypt everywhere; continuous verification and logging. Practical building blocks:

- **Identity-aware access** (IAP/ZTNA proxies, Teleport, Tailscale/WireGuard meshes, cloud IAP) instead of broad VPNs.
- **Service identity** with mTLS and short-lived certificates (SPIFFE/SPIRE, service mesh, cert-manager; chapter 2.10).
- **Microsegmentation**: restrict east-west traffic to what workloads need; Kubernetes **NetworkPolicy** (default-deny ingress/egress per namespace, then allow rules by labels), Calico/Cilium policies (L3/L4/L7 and DNS-based egress), eBPF enforcement; VRFs/VXLAN tenants and GBP in the fabric (chapter 2.16/2.17); cloud security groups and firewall tags.
- **Policy as code**: version-controlled policies, tested in CI, deployed by GitOps, with drift detection.

```yaml
# Kubernetes: default deny, then allow only the inference gateway to reach the model server
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: inference }
spec: { podSelector: {}, policyTypes: [Ingress, Egress] }
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-gateway-to-triton, namespace: inference }
spec:
  podSelector: { matchLabels: { app: triton } }
  policyTypes: [Ingress]
  ingress:
  - from: [ { podSelector: { matchLabels: { app: gateway } } } ]
    ports: [ { protocol: TCP, port: 8001 } ]
```

(Remember to allow DNS egress and metrics scraping when you enforce default-deny egress; test enforcement, as policies only work if the CNI implements them.)

## 13. Security specifics for AI clusters

- **BMC / out-of-band management** (IPMI, Redfish, iDRAC, iLO, XClarity, DGX BMC): historically weak (default credentials, old IPMI 2.0 cipher-zero, exposed web UIs, unauthenticated firmware vectors). Put BMCs on an isolated management network with strict ACLs, unique strong credentials, disabled IPMI-over-LAN if unused, current firmware, HTTPS with real certificates, access only via jump hosts; monitor for Redfish events and firmware changes.
- **Provisioning network**: PXE/DHCP/TFTP and image servers are trust anchors for every node; protect them (signed images, HTTPS boot, secure boot, TPM measured boot where used), isolate the VLAN, and treat compromise as fleet-wide.
- **InfiniBand**: partition keys (**P_Key**) segment the fabric per tenant (managed by the Subnet Manager), M_Key/SM key protect management, Q_Key for datagram queue pairs, secure the SM and UFM; RoCE tenancy relies on VRFs/VLANs and QoS isolation; GPU-to-GPU RDMA traffic is generally unencrypted, so physical and logical isolation matter; NIC firmware and DPU (BlueField) provide isolation features (ARM-side network policy, host isolation modes).
- **Multi-tenant isolation**: network (VRF/VXLAN/IB partitions), compute (MIG, separate nodes, confidential computing), storage (per-tenant namespaces and encryption keys), schedulers (Slurm/K8s quotas, cgroups, user namespaces), side channels; define which tenants can share what.
- **Inference APIs**: authentication (API keys/OIDC), TLS, rate limits/quotas, request size limits, prompt injection/data exfiltration controls at the application layer, logging without leaking sensitive prompts, WAF, egress controls for tool-calling agents.
- **Supply chain**: container image provenance (sign with cosign, verify in admission), pinned base images, scanning (Trivy/Grype), curated model registries, checksum verification of weights, private package mirrors; NVIDIA driver and Container Toolkit CVEs (container escape risks) require rapid patching; do not run privileged containers casually.
- **Secrets**: no secrets in images or environment dumps; use Kubernetes Secrets with encryption at rest + external secret stores (Vault, KMS) and short-lived credentials; rotate tokens; avoid long-lived cloud keys on nodes (use workload identity).
- **Data exfiltration**: egress filtering from GPU nodes (allow-list package mirrors/registries only), DNS monitoring, flow logs, alerting on large outbound transfers.
- **Monitoring**: per-node anomaly detection (unexpected processes using GPUs: cryptominers), audit logs of schedulers and K8s API, flow logs from fabric edges, host IDS (auditd, Falco), centralised SIEM.

## 14. The OODA loop for security operations

Security is a continuous cycle, not a state: **Observe, Orient, Decide, Act** (Boyd's OODA loop), where the side that cycles faster wins.

1. **Observe**: collect telemetry: flow records, logs, packet captures on demand, IDS alerts, authentication events, vulnerability scans, threat intelligence. Without observation there's no detection. Be wary of data overload; tune what you collect.
2. **Orient**: put the observations in context: what is normal, which asset is affected, what the attacker's likely goal/technique is (ATT&CK), what the business impact is. Orientation is where experience and good inventory pay off; bias and assumptions are the main enemies.
3. **Decide**: choose a response: contain (isolate a host/VLAN, block an IP, revoke credentials), eradicate, recover, or monitor further. Predefined playbooks speed decisions.
4. **Act**: execute (automation preferred), then observe the results and loop again. Improve defences afterwards (lessons learned, post-incident review).

Design for fast loops: automated isolation hooks (move a port to a quarantine VLAN, apply a K8s deny policy, disable an account), runbooks, rehearsals (game days), and clear ownership. Keep forensic readiness: preserve logs and memory, avoid destroying evidence, record timelines.

## 15. Hands-on lab: harden and probe

First, run the self-checking Python lab (`code/part02/network_security_zerotrust_lab.py`) locally. It verifies `sshd_config` hardening compliance (`PermitRootLogin no`, `PasswordAuthentication no`, `AllowAgentForwarding no`), InfiniBand 16-bit Partition Key (`P_Key`) full vs limited membership isolation (`0x8042` vs `0x0042` vs `0x8043`), Kubernetes `NetworkPolicy` default-deny + label-based ingress evaluation, and `fail2ban` sliding-window bans.

```bash
python3 code/part02/network_security_zerotrust_lab.py
```

Next, on two or three disposable VMs or network namespaces in a lab you own (all interactive VM commands below are `untested here`), work through these steps:

1. **Exposure audit**: on a fresh VM run `ss -tulpn`, `nmap -p- -sV localhost` and from a second host; list unnecessary services; disable them; re-scan.
2. **Firewall default-deny**: with nftables allow only SSH from the management subnet and established flows (chapter 2.23); verify with nmap from inside/outside; log drops.
3. **SSH hardening**: set keys-only auth, `AllowGroups`, no root login, disable forwarding; test with `sshd -t` and a second session; try password login (should fail); use `ssh -vvv` to read the negotiation; enable `LogLevel VERBOSE`.
4. **Bastion + ProxyJump + certificates**: create an SSH CA with `ssh-keygen`; issue a user certificate valid 1 hour and a host certificate; configure `TrustedUserCAKeys` and `@cert-authority`; connect through a bastion with `ProxyJump`; wait for expiry and see denial.
5. **Host key mismatch**: regenerate a server's host keys and observe the client warning; fix properly (verify fingerprint, `ssh-keygen -R`).
6. **fail2ban**: install, enable the sshd jail with `maxretry=3`, attempt failures from a second host with a wrong key/password, watch the ban in `fail2ban-client status sshd` and `nft list ruleset`, then unban.
7. **L2 attack/defence**: in namespaces with a Linux bridge, run a rogue DHCP server and observe clients taking its lease; apply a bridge-level/ebtables or nft rule dropping DHCP offers from untrusted ports; ARP-spoof (`arpspoof`/scapy) in the lab and mitigate with static ARP entries and `arp_filter`/`arptables`.
8. **SYN flood**: `hping3 --flood -S -p 80` against a lab web server (lab only); watch `nstat` ListenOverflows/SYN cookies; tune `tcp_syncookies`, `somaxconn`, rate-limit with nft `limit`/`meter`.
9. **K8s NetworkPolicy**: in kind with Calico/Cilium, apply default-deny and the allow policy above; verify with `kubectl exec ... curl`; test DNS egress.
10. **Threat model**: draw a data-flow diagram of your training+inference platform, enumerate trust boundaries and STRIDE threats, assign controls, and decide detection signals (OODA).
11. **Clean up** keys and test CAs.

## 16. Common mistakes

- Password SSH on Internet hosts; agent forwarding to untrusted hosts; long-lived unprotected keys; `StrictHostKeyChecking no` everywhere.
- Flat networks with management interfaces reachable from workloads; exposed BMCs and dashboards.
- Firewall rules with "allow any" convenience holes; no egress filtering; rules never reviewed.
- Relying on a single control (perimeter) instead of layers; trusting east-west traffic implicitly.
- No logging or time sync, so incidents can't be reconstructed.
- Treating TLS/mTLS as optional inside the cluster; no certificate lifecycle management.
- Delaying driver/runtime/CVE patches; running privileged containers by default.
- Scanning or testing networks without authorisation.

## 17. Interview angles

- "Explain defense in depth with a concrete example for a GPU cluster."
- "How does SSH authentication work; what is a host key; what does 'remote host identification has changed' mean; how would you scale key management?" (SSH certificates.)
- "How would you harden an Internet-facing SSH bastion?"
- "What is zero trust and how do you implement microsegmentation in Kubernetes?"
- "How do you mitigate a SYN flood / DNS amplification / HTTP flood?"
- "What are DHCP snooping, DAI and 802.1X?"
- "What is the OODA loop and how does it apply to incident response?"
- "How do you isolate tenants on a shared InfiniBand/RoCE fabric?"
- "What would you check on an exposed BMC?"
- "How do you secure the BGP control plane?"

## Exercises

1. **Threat Modeling, `STRIDE`, Biometrics vs. Rotatable Secrets, and Defense in Depth (`CN` Chapter 21):** (a) Define *threat actor*, *vulnerability*, *exploit*, *attack surface*, *asset*, and *risk* (`likelihood * impact`), and apply `STRIDE` across an AI training and inference cluster; (b) explain why fingerprints and biometrics are a poor sole remote authentication credential (`CN` Ch. 21), and trace the six Defense-in-Depth layers in Section 2.
2. **`AAA` Protocols (`RADIUS` vs. `TACACS+`), `802.1X`, and Layer-2 Switch Security:** (a) Contrast **RADIUS** (`UDP 1812/1813`) and **TACACS+** (`TCP 49`) across transport, packet encryption, and per-command router authorization; (b) match the six Layer-2 attacks (MAC flooding, rogue DHCP, ARP/ND spoofing, rogue STP switch, VLAN hopping, link eavesdropping) to their switch controls (**Port Security**, **DHCP Snooping**, **DAI / RA Guard**, **BPDU/Root Guard**, **native VLAN pruning**, **802.1X**, and **MACsec `802.1AE`**).
3. **DoS / DDoS Mitigation, BGP Traffic Diversion (`NO_PEER`, `NO_ADVERTISE`, `RTBH`), and Control-Plane Protection:** Compare the four DoS classes (*volumetric*, *protocol/state exhaustion*, *application/GPU exhaustion*, and *control-plane CPU flood*) and their mitigations (**BCP 38 / uRPF**, `tcp_syncookies`, **RTBH `65535:666`**, `NO_PEER` / `NO_ADVERTISE` BGP steering, **CoPP**, **GTSM `TTL 255`**, and `TCP-AO` / `HMAC-SHA`).
4. **`SSH` Cryptography, Host-Key Verification, `ProxyJump` vs. Agent Forwarding, `sshd_config` Hardening, and `SSH` Certificates:** (a) Using `audit_sshd_config()` in `code/part02/network_security_zerotrust.py`, audit a server's `sshd_config` and explain why **`ProxyJump` (`-J`)** must replace `AllowAgentForwarding yes` when jumping through a bastion; (b) explain what `REMOTE HOST IDENTIFICATION HAS CHANGED` means, how **SSH CA certificates** (`ssh-keygen -s ca`, `TrustedUserCAKeys`, `@cert-authority`) eliminate TOFU at scale, and how `simulate_fail2ban_window()` models `fail2ban`.
5. **Auditing Exposure with `nmap` / `ss -tulpn` and Zero-Trust Microsegmentation with Kubernetes `NetworkPolicy`:** (a) Why must you run `nmap` from outside a host and compare it against local `ss -tulpn`, and what are the common high-risk AI/infra ports (`111`, `623`, `2375`, `2379`, `6379`, `8000–8002`, `8265`, `8888`, `10250`)? (b) Using `evaluate_k8s_ingress_network_policy()`, explain how the Section 12 `default-deny` + `allow-gateway-to-triton` `NetworkPolicy` enforces Zero Trust (`NIST SP 800-207`) and why you must permit DNS (`UDP/TCP 53`) egress when default-denying egress.
6. **Securing AI-Specific Surfaces (`BMC`s, InfiniBand `P_Key`s, Supply Chain) and Boyd's `OODA` Loop:** (a) Using `evaluate_ib_pkey_communication()`, evaluate whether InfiniBand ports with 16-bit Partition Keys `(0x8042, 0x8042)`, `(0x8042, 0x8043)`, `(0x0042, 0x0042)`, and `(0x0042, 0x8042)` can communicate, and state the hardening rules for out-of-band **BMCs** (`IPMI 623` / Redfish `443`); (b) apply Colonel John Boyd's **OODA loop** (*Observe, Orient, Decide, Act*) to an alert showing unexpected outbound traffic from a GPU training node.

## Checkpoint questions (20)

<details>
<summary>1. Define Attack Surface, Vulnerability, Exploit, and Risk, and state the six categories of `STRIDE`.</summary>

- **Attack surface**: every reachable entry point an attacker can interact with (open ports, APIs, BMCs, supply chain, users).\n- **Vulnerability**: a weakness in design, implementation, configuration, or operations.\n- **Exploit**: the specific tool or technique that leverages a vulnerability.\n- **Risk**: **`Likelihood * Impact`** of an adverse event.\n- **`STRIDE`**: **S**poofing identity, **T**ampering with data, **R**epudiation, **I**nformation disclosure, **D**enial of service, and **E**levation of privilege.
</details>

<details>
<summary>2. Why does `CN` Chapter 21 warn against using biometrics as a standalone remote authentication credential?</summary>

Biometrics (fingerprints, face scans, iris patterns) violate two core properties of cryptographic secrets: (1) they are **not secret** (you leave your fingerprints on surfaces and your face on cameras everywhere), and (2) once digitized into a backend database and stolen in a breach, **you cannot rotate or revoke your fingers**. Biometrics should only unlock a local hardware enclave (`TPM` / Secure Enclave / FIDO2 key) that signs challenges with a rotatable private key.
</details>

<details>
<summary>3. What are the three network security problem areas, and how does Defense in Depth work across them (`CN` Chapter 21)?</summary>

The three problem areas are **(1) Access Control** (only authorized principals reach data), **(2) Data Confidentiality and Integrity** (in transit and at rest), and **(3) Service Availability** (resisting DoS). Because any single layer can be bypassed or misconfigured—and deep inspection at line rate is expensive—**Defense in Depth** places overlapping controls at every boundary (edge ACLs + RPKI/BCP38 -> stateful firewall/WAF -> VRF/VLAN/NetworkPolicy segmentation -> mTLS/RBAC service auth -> encryption at rest + continuous telemetry/exfiltration monitoring), forcing an attacker to cross multiple independent grids while giving defenders time to detect and contain.
</details>

<details>
<summary>4. Compare `RADIUS` and `TACACS+` in `AAA` (*Authentication, Authorization, Accounting*).</summary>

- **`RADIUS` (`UDP ports 1812 / 1813`, RFC 2866)**: designed for **network access authentication** (`802.1X` switch ports, WPA-Enterprise Wi-Fi, VPNs); combines authentication and authorization into one reply and **encrypts only the password attribute** in the packet (protect with RadSec/TLS or IPsec).\n- **`TACACS+` (`TCP port 49`)**: designed for **network device administration** (SSH into switches/routers); separates authentication, authorization, and accounting, **encrypts the entire packet body**, and supports **per-command authorization and audit logging** (controlling which exact CLI commands an engineer may run).
</details>

<details>
<summary>5. Compare a Stateless Packet Filter (`ACL`), a Stateful Firewall (`conntrack`), an `NGFW` / `WAF`, and Microsegmentation (`NetworkPolicy`).</summary>

- **Stateless ACL**: checks individual packet headers (`src/dst IP`, protocol, L4 ports, TCP `SYN`/`ACK` flags) in switch TCAM at line rate with zero connection memory.\n- **Stateful Firewall (`nftables` / `iptables` `ct state`)**: tracks active connection 5-tuples in `conntrack`, automatically permitting `ESTABLISHED,RELATED` return packets while dropping unsolicited inbound traffic.\n- **NGFW / WAF**: terminates/inspects L7 payloads for SQLi, SSRF, prompt/API abuse, and IPS signatures.\n- **Microsegmentation (`Kubernetes NetworkPolicy`, Cilium eBPF, VXLAN `GBP`)**: enforces workload-to-workload rules between individual pods/containers based on cryptographic/orchestrator **identity labels** rather than static IP subnets.
</details>

<details>
<summary>6. Why is Egress Filtering just as important as Ingress Filtering on GPU cluster nodes?</summary>

If an attacker compromises a container or dependency via a supply-chain CVE or RCE, their immediate next steps are **command-and-control (`C2`) callbacks**, downloading stage-2 payloads, and **exfiltrating model weights or training data**. Default-deny **egress filtering** (permitting GPU nodes to reach only internal storage, internal DNS, and an approved private artifact mirror) breaks reverse shells and blocks data exfiltration.
</details>

<details>
<summary>7. Match the four DoS/DDoS classes to their primary mitigations, including `BCP 38`, `RTBH`, and `NO_PEER` / `NO_ADVERTISE` (`CN` Chapter 21).</summary>

- **Volumetric floods** (UDP reflection/amplification via DNS/NTP): **BCP 38 / uRPF** ingress anti-spoofing at the network edge, Anycast + upstream scrubbing centers, **Remote-Triggered Black Hole (`RTBH`, community `65535:666`)**, and BGP **`NO_PEER` / `NO_ADVERTISE`** communities to divert traffic off congested peering links.\n- **Protocol / state exhaustion** (TCP `SYN` floods, conntrack exhaustion): **`tcp_syncookies = 1`**, SYN rate limits, and stateless edge ACLs.\n- **Application / GPU exhaustion** (expensive LLM prompts): API authentication, per-tenant token-bucket rate limits, `max_tokens` caps, and admission control.\n- **Control-plane CPU floods** (ARP/ICMP/BGP punts): **Control-Plane Policing (`CoPP`)**, **GTSM (`TTL = 255`)**, and `TCP-AO` / `HMAC-SHA`.
</details>

<details>
<summary>8. How does SSH authenticate both the server and the user, and what does the `REMOTE HOST IDENTIFICATION HAS CHANGED` warning mean (`HLW` Chapter 10)?</summary>

First, the server proves its identity using its **host key pair** (`/etc/ssh/ssh_host_ed25519_key`); on first connection (**Trust On First Use, `TOFU`**), the client records the server's public key in `~/.ssh/known_hosts`. Next, over an ephemeral Diffie-Hellman encrypted channel, the user proves possession of their private key (`~/.ssh/id_ed25519`) by signing a challenge verified against `~/.ssh/authorized_keys` on the server. If the server's presented host key ever differs from `~/.ssh/known_hosts`, SSH aborts with **`REMOTE HOST IDENTIFICATION HAS CHANGED`**—which means either the server was legitimately reinstalled/re-keyed OR an attacker is performing an active **Man-in-the-Middle (`MitM`)** attack. Always verify the new fingerprint out of band (`ssh-keygen -lf` via console) before running `ssh-keygen -R <host>`.
</details>

<details>
<summary>9. Why is `AllowAgentForwarding yes` dangerous when connecting through a bastion/jump host, and why should you use `ProxyJump` (`ssh -J`) instead?</summary>

With **SSH Agent Forwarding (`ssh -A`)**, sshd creates a Unix domain socket on the intermediate host pointing back to the `ssh-agent` on your laptop; **anyone with root access on that intermediate host can hijack that socket and use your keys to authenticate to every other server you have access to**. With **`ProxyJump` (`ssh -J bastion user@gpu01`)**, SSH opens a TCP port-forward through the bastion and performs the **end-to-end SSH handshake directly between your laptop and `gpu01`**—so your private key and agent socket are never exposed to the bastion.
</details>

<details>
<summary>10. How do `SSH Certificates` (`ssh-keygen -s`) solve `known_hosts` TOFU and `authorized_keys` sprawl across a 1,000-node GPU cluster?</summary>

Instead of copying static public keys into `~/.ssh/authorized_keys` on 1,000 nodes and maintaining 1,000 host keys in every engineer's `known_hosts`:\n- **Host CA**: signs each node's host public key (`HostCertificate`); engineers add a single **`@cert-authority *.cluster.example.com <CA-pub-key>`** line to `known_hosts` to trust any node signed by the Host CA without TOFU prompts.\n- **User CA** (Vault, `step-ca`, Teleport): after an engineer logs in with SSO + MFA, issues a **short-lived user certificate** (e.g., valid for `8` hours, `-V +8h`) signed by the User CA; every node's `sshd_config` sets **`TrustedUserCAKeys /etc/ssh/user_ca.pub`**, requiring zero per-user `authorized_keys` files on nodes and expiring access automatically.
</details>

<details>
<summary>11. List the eight essential `sshd_config` hardening directives for production Linux servers.</summary>

(1) `PermitRootLogin no` (or `prohibit-password`), (2) **`PasswordAuthentication no`** and `KbdInteractiveAuthentication no` (keys/certificates only), (3) `PubkeyAuthentication yes` / `AuthenticationMethods publickey`, (4) `AllowGroups ssh-users`, (5) **`AllowAgentForwarding no`**, (6) `X11Forwarding no` and `AllowTcpForwarding no` (unless explicitly matched), (7) `MaxAuthTries 3` and `LoginGraceTime 20`, and (8) `LogLevel VERBOSE` (to log which key fingerprint authenticated). Always test with **`sudo sshd -t`** before reloading while keeping an existing root session open.
</details>

<details>
<summary>12. What does `fail2ban` do, and why is it NOT a substitute for `PasswordAuthentication no` (`HLW` Chapter 10)?</summary>

`fail2ban` tails `/var/log/auth.log` or `journald` and temporarily adds an `nftables`/`iptables` drop rule when an IP exceeds `maxretry` failed logins within `findtime`. While `fail2ban` cuts log spam and brute-force CPU load, a distributed botnet of 50,000 IPs can still guess weak passwords at 2 attempts per IP without triggering a single ban (and a shared corporate NAT IP can lock out an entire office); therefore `PasswordAuthentication no` + network allow-listing remain mandatory.
</details>

<details>
<summary>13. Why should you compare local `ss -tulpn` output against an external `nmap` scan (`nmap -p- -sV`), and what AI/cluster ports are most frequently exposed by mistake?</summary>

`ss -tulpn` shows every socket bound on the host (`0.0.0.0:*` vs `127.0.0.1:*`), whereas an external `nmap` scan from another subnet/zone verifies what actually passes through host and perimeter firewalls. Common high-risk exposures on AI clusters include: **unauthenticated Docker daemon (`2375`)**, **Kubernetes `kubelet` (`10250`) and `etcd` (`2379`)**, **Ray Dashboard (`8265`, arbitrary job submission)**, **Jupyter Notebook (`8888`)**, **Triton (`8000–8002`)**, **MLflow (`5000`)**, **Redis (`6379`)**, **`rpcbind`/NFS (`111`/`2049`)**, and **BMC IPMI (`UDP 623`) / Redfish (`443`)**.
</details>

<details>
<summary>14. What are the seven classic Layer-2 LAN attacks and their corresponding switch defenses?</summary>

(1) **MAC table flooding** -> **Port Security** (limit MAC count per port) + storm control;\n(2) **Rogue DHCP server** -> **DHCP Snooping** (drop `DHCPOFFER`/`DHCPACK` on untrusted ports) + **IP Source Guard**;\n(3) **ARP spoofing / poisoning** -> **Dynamic ARP Inspection (`DAI`)** validating ARP packets against the DHCP snooping binding table;\n(4) **IPv6 Rogue Router Advertisement** -> **IPv6 RA Guard** + ND Inspection;\n(5) **Rogue switch / STP root hijack** -> **BPDU Guard** and **Root Guard**;\n(6) **VLAN hopping (double tagging / DTP)** -> disable auto-trunking (`DTP`), set the native VLAN to an unused ID, and explicitly prune allowed trunk VLANs; and\n(7) **Physical link wiretapping** -> **IEEE `802.1AE` MACsec** line-rate hop-by-hop encryption.
</details>

<details>
<summary>15. Define Zero Trust (`NIST SP 800-207`) and explain how Kubernetes `NetworkPolicy` enforces east-west microsegmentation.</summary>

**Zero Trust** eliminates implicit trust based on network location ("inside the cluster VLAN = trusted"): every request between users, devices, and workloads must be strongly authenticated (`mTLS` / `SPIFFE`), authorized by least-privilege policy, and encrypted. In Kubernetes, Pods can talk to every other Pod in the cluster by default; applying a namespace-wide **default-deny `NetworkPolicy`** (`podSelector: {}, policyTypes: [Ingress, Egress]`) blocks all unsolicited east-west traffic until explicit label-based allow rules (such as allowing only `app: gateway` to reach `app: triton` on `TCP 8001`, plus DNS `53` egress) are added and enforced by the CNI (`Cilium`, `Calico`).
</details>

<details>
<summary>16. Why are Out-of-Band `BMC`s (`IPMI` / `Redfish`) and the PXE Provisioning Network the highest-value targets in a bare-metal GPU cluster, and how do you secure them?</summary>

The **BMC** has total hardware control over the server regardless of the host OS: it can mount virtual media, read console memory, reflash BIOS/BMC firmware, and reboot the machine, yet BMCs have a long history of critical vulnerabilities (`IPMI 2.0 RAKP` hash disclosure and `Cipher 0` authentication bypass). Similarly, compromising the **PXE/DHCP/HTTP provisioning server** compromises the boot image of every node in the fleet. Secure them by: placing BMCs on a **strictly air-gapped OOB management VLAN/VRF** reachable **only via hardened jump hosts**, disabling legacy `IPMI-over-LAN` (`UDP 623`) in favor of authenticated **Redfish over HTTPS (`TLS`)**, setting unique per-BMC passwords, patching BMC firmware, and enforcing **UEFI Secure Boot + signed OS images**.
</details>

<details>
<summary>17. How does InfiniBand Partitioning (`P_Key`) isolate tenants in hardware, and how do Full (`0x8000`) and Limited (`0x0000`) memberships work?</summary>

In an InfiniBand fabric, the **Subnet Manager (`OpenSM` / `UFM`)** programs a table of 16-bit **Partition Keys (`P_Key`s)** into every Host Channel Adapter (`HCA`) port (and `M_Key` protects management SMPs):
- **Bits `0..14` (`15` bits)**: the **Partition ID** (`0x0001..0x7FFF`; default partition `0x7FFF`).
- **Bit `15` (`MSB`, `0x8000`)**: the **Membership bit** (`1` = **Full member**, `0` = **Limited member**).
Every IB packet carries its `P_Key` in the Base Transport Header (`BTH`), and the HCA silicon enforces that two ports can communicate **if and only if they share the exact same 15-bit Partition ID AND at least one of the two ports is a Full member** (allowing multiple untrusted tenants assigned *Limited* membership in a shared storage partition to talk to a *Full*-member storage server while being hardware-blocked from talking to each other).
</details>

<details>
<summary>18. How do NVIDIA BlueField `DPU`s strengthen multi-tenant security on bare-metal GPU servers?</summary>

When a tenant has root access on a bare-metal GPU host, any software agent, `iptables` rule, or CNI running inside the host kernel can be disabled by the tenant. A **BlueField DPU** runs an independent Linux OS and hardware-offloaded Open vSwitch / eBPF / IPsec / RDMA firewall pipeline on a separate Arm complex in front of the physical network ports (**host-isolated / zero-trust mode**), enforcing tenant VRF/EVPN isolation, firewall ACLs, storage authentication, and line-rate encryption outside the tenant's reach.
</details>

<details>
<summary>19. What are the unique security threats to LLM Inference APIs and AI Supply Chains?</summary>

- **Inference APIs**: GPU resource-exhaustion DoS (long-context prompts), unauthorized model/weight extraction, prompt injection, and **SSRF / data exfiltration via tool-calling agents** (requiring strict egress allow-lists on agent sandboxes, per-key token quotas, and prompt-redacted logging).\n- **AI Supply Chain**: malicious pickle weights (`torch.load` arbitrary code execution—prefer **`safetensors`** plus SHA-256 signature verification), unverified container images (sign with **`cosign`** and enforce in Kubernetes admission), and container-escape CVEs in GPU drivers / **`nvidia-container-toolkit`** (patch promptly and avoid `--privileged`).
</details>

<details>
<summary>20. Explain Colonel John Boyd's `OODA` Loop (`Observe, Orient, Decide, Act`) as a network security operations model (`CN` Chapter 21).</summary>

Originally developed by USAF Colonel John Boyd for air combat, the **OODA loop** models security operations as a race of decision cycles against the attacker:\n1. **Observe**: collect high-signal telemetry (NetFlow/IPFIX, DNS logs, `auditd`/`Falco` GPU process alerts, SSH/API auth logs, BGP/RPKI monitors) without drowning in unindexed noise;\n2. **Orient**: correlate observations against asset inventory, baseline behavior, and threat models (`MITRE ATT&CK`) to overcome cognitive bias and answer *"is this real, and what is the blast radius?"*;\n3. **Decide**: select a pre-rehearsed response playbook (quarantine VLAN/NetworkPolicy, revoke SSH/SPIFFE cert, trigger BGP `RTBH`) without freezing in self-doubt; and\n4. **Act**: execute the containment (ideally automated), observe the effect, and feed lessons back into hardening.
</details>

## Sources and review notes

- **Sources read in full:**
  - `computer-networking-problems-and-solutions` — Russ White and Ethan Banks, *Computer Networking Problems and Solutions*, **Chapter 10: Transport Security** (developed in Chapter 2.10) and **Chapter 21: Security: A Broader Sweep** (the biometric identity conundrum, vocabulary threat actor / exploit / vulnerability / attack surface, the 3 problem areas access / confidentiality / availability, defense in depth and filtering cost, AAA RADIUS / TACACS+ / 802.1X, data protection, DoS/DDoS and BGP `NO_PEER` / `NO_ADVERTISE` / `RTBH` traffic diversion, and Colonel John Boyd's OODA loop).
  - `how-linux-works-3rd-edition` — Brian Ward, *How Linux Works*, 3rd ed., **Chapter 9** (firewall strategy) and **Chapter 10: Network Applications and Services** (Secure Shell public-key cryptography, `sshd_config` and host keys, `fail2ban`, `known_hosts` warnings, `scp`/`sftp`, `inetd`/`xinetd` and TCP wrappers, port scanning with `nmap`, RPC `rpcbind`, network security rules of thumb, typical vulnerabilities, and security resources).
  - `production-kubernetes` — Josh Rosso et al., *Production Kubernetes*, **Chapters 7 and 8**, and `networking-and-kubernetes` — James Strong and Vallery Lancey, *Networking and Kubernetes*, **Chapters 4 and 6** (Kubernetes `NetworkPolicy` microsegmentation and secret management).
- **Run here:** `python3 code/part02/network_security_zerotrust_lab.py` (12 passed, 0 failed).
- **Explicitly labelled inferences:** The `sshd_config` hardening snippet, SSH CA certificate workflow, Kubernetes `NetworkPolicy` YAML (`default-deny` + `allow-gateway-to-triton`), and AI-cluster security checklist (BMC/Redfish OOB isolation, InfiniBand 16-bit `P_Key` full/limited membership, `safetensors`/`cosign` supply-chain controls, and BlueField DPU host isolation) synthesize NIST SP 800-207 (Zero Trust), RFC 2866, OpenSSH manuals, and NVIDIA security documentation (cross-referenced with Chapters 1.21, 2.6, 2.9, 2.10, 2.15–2.17, 2.20, 2.23, and 2.28–2.29, plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, and 40).
- **Not verified on live hardware:** All interactive VM and Kubernetes commands (`ssh`, `ssh-keygen`, `sshd -t`, `fail2ban-client`, `nmap`, `hping3`, `kubectl`) are marked (untested here) and must be executed ONLY on disposable lab VMs or networks you own or have written authorization to test.
