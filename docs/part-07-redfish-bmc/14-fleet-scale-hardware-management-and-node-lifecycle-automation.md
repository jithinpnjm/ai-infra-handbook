---
id: "c07-14"
title: "7.14 Fleet-scale hardware management and node lifecycle automation"
sidebar_label: "7.14 Fleet-scale hardware management and node lifecycle automation"
sidebar_position: 14
description: "Putting Part 7 together for a cluster: BIOS settings through the Redfish Settings resource and attribute registry, one-time and continuous boot override, a bring-up script that stops at the first problem and can be re-run, drift management, and the five troubleshooting scenarios from the notes worked through with the tools"
status: "drafted"
tier: "1b"
level: "A"
lab_venue: "GCP / GKE"
---

# 7.14 Fleet-scale hardware management and node lifecycle automation

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted (`lifecycle_lab.py`: 24 checks pass against mock; **untested** on live BMC) |

## Why this matters for AI infrastructure

Racking 128 GPU servers is the easy part. Getting every one of them to the same state, with the same BIOS, firmware and boot setup, proving it, and keeping it that way for years is the hard part. The user's notes say it plainly: a distributed training job runs at the speed of its slowest GPU, so one node with a different BIOS setting or an older firmware is a cluster-wide problem. This chapter turns the primitives of chapters 7.2 to 7.13 into a repeatable **node lifecycle**.

## Prerequisites and outcomes

You need chapters 7.5, 7.7 to 7.12. After this chapter you can:

- change BIOS settings through Redfish, and explain pending versus live
- use the attribute registry to validate a setting before sending it
- use one-time and continuous boot override correctly
- run a bring-up that is safe to repeat and stops on the first problem
- keep a fleet in line with baselines for firmware, BIOS and health
- work through five classic incidents with the right tools

## 1. The fleet mindset in four ideas

1. **Describe the target state in files** (firmware baseline, BIOS target, acceptance profile, account policy), in version control.
2. **Measure the real state** the same way on every node (inventory, hardware, sensors, logs).
3. **Compare and report drift** automatically and often.
4. **Change in small, verified, repeatable steps**, with a human decision before anything risky.

The tools of Part 7 map onto these: `rf_inventory.py`, `rf_hardware.py`, `rf_sensors.py`, `rf_logs.py` measure; `rf_firmware.py drift` and `rf_bios.py plan` compare; `rf_firmware.py update`, `rf_bios.py apply` and `node_lifecycle.py` change; `fleet_run.py` runs a read-only task on many BMCs.

## 2. BIOS settings: live, pending, and the registry

### 2.1 The Settings resource pattern

Some resources cannot change at once. A BIOS setting is read when the machine boots, so a change must be stored until the next reset. The spec's **Settings resource** (DSP0266 9.10) handles it with a fixed pattern:

- The main resource (`Bios`) shows the **live** values.
- It carries an annotation `@Redfish.Settings` with a `SettingsObject` link, the `SupportedApplyTimes`, and the `Time` of the last change.
- You `PATCH` the **Settings object**, never the live resource. The change is stored as **pending**.
- The pending values become live when the apply time comes (here: `OnReset`).

In my lab:

```text
PATCH .../Bios/Settings {"Attributes": {"PowerProfile": "MaxPerf"}}   -> 200, "ResetRequired" message
GET   .../Bios                  Attributes.PowerProfile = Balanced      (live: unchanged)
GET   .../Bios/Settings         Attributes = {"PowerProfile": "MaxPerf"} (pending)
POST  ComputerSystem.Reset GracefulRestart
GET   .../Bios                  Attributes.PowerProfile = MaxPerf       (live now)
GET   .../Bios/Settings         Attributes = {}                         (pending cleared)
```

BCM shows the same three states for a node. In `cmsh`, under `biossettings`, `status` prints a table with **Configured** (what BCM wants), **Pending** (staged on the node) and **Live** (running now). `bios check` lists differences between configured and detected values, and `bios apply` stages the configuration. The manual's example changes the boot mode from UEFI to legacy: set it, commit, `bios apply`, then reset the node for it to become Live. (The BCM book covers it in section 14.5; I read the boot-mode example only.)

:::note Correction to my notes
The notes' example answer to a BIOS `PATCH` shows the message ID `Base.1.8.UpdatePending`. The `UpdatePending` message exists in the **Update** registry, not in the **Base** registry (I checked the registry files). A BMC may use a vendor message, or the Base message `ResetRequired` ("a component reset is required with the Reset action URI ... and ResetType ..."), which my mock uses. Do not match on the exact text. Check the HTTP status and then read the pending object.
:::

### 2.2 The attribute registry

BIOS settings differ so much between platforms that Redfish cannot fix their names. It uses an **attribute registry** (chapter 7.6): a JSON file, named by the `AttributeRegistry` property of `Bios`, that lists each attribute with its display name, type (`Enumeration`, `Integer`, `String`, `Boolean`, `Password`), allowed values or range, default, whether it is read-only or hidden, and whether changing it needs a reset.

A good tool reads the registry first, then validates a value **before** sending it. My `rf_bios.py` does so, and my mock also checks on its side. In the lab:

| Request | Answer |
|---|---|
| value not in the list (`PowerProfile: Turbo`) | 400, `PropertyValueNotInList` |
| unknown attribute | 400, `PropertyUnknown` |
| read-only attribute | 400, `PropertyNotWritable` |
| integer out of range or wrong type | 400 |
| read-only user | 403 |

### 2.3 What to set for AI: the notes' matrix, with cautions

The user's notes list a "production BIOS matrix" for AI nodes. Here it is in my lab's attribute names, with the notes' reasons. The reasons are **claims from the notes that I could not verify**. The final authority is your server vendor's tuning guide for your exact model.

| Setting (lab name) | Factory-style value | Target in the notes | Reason given in the notes |
|---|---|---|---|
| `PowerProfile` | Balanced | MaxPerf | stop CPU cores entering deep sleep states |
| `ProcCStates` | Enabled | Disabled | sleep-state wake-up latency adds jitter to collective operations |
| `SubNumaClustering` | Disabled | Enabled (SNC2 or SNC4 on Intel, NPS4 on AMD) | keep GPU-related memory traffic local and reduce cross-socket traffic |
| `PcieLinkSpeed` | Auto | Gen5 (force) | "Auto" may renegotiate to a lower generation under load |
| `PcieRelaxedOrdering` | Disabled | Enabled | needed for GPUDirect RDMA and GPUDirect Storage performance |
| `PcieMaxPayloadSize` | 256B | 512B | less overhead for 400 Gb/s NICs |
| `IommuMode` | Enabled | Enabled, with kernel parameter `iommu=pt` | needed for SR-IOV, passthrough avoids translation cost |
| `ProcHyperthreading` | Enabled | workload dependent | disable for some strict MPI codes, keep for Kubernetes agents |
| Above-4G decoding | Enabled | Enabled | lets the CPU map the large GPU memory regions |

Notes for your own judgement: a forced `Gen5` link is only sensible if every device on that path supports it; `512B` payload only works if the platform supports it end to end; and "disable C-states" costs power and heat. I have **not** measured any of these. Treat the matrix as a checklist of questions for your vendor.

### 2.4 The tool

```bash
python3 rf_bios.py plan  http://<bmc> <user> <password> --target profiles/ai_node_bios.json
python3 rf_bios.py apply http://<bmc> <user> <password> --target profiles/ai_node_bios.json --yes --reset
```

Output of the real `plan` on my mock (six differences, two already right), and after `apply --yes --reset` the final line is `LIVE and verified`, and a second `plan` shows `0 to change`. `apply` without `--yes` only prints what it would send. The tool changes only the attributes that differ, so it can run again and again (**idempotent**).

## 3. Boot override: one time or forever

To install an operating system over the network you ask the machine to boot from the network once. The `Boot` object of the `ComputerSystem` has:

- `BootSourceOverrideTarget`: `Pxe`, `UefiHttp`, `Hdd`, `BiosSetup`, `Diags` and others (chapter 7.7),
- `BootSourceOverrideEnabled`: **`Once`** (use it at the next boot and then go back to normal), **`Continuous`** (use it every boot) or `Disabled`,
- `BootSourceOverrideMode`: `UEFI` or `Legacy`.

The lab shows both behaviours:

```text
PASS  a 'Once' boot override is used by the next restart and then switches itself off
PASS  the restart after that boots normally (no repeated PXE)
PASS  a 'Continuous' override keeps booting from the network on every restart (a classic provisioning trap)
```

The trap: a `Continuous` network boot left in place makes the node reinstall itself at every restart. Always use `Once` for provisioning, and verify afterwards that the override is `Disabled`. For diagnosing why a network boot fails, use the D-T-B-I chain from chapter 6.22 (DHCP, Transfer, Boot-mode, Image).

## 4. A node lifecycle you can re-run

`code/part07/node_lifecycle.py` takes one node from "racked" to "ready". It runs six steps; each **checks first and skips what is already right**:

| Step | What it does | Stops when |
|---|---|---|
| `inventory` | saves what the BMC reports (evidence) | |
| `health` | runs the sensor and hardware checks from chapters 7.8 and 7.9 | any sensor, link or drive is flagged |
| `firmware` | compares versions with the baseline file | any component differs (updates are a separate, reviewed job, chapter 7.10) |
| `bios` | validates the target against the registry, stages it, optionally restarts and checks it is live | a value or attribute is not accepted, or the settings are not live |
| `boot` | sets a one-time network boot and checks that it was consumed | the override is refused or still set |
| `ready` | writes the record | |

Rules in the code:

- **Dry run by default.** Without `--yes` it stops at the first step that would change something. Without `--reset-ok` it never restarts the host (it stages the change and stops at `pending`).
- **Stop at the first failure**, with a clear reason.
- **A state file** (JSON) keeps each step's result, time and the evidence, so you can fix the cause and run the same command again. The finished steps are re-checked and skipped.

The lab walks through it:

```text
PASS  dry run: stops at the first step that would change something, changes nothing
PASS  with --yes but no permission to restart, it stages and stops at 'pending'
PASS  with --reset-ok it finishes: BIOS live, boot override consumed, node ready
PASS  running it again is harmless: BIOS already matches, nothing is restarted again
PASS  a degraded GPU link stops the run at 'health' and nothing after it is attempted
PASS  after the fault is fixed the same command continues and completes
PASS  firmware drift stops the run at 'firmware' (updates are a separate, reviewed job)
PASS  a BIOS target with an invalid value or an unknown attribute is refused before anything is sent
```

This is deliberately small. A production version adds: a real burn-in step with DCGM diagnostics, NVLink and network tests whose output is attached as evidence; batching and concurrency (chapter 7.12); approval before risky steps; and a link to your inventory or CMDB. The state machine around it, however, is the same.

## 5. Keeping a fleet in line

- **Baselines in git:** one file for firmware, one for BIOS, one for account and protocol policy (chapter 7.15). A change to a baseline is a reviewed change.
- **Scheduled drift reports:** run inventory, firmware drift and hardware checks nightly with the fleet runner and send the exceptions to a ticket queue.
- **Waves for changes:** 1 node, then 1 rack, then 10 percent, then the rest, checking health between waves.
- **Evidence, not memory:** keep every before and after (inventory snapshots, bundles, task results).
- **Never "fix" one node by hand and forget it.** Either make the change everywhere through the baseline or put the node in a documented exception list.
- **RMA'd parts need re-baselining.** The notes' example of replacement nodes with old firmware (chapter 7.10) is exactly this case. A replacement node enters the lifecycle at step 1.

## 6. Five scenarios from the notes, with the tools

These are retold from volume 10 chapter 1. The commands in the notes are real commands whose output on your system will differ. I mark where my Part 7 tools help.

### Scenario 1: "Ghost" throttling in a 64-node job

*All-reduce latency spikes at random; CPU and GPU utilisation look normal.* The notes' three boundaries: (1) PCIe and link health, (2) NVLink error counters, (3) thermal and power throttling.

- PCIe: on the host `dmesg` for AER errors and `lspci -vvv` for `LnkSta`; out of band, **`rf_hardware.py`** shows any link below its maximum (chapter 7.9).
- NVLink: `nvidia-smi nvlink` status and error counters (host side, Part 10).
- Thermal and power: **`rf_sensors.py`** for fans, inlet temperature and supplies (chapter 7.8) and `nvidia-smi` clock event reasons on the host. The notes note that one throttled GPU slows all the others.
- Compare the suspect node with healthy twins using **`rf_firmware.py drift`** (chapter 7.10).

### Scenario 2: Bringing up 128 DGX systems (1,024 GPUs)

The notes' three principles: separate out-of-band network, immutable firmware baseline, automated acceptance gates.

- Out-of-band: dual 1 GbE management switches to every BMC and PDU, with DHCP reservations and HTTP boot rather than TFTP (chapters 7.1 and 6.22).
- Baseline: push BIOS, BMC, GPU, NVSwitch and NIC firmware to the validated bundle and assert it with reads (**`rf_firmware.py`**, **`rf_bios.py`**).
- Gate: only nodes with clean evidence enter the pool. The notes name `dcgmi diag -r 3` (about 15 minutes) and `-r 4` for burn-in, `nvbandwidth` for NVLink, and `ib_write_bw` for the network. That is the part of **`node_lifecycle.py`** you extend.

### Scenario 3: A "bricked" BMC after a bad firmware push

*The BMC does not answer ping, SSH or Redfish. The host is up, fans are at 100 percent.* The notes' recovery order: (1) reset the BMC from the host through the in-band interface (the notes write `ipmitool bmc reset cold`; chapter 7.1 and the firmware steps use `ipmitool mc reset cold`; I believe `bmc` is an alias of `mc` in ipmitool but did not check); (2) if the flash is corrupted, field staff use the chassis BMC reset or a recovery image; (3) a full AC power drain through the PDU. Prevention matters more: update the BMC in a first small wave, keep the recovery procedure written down, and never update BMC firmware on a whole rack at once. Also keep `Manager.Reset` in mind (chapter 7.7): a restart request over Redfish needs a working BMC, so this scenario needs the in-band route.

### Scenario 4: A CUDA error with a clean OS log

Use chapter 7.11: look at the BMC event log and SEL around the time of the crash for memory or PCIe fault events, check GPU ECC counters on the host, and put both on one timeline. A DIMM fault means drain and replace; a GPU fault means a targeted test (the notes name `dcgmi diag`).

### Scenario 5: Moving to UEFI Secure Boot

The notes' steps: signed shim and bootloader, HTTPS boot, a signed kernel (or enrolled owner key), and a Redfish check that Secure Boot is on. Chapter 7.15 covers Secure Boot and corrects one detail of the notes.

## 7. Exercises

1. Run `lifecycle_lab.py`, then read `node_lifecycle.py`. Add a seventh step `accounts` that fails if any account has `PasswordChangeRequired` true.
2. Change `profiles/ai_node_bios.json` to include an attribute that does not exist in the registry. What does `plan` show?
3. Write the BIOS target for a second server model with different attribute names. Where do you find the names?
4. Add a `--wave N` option to a wrapper that runs `node_lifecycle.py` on N nodes at a time with `fleet_run.py`'s worker pool. What should stop the whole wave?
5. Explain, to someone new, why `Continuous` network boot is risky.
6. Design a nightly drift job for 500 nodes: what it reads, what it stores, what raises a ticket.

## 8. Interview angles

- "How do you make sure 500 nodes have identical BIOS settings?" A baseline file, the attribute registry for validation, Redfish Settings objects, reset, and reading the live values back; run it as a repeatable lifecycle.
- "What is the difference between pending and live settings?" Settings are stored until the apply time (usually reset); the main resource shows what is running now.
- "How do you provision safely?" One-time network boot, verify the override is gone, stop on the first failed gate.
- "A job is slow on one node. Where do you start?" Compare that node with a healthy twin: firmware drift, BIOS drift, link speed and width, thermals.
- "What would you automate first?" Inventory and drift detection, because it is read-only and shows the size of the problem.

## 9. Checkpoint questions (20)

1. What are the four ideas of the fleet mindset?
2. What does the Settings resource pattern solve?
3. Which property links `Bios` to its pending settings?
4. What is the difference between pending and live?
5. What does the attribute registry contain?
6. Why validate against the registry before sending?
7. What are BCM's Configured, Pending and Live states?
8. Why are the BIOS attribute names in this chapter only an example?
9. Give two BIOS settings the notes change for AI nodes and the reason given.
10. What is the difference between a `Once` and a `Continuous` boot override?
11. How do you verify that a provisioning override is gone?
12. Why does the lifecycle tool stop at the first failure?
13. What does the state file hold?
14. Why is the run safe to repeat?
15. Why is firmware updating not part of the lifecycle tool?
16. Name three baselines to keep in version control.
17. What is a wave and why use it?
18. What happens to a replacement node's firmware?
19. For the ghost-throttling scenario, which three boundaries does the notes' answer check?
20. Why does the bricked-BMC scenario need an in-band route?

## 10. Sources and review notes

- **Redfish Specification DSP0266 v1.21.0:** the Settings resource and settings annotations (9.10), operation apply time (7.12).
- **Redfish Resource and Schema Guide, official JSON Schemas and registries:** `Bios` v1.2, `AttributeRegistry` v1.5 (attribute types and entries), the Base registry (`ResetRequired`) and the Update registry (`UpdatePending`).
- **BCM 11 Administrator Manual, section 14.5:** the `biossettings` states (Configured, Pending, Live), `bios check`, `bios apply`.
- **NVIDIA-DevOps notes (volume 10 chapter 1):** section 5 (BIOS matrix and Redfish BIOS automation), section 9 (the five scenarios). The notes' BIOS rationale and attribute names (`OperatingPerformance`, `SubNumaClustering` and others) are unverified; I used my own lab names.
- **Chapter 6.22** for provisioning (HTTP boot, D-T-B-I).
- **Run here:** `rf_bios.py` (plan, apply, reset, verify), `node_lifecycle.py`, and `lifecycle_lab.py` (24 checks); the mock's BIOS, registry and attribute resources validate against the official DMTF schemas.
- **Not verified:** real BIOS attribute registries, real apply behaviour on DGX or HGX BMCs, anything about the numerical effect of the BIOS settings, and the burn-in tools (`dcgmi`, `nvbandwidth`, `ib_write_bw`), which I did not run.
