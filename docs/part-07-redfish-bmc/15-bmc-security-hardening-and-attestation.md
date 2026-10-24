---
id: "c07-15"
title: "7.15 BMC security hardening and attestation"
sidebar_label: "7.15 BMC security hardening and attestation"
sidebar_position: 15
description: "How to secure the most privileged part of a GPU server: network isolation, switching off unused services, certificates (GenerateCSR and ReplaceCertificate, tested with a real lab CA), accounts and policy, a hardening audit tool, UEFI Secure Boot through Redfish, firmware signing and downgrade risks, and what attestation (SPDM and TPM measurements) is and is not"
status: "drafted"
tier: "1b"
level: "A"
lab_venue: "GCP / GKE"
---

# 7.15 BMC security hardening and attestation

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted. `code/part07/hardening_lab.py` ran **29 checks**, all passed, with **real TLS** (the mock serves HTTPS with TLS 1.2 or newer) and a real throw-away certificate authority made with `openssl`. The DMTF interoperability validator checked my hardening profile: 11 of 17 checks passed on the default mock and **17 of 17** after `rf_harden.py apply`. Attestation was only **read** (a DMTF example tree). Nothing was tested on a real BMC, so vendor behaviour (what a DGX BMC lets you switch off, how it stores certificates, which anti-rollback rules apply) is **not verified** |

## Why this matters for AI infrastructure

The BMC is the most privileged computer in the rack. It can power the server on and off, mount a virtual disk, open a console, rewrite firmware and read hardware state, and it works below the operating system where your normal security tools cannot see. The user's Security volume (volume 18) puts it plainly: if the BMC is compromised, the server is lost, and if firmware is compromised, no operating system reinstall helps. GPU clusters also hold valuable data and expensive hardware, so they attract attackers. This chapter closes Part 7 with the controls that matter and tests of the ones you can test.

## Prerequisites and outcomes

You need chapters 7.1 to 7.4, 7.10 and 7.12. After this chapter you can:

- explain the BMC threat model in simple words
- list the layers of BMC defence and what each stops
- replace a BMC's self-signed certificate through Redfish, step by step
- audit and fix management protocols and account policy, safely
- use Secure Boot through Redfish, and explain Setup Mode versus User Mode
- explain firmware signing, downgrade risk and tenant root access
- explain what attestation is, read it, and say what is still missing

## 1. The threat in plain words

An attacker who reaches your BMC can do things an attacker on the host cannot:

| What they can do | Why it hurts |
|---|---|
| power off or reset servers | an outage, or repeated disruption of a long training run |
| attach virtual media and boot their own image | takes the host without touching its disk |
| open the console or send keystrokes (KVM) | see and control the machine |
| flash firmware | a persistent implant that survives reinstalls |
| read hardware state and logs | learn about the cluster |
| change settings (boot order, BIOS, accounts) | quiet persistence |

The notes (volume 10) add that a compromised BMC can steal secrets from memory through DMA, or destroy hardware by changing thermal thresholds. The Security volume says "the architectural mandate" is that the BMC network must be isolated from the AI data network, on a dedicated out-of-band network or VLAN with firewall rules, reachable only through a VPN with multi-factor authentication by authorised infrastructure administrators. The next section is that mandate in practice.

## 2. Layers of defence

```mermaid
flowchart TB
    L1["1. Network isolation<br/>OOB network, no user access, VPN plus MFA bastion"]
    L2["2. Fewer doors<br/>switch off HTTP, Telnet, IPMI over LAN, SSDP"]
    L3["3. Identity<br/>per-purpose accounts, no factory passwords, lockout, no shared admin"]
    L4["4. Encrypted and verified channel<br/>HTTPS with your CA, TLS 1.2+, sessions not Basic"]
    L5["5. Trusted firmware<br/>signed images, controlled update path, anti-rollback where supported"]
    L6["6. Host boot integrity<br/>UEFI Secure Boot, measured boot"]
    L7["7. Evidence<br/>NTP, central logs, config audit, attestation"]
    L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7
```

No single layer is enough. If layer 1 fails (someone plugs into the OOB switch), layers 2 to 4 still stand. If a password leaks, lockout and per-purpose roles limit damage.

### Layer 1: network isolation

The DGX GB300 SuperPOD reference architecture shows how NVIDIA builds it: a separate **out-of-band Ethernet fabric** of SN2201 switches that connects "the management ports of all devices", rolled up into a dedicated VXLAN at the spine layer of each scalable unit, with no case where a non-privileged user needs access, so it is secured by logical network separation. It carries IPMI traffic and the management of the InfiniBand and NVLink fabrics. SCL (the SysAdmin book, chapter 10) gives the same advice in a few words: the IPMI network is "not really secure", so put it on a dedicated physical network or a dedicated VLAN enabled only on management nodes.

Rules to follow: no route from user or data networks to BMC addresses; reach BMCs only from a hardened management host (bastion) with MFA; log all access to it; firewall BMC subnets in both directions (BMCs should not browse the internet either, other than to approved NTP and log servers).

### Layer 2: switch off what you do not use

Each open service is a possible door. The `ManagerNetworkProtocol` resource (chapter 7.7) lists them: `HTTP`, `HTTPS`, `IPMI`, `SSH`, `Telnet`, `SNMP`, `SSDP`, `NTP`, `KVMIP`, `VirtualMedia` and more. A hardened policy turns off plain `HTTP`, `Telnet`, `IPMI` (the old, weakly protected remote protocol, chapter 7.1) and `SSDP` discovery (chapter 7.2), and turns on `NTP`. The notes' example does this with one `PATCH`:

```json
{ "IPMI": {"ProtocolEnabled": false}, "Telnet": {"ProtocolEnabled": false}, "HTTP": {"ProtocolEnabled": false}, "SSH": {"ProtocolEnabled": true, "Port": 22} }
```

Think before you switch off: BCM may use IPMI for some functions on your BMCs (the BCM manual says IPMI, iLO, DRAC, CIMC and Redfish are all supported BMC interface types), and virtual media or KVM may be needed during repairs. Switch off what you have tested without, and keep a documented way back (chapter 7.14 scenario 3).

### Layer 3: identity

All of chapter 7.4 applies. In short: no factory passwords (the audit checks `PasswordChangeRequired`), a lockout threshold, a minimum password length, per-purpose accounts with the lowest role that works, personal accounts for people, secrets in a secret manager, and an audit of credential drift across the fleet (chapter 7.1).

### Layer 4: a verified HTTPS channel

Traffic to the BMC carries passwords, tokens and firmware, so it must be encrypted **and the client must check who answers**, or an attacker on the path can pretend to be the BMC. That needs a certificate your clients trust. Here is the full flow, which I ran.

## 3. Replacing the certificate through Redfish

A BMC ships with a self-signed certificate. The standard way to replace it (chapter 7.4, correcting the notes) uses two actions of the `CertificateService`:

```mermaid
sequenceDiagram
    participant A as Admin tool
    participant B as BMC (Redfish)
    participant C as Your CA
    A->>B: POST GenerateCSR (CommonName, SAN, key size)
    Note over B: BMC makes a NEW private key and keeps it inside
    B-->>A: 200, CSRString (a certificate request)
    A->>C: sign the request
    C-->>A: signed certificate (PEM)
    A->>B: POST ReplaceCertificate (CertificateUri, CertificateString, PEM)
    Note over B: BMC checks the certificate matches its key, then starts using it
    B-->>A: 200
    A->>B: new connection, verified against your CA
```

Why this order: the private key is created **inside the BMC** and never travels, so only the public request and the signed certificate cross the network. In my mock the lab proves each rule:

| Check in the lab | Result |
|---|---|
| a client that trusts the lab CA refuses the BMC's self-signed certificate | yes, `CERTIFICATE_VERIFY_FAILED` |
| `ReplaceCertificate` with no pending request | 400, because the key must be made inside the BMC |
| `GenerateCSR` without `CommonName` | 400 |
| `GenerateCSR` returns a PEM request and no private key | yes |
| a valid certificate for a **different** key | 400, "does not match the pending key" |
| garbage text instead of a certificate | 400 |
| the CA-signed certificate | 200; **new connections** now verify with no `-k` |
| the `Certificate` resource afterwards | issuer `Lab Root CA`, subject `bmc-lab` |
| a user without `ConfigureManager` | 403 |

The `Certificate` resource shows `Issuer`, `Subject`, `ValidNotBefore`, `ValidNotAfter`, `SerialNumber`, `Fingerprint` and `KeyUsage`. Plan for expiry: the hardening audit warns when less than 30 days remain (it flagged my own 30-day lab certificate as expiring in 29 days). In a real fleet, issue certificates with a lifetime your automation can renew, and monitor the expiry date (`rf_harden.py audit`).

What I did not test: how real DGX or OEM BMCs handle `GenerateCSR` (some BMCs have vendor-specific certificate steps), whether they apply the new certificate without a restart of the web service, and their key algorithm choices.

## 4. The hardening audit tool

`code/part07/rf_harden.py` audits against a policy file (`profiles/bmc_policy.json`) and labels each finding **FIX** (the tool can change it) or **MANUAL** (a person must decide). On my TLS mock, before hardening:

```text
HIGH   FIX    HTTP is enabled (policy: off)
HIGH   FIX    Telnet is enabled (policy: off)
HIGH   FIX    IPMI is enabled (policy: off)
HIGH   MANUAL HTTPS certificate expires in 29 days
HIGH   MANUAL account 'factory' still has PasswordChangeRequired: a factory or reset password is in use
MEDIUM FIX    SSDP is enabled (policy: off)
MEDIUM FIX    NTP is off or has no servers: log timestamps will drift (chapter 7.11)
MEDIUM FIX    HTTP Basic authentication is Enabled (policy: Disabled)
MEDIUM FIX    MinPasswordLength is 8 (policy: 12)
MEDIUM MANUAL account 'factory' is a default-style administrator name: rename or disable it
MEDIUM MANUAL System_0: UEFI Secure Boot is not active (enable: False, mode: SetupMode)

7 fixable by this tool, 4 need a person
```

Then `rf_harden.py apply --yes` sent seven `PATCH` requests (four protocols off, NTP on with the policy servers, Basic authentication disabled, minimum password length 12), re-audited, and reported `0 fixable finding(s) left`. Safety rules in the tool:

- **Dry run unless `--yes`.**
- **It refuses to switch off the protocol it is connected over.** In the lab, a request to disable HTTP over a plain-HTTP connection is refused with "would lock you out".
- **Accounts, certificates and Secure Boot stay manual**, because the right action depends on your process.
- It re-reads the settings after changing them.

### Checking with DMTF's validator

My `profiles/bmc_hardening.json` states the same target as a DMTF interoperability profile (HTTPS on; HTTP, Telnet, IPMI and SSDP off; NTP on; Basic auth disabled; lockout greater than zero; minimum password length at least 12). Result of `rf_interop_validator` on the default mock: 11 passed, **6 failed** (HTTP, Telnet, IPMI, SSDP, NTP and Basic auth). After `rf_harden.py apply --yes`: **17 passed, 0 failed**. Two independent tools agreeing is a good sign. Remember the lesson from chapter 7.13: boolean values in a profile must be JSON booleans.

### What the tool does not do

It does not read BMC-specific security features: SSH key policy, LDAP or Active Directory integration, role mapping (the schema has `RemoteRoleMapping`), multi-factor authentication settings, or the `SecurityPolicy` resource (TLS and SPDM policy: allowed versions, algorithms, trusted and revoked certificates, shown in DMTF's example). A mature audit adds these, using the resources your BMC really has.

## 5. Firmware trust

The Security volume's chapter on hardware and firmware trust explains the idea for beginners: firmware is the small software inside each part (GPU, NIC, BIOS, BMC). If an attacker replaces it with a malicious copy, it survives an operating system reinstall. Defences:

1. **Signed firmware and a hardware root of trust.** A security chip checks the signature of the next stage before it runs, forming a chain (hardware root of trust, BIOS, bootloader, kernel). The notes say NVIDIA GPUs and ConnectX NICs verify signatures of their own firmware, so an unsigned or altered image will not initialise. (From the notes; not verified by me.) The BCM firmware lists show the ERoT (external root of trust) chips as separate updatable items (chapter 7.10).
2. **A controlled update path.** The notes' customer scenario is useful: users with `sudo` on the host could run firmware tools (`nvfwupd`, `mstflint`) and flash devices. The notes' answer: remove tenant root access, run user tools in unprivileged containers, and allow firmware updates only from change-managed tooling using vendor-signed images. The notes also stress that device firmware is signed by the **vendor**, not by your CA, so what you control is **who may run the update path**.
3. **Downgrade resistance.** A signed but old, vulnerable image is still a valid image. The notes recommend checking each device's documentation for anti-rollback support. Redfish helps in two ways: `ForceUpdate` is the switch that bypasses update policies (chapter 7.10), so limit it to a role or process; and the inventory lets you detect an unexpected old version (`rf_firmware.py drift`).
4. **Provenance.** Take images only from the vendor, verify hashes and signatures where the vendor gives them, and keep the update log (task messages, chapter 7.10).

In Redfish terms, the BMC's role is limited to what the vendor exposes. Redfish does not define "make firmware read-only" as a standard action, so lockout features are vendor specific.

## 6. UEFI Secure Boot through Redfish

Secure Boot is for the **host** firmware: it only runs bootloaders and kernels signed by keys in its databases. Redfish exposes it under the system:

- `SecureBoot`: `SecureBootEnable` (what you want), `SecureBootCurrentBoot` (what is active now), `SecureBootMode` (`SetupMode`, `UserMode`, `AuditMode`, `DeployedMode`), and `SecureBootDatabases`;
- `SecureBootDatabases`: `PK` (platform key), `KEK`, `db` (allowed signatures) and `dbx` (forbidden signatures), each with `Certificates` and `Signatures` collections;
- action `SecureBoot.ResetKeys` with `ResetAllKeysToDefault`, `DeleteAllKeys` or `DeletePK`.

:::note Correction to my notes
The notes' scenario 5 says the signed boot chain needs "a trusted key enrolled in the BMC's secure boot database (db)". The key databases belong to the **host's UEFI firmware**, and Redfish only exposes them under the system's `SecureBoot` resource. The BMC is the management channel, not the owner of those keys.
:::

My lab proves the mechanics that surprise people:

```text
PASS  enabling Secure Boot changes the setting but not the running state (CurrentBoot stays Disabled)
PASS  after a restart it is STILL not enforced because no platform key is enrolled (SetupMode)
PASS  ResetKeys to the default keys puts the system in UserMode
PASS  after the next restart Secure Boot is enforced
```

Meaning: setting `SecureBootEnable` to true is not enough. The change applies at the next boot (like a BIOS setting, chapter 7.14), and Secure Boot only protects when a platform key is enrolled (User Mode). A checker must read `SecureBootCurrentBoot`, not only `SecureBootEnable`. My audit does.

For the operating system side, the notes describe the usual Linux route: a signed shim (signed by the Microsoft UEFI CA) that loads your signed bootloader, a kernel signed with your own key (a machine owner key enrolled with `mokutil`), HTTPS instead of plain HTTP for the boot transfer, and Redfish to confirm that Secure Boot is on. That flow is standard Linux practice, but I did not test it, and DGX images may ship their own signing arrangements.

## 7. Attestation: what it is, and what I did not do

**Attestation** means proving what software and firmware a device is running. Two Redfish mechanisms, both under `ComponentIntegrity`:

- **SPDM** (Security Protocol and Data Model): a device (the *responder*) can report **measurements** (hashes of its firmware and configuration) and sign them with a key whose certificate chains to the vendor.
- **TPM**: a trusted platform module keeps **PCR** values (running hashes of what booted) and can sign them.

A `ComponentIntegrity` resource reports its type and version, whether it is enabled, which component it protects (`TargetComponentURI`), the measurements, and the result of checking the device's identity. Actions: `SPDMGetSignedMeasurements` (give a 32-byte nonce, get a signed statement over chosen measurements) and `TPMGetSignedMeasurements`. The manager's `SecurityPolicy` sets the allowed SPDM and TLS versions and algorithms and the trusted and revoked certificates.

I wrote a small read-only lister, `rf_attest.py`, and ran it on DMTF's rack-server example:

```text
4 ComponentIntegrity resource(s), 1 SecurityPolicy resource(s)
  TPM-0        TPM   enabled=True  ... measurements= 4 identity=Success health=OK
  USB-Integrity SPDM enabled=False ... measurements= 0
  SS-SPDM-1    SPDM  enabled=True  ... measurements= 3
  SS-SPDM-0    SPDM  enabled=True  ... measurements= 3
  SecurityPolicy: SPDM enabled=True verify_certificate=True; TLS client allowed versions=['1.2', '1.3']
```

**What this is not.** Listing measurements is not attestation. Real attestation needs: (1) a fresh nonce from you, (2) a signed answer from the device, (3) checking the signature through a certificate chain you trust, and (4) comparing the measurements with known-good values from the vendor, held somewhere an attacker cannot change. I did none of steps 2 to 4 and I have no known-good values for any NVIDIA part. Whether and how DGX, HGX and GB200 BMCs expose attestation through Redfish is **not verified**. Use `rf_attest.py` only as a way to see what your BMC offers.

## 8. A BMC security checklist

1. BMC and OOB switch management on an isolated network; access only through a bastion with MFA; no route from tenant networks.
2. Change all factory passwords at first contact; handle `PasswordChangeRequired`.
3. Per-purpose accounts and roles; a personal account for each person; lockout and password length set.
4. HTTPS only, TLS 1.2 or newer, certificates from your CA, expiry monitored; clients verify (never `-k`).
5. Basic authentication off; sessions on; sessions closed after use.
6. HTTP, Telnet, IPMI over LAN and SSDP off unless a documented need exists; NTP on.
7. Firmware only from vendor-signed images through change-managed tooling; `ForceUpdate` restricted; drift checked nightly (chapter 7.10).
8. Host: Secure Boot active (read `SecureBootCurrentBoot`); tenants without root on hosts.
9. Logs centralised, clocks right (chapter 7.11); events subscribed (chapter 7.5).
10. A tested recovery path for a locked-out or bricked BMC (chapter 7.14).
11. Re-run the audit and the profile after every firmware update, because updates can reset settings.

## 9. Exercises

1. Run `hardening_lab.py`. For each of the 29 checks write down which layer of section 2 it tests.
2. Edit `profiles/bmc_policy.json` to also require `SSH` off and rerun the audit. What must you check before switching SSH off on a real BMC?
3. Make a CSR through `GenerateCSR` with two alternative names. Sign it with the lab CA (`tls_setup.sign_csr`) and show that a client using `localhost` and one using `127.0.0.1` both verify.
4. Reproduce the self lock-out check: connect over plain HTTP and try to disable HTTP.
5. Write the policy text for what your team allows tenants to do on GPU hosts regarding firmware tools. Which part is a technical control and which is a process?
6. Pick one `ComponentIntegrity` resource in DMTF's example and write down what a verifier would need to check it.

## 10. Interview angles

- "How do you secure BMCs in a GPU cluster?" Isolated management network with a bastion and MFA, services minimised, per-purpose accounts, verified HTTPS from your CA, signed firmware only through controlled tooling, Secure Boot on hosts, central logs and regular audits.
- "How do you replace the BMC certificate at scale?" GenerateCSR so the key never leaves the BMC, sign, ReplaceCertificate, verify with a client that trusts your CA, monitor expiry.
- "Why check `SecureBootCurrentBoot` and not `SecureBootEnable`?" The setting applies at the next boot, and with no platform key enrolled nothing is enforced.
- "What is attestation and what do you need beyond Redfish?" Signed measurements with a nonce, a trusted certificate chain, and known-good values.
- "A data scientist has sudo on the GPU hosts. What is the risk?" They can run firmware tools and flash devices. Remove root, containerise, control the update path.

## 11. Checkpoint questions (20)

1. Name four things an attacker can do through a BMC.
2. What does the SuperPOD reference architecture say about the OOB network?
3. List the seven layers of defence in this chapter.
4. Why not leave Telnet or plain HTTP on?
5. Why does `GenerateCSR` come before `ReplaceCertificate`?
6. Why does the BMC make the private key itself?
7. What happens if the certificate does not match the pending key?
8. Does the new certificate apply to existing connections?
9. Which findings can `rf_harden.py` fix and which does it leave to people?
10. Why does it refuse to disable the protocol it is using?
11. What does `HTTPBasicAuth: Disabled` mean for scripts?
12. What are `PK`, `KEK`, `db` and `dbx`?
13. Why can `SecureBootEnable: true` still mean no protection?
14. Whose key databases are the Secure Boot databases: the BMC's or the host's?
15. What is a hardware root of trust?
16. Why is device firmware signed by the vendor, not your CA?
17. What is a downgrade attack?
18. What does `ForceUpdate` bypass?
19. What do SPDM and TPM attestation each report?
20. What four things does real attestation need that `rf_attest.py` does not do?

## 12. Sources and review notes

- **Redfish Specification DSP0266 v1.21.0:** TLS and certificates (13.1), sensitive data (13.2), authentication and sessions (13.3), authorization (13.4), account service (13.5), discovery with SSDP and its disable rule (12.4).
- **Redfish Resource and Schema Guide and the official JSON Schemas:** `CertificateService` (`GenerateCSR`, `ReplaceCertificate`), `Certificate`, `ManagerNetworkProtocol`, `AccountService`, `SecureBoot` (modes, `ResetKeys`), `SecureBootDatabase`, `ComponentIntegrity` (SPDM and TPM, signed-measurement actions) and `SecurityPolicy`.
- **NVIDIA-DevOps notes:** volume 18 chapter 2 (hardware and firmware trust: the root of trust chain, the BMC as most dangerous component, the `sudo` customer scenario and the firmware lockdown answer), volume 10 chapter 1 sections 6 and 9 (BMC security commands, scenario 5 on Secure Boot). All unverified against NVIDIA documents; one correction is in section 6.
- **DGX GB300 SuperPOD reference architecture** (out-of-band network design). **Supercomputers for Linux SysAdmins** chapter 10 (separate IPMI network). **BCM 11 Administrator Manual** (BMC interface types, firmware ERoT items).
- **DMTF tools:** Redfish-Interop-Validator 3.0.4 with my profile `bmc_hardening.json`; DMTF example trees for `ComponentIntegrity` and `SecurityPolicy` (commit `fa6d23d9`).
- **Run here:** `hardening_lab.py` (29 checks, real TLS, real lab CA), `rf_harden.py` (audit and apply), `rf_attest.py` (read-only, DMTF example), the interop validator before and after hardening.
- **Not verified:** any behaviour of a real BMC for the actions above, NVIDIA firmware lockdown and anti-rollback features, real attestation on any NVIDIA part, and the Linux Secure Boot flow (shim, MOK) which I only retell.
