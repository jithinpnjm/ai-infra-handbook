---
id: "c07-10"
title: "7.10 Firmware inventory and the UpdateService"
sidebar_label: "7.10 Firmware inventory and the UpdateService"
sidebar_position: 10
description: "How to see every firmware version on a GPU server, find drift across a fleet, and update firmware safely through Redfish: SimpleUpdate and multipart push, tasks and their messages, staging, activation by BMC reset, host reset or AC power cycle, how BCM does it, and a 46-check lab"
status: "drafted"
tier: "1b"
level: "A"
lab_venue: "GCP / GKE"
---

# 7.10 Firmware inventory and the UpdateService

| | |
|---|---|
| Level | Intermediate to Advanced |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted. `code/part07/firmware_lab.py` ran **46 checks**, all passed, against my teaching mock with **invented** firmware images (a tiny package format I made up so every failure can be produced on purpose). It tests the Redfish update **flow** (inventory, `SimpleUpdate`, multipart push, tasks, staging, activation, errors). It does not test any real firmware or any vendor rule. The component names in the GPU-tray example are copied from the BCM manual's DGX H100 listing. The activation rules per component come from the BCM manual and the user's notes, and are **not verified** against NVIDIA's firmware update guides |

## Why this matters for AI infrastructure

A GPU cluster is a set of parts that must work together: BIOS, BMC, GPU firmware, NVSwitch firmware, NIC firmware, PCIe switches and more. If one node runs older firmware than the rest, it may be slower or may fail in odd ways, and everyone waits for the slowest node. The user's notes tell a story of four replacement nodes with an older GPU firmware that throttled under sustained load and cut the throughput of a 512-GPU job by 14 percent. (The notes' numbers are an illustration, not a measurement.) Two jobs follow from this: know exactly what is installed everywhere (**inventory and drift**), and change it safely (**update**). Redfish does both through one service, and firmware updating is the riskiest thing you do with a BMC, so this chapter is careful.

## Prerequisites and outcomes

You need chapters 7.2 to 7.5 and 7.7. After this chapter you can:

- list all firmware on a machine and compare it with a baseline
- explain the two Redfish ways to send a firmware image
- follow an update task and read its messages
- explain why an update can be finished but not active, and what activates it
- describe how BCM's `firmware` commands do the same work
- write a safe update procedure for a fleet

## 1. What is "firmware" in a GPU server?

Firmware is software stored on a chip inside a part. The user's notes list seven groups that an AI cluster has to keep consistent:

| Group | Why it matters |
|---|---|
| System BIOS or UEFI | boot code, PCIe settings, memory training |
| BMC firmware | the management controller itself (sensor tables, fan curves) |
| GPU VBIOS and firmware | clocks, power and thermal behaviour of each GPU |
| NVSwitch firmware | NVLink routing and error recovery |
| NIC and DPU firmware (ConnectX, BlueField) | RDMA, congestion control |
| PCIe retimer and switch firmware | signal quality for fast links |
| NVMe drive firmware | wear handling and bug fixes |

The BCM manual's DGX H100 example shows how many pieces there really are. After one GPU-tray update it lists these components, each with its own version: `HGX_FW_BMC_0`, `HGX_FW_FPGA_0`, `HGX_FW_ERoT_BMC_0`, `HGX_FW_ERoT_FPGA_0`, four `HGX_FW_ERoT_NVSwitch_n`, `HGX_FW_ERoT_PCIeSwitch_0`, eight `HGX_FW_GPU_SXM_n`, four `HGX_FW_NVSwitch_n`, eight `HGX_FW_PCIeRetimer_n` and `HGX_FW_PCIeSwitch_0`. That is **30** components in the GPU tray alone (ERoT means external root of trust, a security chip). The motherboard tray adds more, such as `CPLDMB_0` and `EROT_BIOS_0`. This is why inventory and baselines must be automatic.

## 2. Inventory: UpdateService and FirmwareInventory

The service root links to `UpdateService`. It links to `FirmwareInventory`, a collection of `SoftwareInventory` resources, one per updatable component. A `SoftwareInventory` has (from the schema):

| Property | Meaning |
|---|---|
| `Id`, `Name` | the component name (Ids are platform specific, like the `HGX_FW_GPU_SXM_1` above) |
| `Version` | the version string |
| `VersionScheme` | `SemVer`, `DotIntegerNotation` or `OEM`, how to compare versions |
| `Updateable` | can the update service change it |
| `SoftwareId` | a vendor label for this software |
| `LowestSupportedVersion` | the oldest version this component accepts |
| `RelatedItem` | links to the device or manager it belongs to |
| `Manufacturer`, `ReleaseDate` | provenance |
| `Status` | `State` (it becomes `Updating` during an update) and `Health` |
| `WriteProtected` | cannot be written |

The `UpdateService` resource itself lists what is possible: the actions `SimpleUpdate` and `StartUpdate`, `MultipartHttpPushUri`, `MaxImageSizeBytes`, and `ServiceEnabled`.

My tool reads it all:

```bash
python3 rf_firmware.py inventory http://<bmc> <user> <password>
```

and the mock prints 34 lines (the four base components and the 30 GPU-tray components), such as `HGX_FW_GPU_SXM_1  HGX_FW_GPU_SXM_1  96.00.70.00.01  updateable=True state=Enabled`.

### Drift: comparing with a baseline

**Drift** means a machine differs from what you decided it should be. Keep a baseline file (component to expected version). The tool compares:

```json
{ "BIOS": "1.28", "BMC": "1.00.0", "HGX_FW_GPU_SXM_5": "96.00.74.00.01" }
```

```bash
python3 rf_firmware.py drift http://<bmc> <user> <password> --baseline baseline.json
```

It reports each line as `ok`, `DRIFT` (version differs), `MISSING` (the baseline names something the machine does not have) or `not in baseline` (the machine has something you did not list). The exit code is non-zero when anything is wrong, so you can use it in a pipeline. Where the baseline comes from is the key policy question: it should be the **validated bundle** from your vendor for your platform, not "whatever is on the first node."

## 3. Two ways to send an image

The spec (12.6.2) defines two methods. A service may offer either or both.

| | SimpleUpdate (pull) | Multipart HTTP push |
|---|---|---|
| Who moves the file | the **BMC downloads** it from a URL you give | **you upload** it in the request |
| Needs a file server | yes, reachable from the BMC | no |
| Request | `POST` the action `UpdateService.SimpleUpdate` | `POST` to `MultipartHttpPushUri` with `multipart/form-data` |
| Parameters | `ImageURI` (required), `TransferProtocol`, `Targets`, `ExcludeTargets`, `ForceUpdate`, user name and password for the file server | a JSON part named `UpdateParameters` (same fields) and a binary part named `UpdateFile` |
| Answer | `202` with a task monitor | `202` with a task monitor; `413` if the image is bigger than `MaxImageSizeBytes`; `411` if a length is required and missing |

**Which to use.** Pull scales well: 100 BMCs fetch the same file from one server in parallel and you send only small requests. Its cost is a file server on the management network that every BMC can reach. Push needs no server but moves the whole image through your script for every machine (the BCM examples show packages of 100 to 135 MB). The legacy `HttpPushUri` also exists but its format is vendor specific.

Parameters you should understand:

- `Targets`: URIs of the inventory items to update. If you give none, the service applies the image to every applicable target it finds. Always give targets in scripts. `ExcludeTargets` does the opposite (and is ignored if `Targets` has members).
- `ForceUpdate`: bypass update policies such as "do not downgrade." Use with care.
- `TransferProtocol`: the values in the schema are `CIFS`, `FTP`, `SFTP`, `HTTP`, `HTTPS`, `NFS`, `SCP`, `TFTP` and `OEM`. A service lists what it supports in the action's `TransferProtocol@Redfish.AllowableValues`. Prefer HTTPS. A user name and password sent in a request must only travel over HTTPS (spec 13.2).
- `@Redfish.OperationApplyTime`: when to apply. The `UpdateService` values are `Immediate`, `OnReset`, `AtMaintenanceWindowStart`, `InMaintenanceWindowOnReset`, `OnStartUpdateRequest` and `OnTargetReset`. With `OnStartUpdateRequest`, the update is **registered** now and starts only when you call `StartUpdate`.

That last value is useful in a cluster. You can stage the same update on a whole rack, check that all requests were accepted, and only then call `StartUpdate` on each. In my lab the staged task stays `Pending` however long you wait until `StartUpdate` is called.

## 4. The task and its messages

Both methods return `202` and a task monitor (chapter 7.5). The Task's `Messages` tell the story, using the **Update message registry**:

| Stage message | Meaning |
|---|---|
| `TargetDetermined`, `AllTargetsDetermined`, `NoTargetsDetermined` | which devices will be updated |
| `TransferringToComponent` | the image is moving to the component |
| `VerifyingAtComponent` | the image is being checked (signature, hash, compatibility) |
| `InstallingOnComponent`, `ApplyingOnComponent` | being written |
| `StagingOnComponent` | being staged for later |
| `AwaitToUpdate`, `AwaitToActivate` | waiting for an action (a reset) |
| `ActivatingOnComponent` | being activated |
| `UpdateSuccessful` | done |

and the endings that are not success:

| Message | Severity | Meaning |
|---|---|---|
| `TransferFailed`, `VerificationFailed`, `ApplyFailed`, `ActivateFailed`, `StageFailed`, `CleanupFailed` | Critical | that stage failed |
| `UpdateSkippedSameVersion` | OK | the same version is already installed |
| `UpdateSkippedVersionTooLow` | OK | the image is older than allowed |
| `UpdateSkipped` | OK | skipped for another reason |
| `UpdateNotApplicable` | Warning | this image does not fit that device |
| `AutomaticRecoveryInitiated`, `AutomaticRecoveryFailed`, `AutomaticRecoverySuccessful` | | the device tried to roll back |

Your tool must read these. `200` at the end of a task does **not** mean a new version is running. A skipped update also ends in `200`. In my lab a skipped downgrade finished with HTTP 200 and an unchanged version. Always read the final message and re-read the inventory.

Here is the real output of my tool following an update on the mock (the dry run first, then the real run with `--yes`):

```text
PLAN  component HostBIOS_0 (System BIOS) is at version 1.20
      POST /redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate
      body {"ImageURI": "http://.../bios128.fwpkg", "TransferProtocol": "HTTP", "Targets": [".../FirmwareInventory/HostBIOS_0"]}
DRY RUN: nothing sent. Drain the node, then add --yes.
...
accepted, following /redfish/v1/TaskService/TaskMonitors/1
    [0%] Image 'bios128.fwpkg' is being transferred to 'BIOS'.
    [30%] Image 'bios128.fwpkg' is being verified at 'BIOS'.
    [60%] Image 'bios128.fwpkg' is being installed on 'HostBIOS_0'.
    [90%] Awaiting for an action to proceed with activating image 'bios128.fwpkg' on 'HostBIOS_0'.
task finished: HTTP 200 Update.1.0.AwaitToActivate
activating: POST /redfish/v1/Systems/System_0/Actions/ComputerSystem.Reset ResetType=GracefulRestart
inventory now says HostBIOS_0 = 1.28
```

The tool is a **dry run unless you pass `--yes`**, because updating firmware by mistake is expensive.

## 5. Staged is not active: activation

Most firmware is written to a spare area and used only after a reset, so the old firmware can keep running until then. The task ends with `AwaitToActivate` and the inventory keeps showing the **old** version. Which reset is needed depends on the component.

| Component (from the notes and the BCM manual) | What activates it |
|---|---|
| BMC firmware | a BMC restart: the Redfish `Manager.Reset`, or `ipmitool mc reset cold` (the notes' firmware steps use it) |
| BIOS and the GPU tray (notes) | a cold reset of the system |
| PCIe switches, retimers, ERoT, CPLDs (notes) | an **AC power cycle** |
| DGX H100 GPU firmware (BCM manual) | an **AC power cycle**: the manual says a regular DC power cycle from `cmsh` "is not enough to initialize some of the components" |

The BCM manual explains the terms: a **DC power cycle** is a board-level reset, an **AC power cycle** means all AC inputs to the system are cut, which can be done by powering off the system's PDU outlets or pulling the mains cables. In Redfish the `ResetType` values closest to these are `PowerCycle` (like removing power and restoring it) and `FullPowerCycle` (like removing utility power lines), see chapter 7.5. Whether the BMC's `FullPowerCycle` really removes AC power on a given DGX is something I could not check.

My mock models the idea: BMC firmware needs a `Manager.Reset`, BIOS needs a host restart, and the GPU-tray package needs a `FullPowerCycle`. The lab proves that:

```text
PASS  BMC firmware is NOT activated by a host reset
PASS  a Manager.Reset (BMC restart) activates it
PASS  one GPU-tray package stages all 30 GPU-tray entries
PASS  a normal host restart does NOT activate the GPU tray firmware
PASS  a board-level power cycle (PowerCycle) still does not activate it
PASS  a FullPowerCycle (AC power removed) activates all 30 entries
PASS  tool: a normal restart leaves the GPU firmware NOT active and the tool says so (exit 7)
```

The last line is the point. A tool that stops after "update finished" would leave nodes half-updated and report success. The tool re-reads the inventory afterwards and says `NOT ACTIVE` with exit code 7.

Also note one package can change many inventory items. My mock's GPU-tray package updates 30 entries at once, like the BCM manual's single `nvfw_dgx-hgx-h100x8_...fwpkg` file. With `Targets` you can limit it to one member.

## 6. How BCM does it

BCM wraps all this in its `firmware` commands (BCM 11 Administrator Manual, section 14.5.2). The steps for a DGX H100:

1. Get the `.fwpkg` files from NVIDIA's DGX support portal. Put them on the head node in `/cm/local/apps/cmd/etc/htdocs/bios/firmware/` in the subdirectory for the platform (`h100`, `gb200`, `gb200sw` and so on). Examples in the manual are about 100 to 135 MB each, such as `nvfw_DGX-H100_0003_230817.1.1_custom_prod-signed.fwpkg` for the motherboard tray and `nvfw_DGX-HGX-H100x8_0002_230705.1.1_prod-signed.fwpkg` for the GPU tray.
2. Configure the BMC network and BMC settings (user name, user id, password) and set **`firmwaremanagemode`** to the platform: the choices include `auto`, `h100`, `b200`, `b300`, `gb200`, `gb200sw`, `gb300`, `gb300sw`, `iLO` and `none`.
3. `firmware info` lists the packages on the head node (state `available`). `firmware status -n node001` shows each component's version, state (`current`, `pending`, `completed`) and a Result text.
4. `firmware flash <package>.fwpkg` on a device starts the update. The manual says progress shows in `firmware status` as a percentage, and the GPU rows show a transition such as `96.00.70.00.01 -> 96.00.74.00.01`. (That arrow display is BCM's view. Redfish itself just gives the old version until activation.)
5. When the flash is done the GPU rows say **`success: AC power cycle to activate`** with state `pending`. After the AC power cycle they say **`success: activated`** with state `completed` and the new version.

Details from the manual:

- Only the components covered by the chosen package are updated. "The non-GPU-related firmware components are not updated" by the GPU-tray package.
- For GB200 and GB300 racks, compute trays are updated with two packages (DGX-side and HGX-side), NVLink switch trays with three. The NVLink **switch tray** is updated through the **NVOS REST API, not Redfish**, so its credentials go in `accesssettings`, not `bmcsettings`.
- BCM uses a module called `cm-nvfwupd`. The manual says release 11.34.0 brings module version 2.1.2 with support for the GB200 NVL72 rack and Rubin-generation platforms.
- The manual points to NVIDIA's own update guides for each platform, which are the authority.

So BCM adds package management, many-node execution and status tracking on top of the same flow. Part 8 covers BCM in more depth.

## 7. NVIDIA's own tool, `nvfwupd`

The user's notes describe `nvfwupd`, a command-line tool from the NVIDIA Enterprise Support Portal that updates DGX H100 and H200 out-of-band, and the Redfish API as the other documented way (the same steps and known issues apply). Commands the notes show:

```bash
nvfwupd --target ip=<bmc-ip> user=<user> password=<password> show_version -p <package>.fwpkg
nvfwupd -t ip=<bmc-ip> user=<user> password=<password> update_fw -p <package>.fwpkg -y -s update_bmc.json
```

Points from the notes: `show_version -p` compares installed versions with a package; `update_fw -s <file>.json` limits the update to listed targets; stop GPU activity first because `nvidia-smi` can block a VBIOS update; do not add load such as jobs, diagnostics or monitoring during the update; downgrades follow a `ForceUpdate` procedure. **I have not run `nvfwupd` and cannot confirm these details.** The notes also explicitly say that an earlier draft of their text described a container image and an `update_fw all --preview` command that are not in NVIDIA's documentation, so I do not use them.

## 8. A safe fleet procedure

1. **Decide the baseline** from the vendor's validated bundle for your platform and write it to a file in version control.
2. **Read the vendor's update guide** for this exact platform and release. Check prerequisites, known issues, the order of components, and which activation each needs.
3. **Take a snapshot:** firmware inventory, health and (if you can) the vendor's support bundle. This is your before picture.
4. **Drain** the node in the scheduler (chapter 6.14) and wait until jobs end. Stop monitoring agents and GPU tools if the guide says so.
5. **Test on one node** first, then a small group, then waves. Do not update the whole cluster at once.
6. **Stage and verify:** send the update; follow the task; stop on the first failed stage.
7. **Activate** with the right reset for each component, in the order the vendor gives (BMC first is common, but follow the guide).
8. **Verify:** re-read the inventory and compare with the baseline. Run the health checks (chapters 7.8, 7.9 and Part 10) before returning the node.
9. **Return the node** to the scheduler only after it passes.
10. **Record** who, what, when, which versions before and after, and the task result.
11. **Plan the rollback** before you start: which package, which `ForceUpdate`, and what to do if the BMC will not respond (the notes describe recovery steps for a bricked BMC; I carry those into chapter 7.14).

Why not do firmware updates over SSH from the host OS? The notes argue (volume 5) that an SSH session can drop in the middle of a write. A BMC-driven update does not depend on the host OS staying healthy. This is a reasonable argument, but it is not a guarantee: the vendor's guide, not a general rule, decides how each component is updated, and some components do need the host side to be quiet during the transfer.

## 9. The lab

```bash
cd code/part07
python3 firmware_lab.py
```

It runs 46 checks. Grouped:

1. **Inventory and drift** (34 components, matching baseline, drift/missing/extra).
2. **The happy path:** 202, `Updating` while running, stage messages in order, `AwaitToActivate`, old version still shown, new version after the right reset.
3. **Different activation:** BMC reset, host reset, board power cycle, full power cycle.
4. **Failure and skip cases:** corrupted image, not a package, unreachable image, same version, downgrade, minimum-version rule, wrong target, missing `ImageURI`, bad transfer protocol, forbidden for a read-only user.
5. **Cancel** a running update and **staging** with `OnStartUpdateRequest` and `StartUpdate`.
6. **Multipart push:** success, missing part, too large, wrong content type.
7. **The tool:** dry run, skipped, failure exit code, timeout reported as unknown, normal restart not active (exit 7), full power cycle active.
8. The Task with its messages and the `Updating` inventory item **validate against the official DMTF schemas**.

One thing I fixed along the way: my first lab run died because the update ran longer than the simulated session timeout, and the client got a 401 in the middle. I added automatic **session renewal** to my Redfish client (on a 401 while holding a token it logs in again once and repeats the request). Real BMCs time sessions out too, and a long update is exactly when it happens.

## 10. Exercises

1. Run `firmware_lab.py` and `rf_firmware.py inventory` on the mock. Which components need which activation?
2. Write a baseline file for the mock after the GPU-tray update and run the `drift` command. Change one version and see the exit code.
3. Add a check to the lab: an update whose task is cancelled halfway must not leave a component in `Updating`.
4. Explain the difference between SimpleUpdate and multipart push to a colleague, with one advantage of each.
5. Design the wave plan to update the BMC firmware on 128 nodes: wave sizes, what you check between waves, the stop rule.
6. Why does the tool treat a timeout as "unknown" and not "failed"? What would you do next in real life?
7. Read the BCM manual section on `firmware status` and map each of its columns to a Redfish property.

## 11. Interview angles

- "How do you update firmware on 500 DGX nodes?" Baseline from the vendor, drain, small waves, BMC-driven updates with `Targets`, verify the inventory and health, then return nodes. Mention activation and rollback.
- "The update task finished with 200. Are you done?" No: read the final message (skipped? waiting for activation?) and re-read the inventory.
- "What is drift and why does it matter for training?" Nodes on different firmware behave differently, and collectives run at the speed of the slowest GPU.
- "Why `Targets`?" Without them the service may apply the image to every applicable device it finds.
- "How do you stage an update across a rack and start it together?" `@Redfish.OperationApplyTime: OnStartUpdateRequest`, then `StartUpdate`.
- "Why can't you just reboot to activate?" Some parts need a DC cycle, some an AC cycle. The vendor lists which.

## 12. Checkpoint questions (20)

1. Name five groups of firmware in a GPU server.
2. What is `FirmwareInventory` and what is in each member?
3. What does `Updateable` mean?
4. What is firmware drift and how do you detect it?
5. What is a baseline and where should it come from?
6. Compare SimpleUpdate and multipart push.
7. What does `Targets` do and why use it?
8. What does `ForceUpdate` bypass?
9. What does `@Redfish.OperationApplyTime: OnStartUpdateRequest` do?
10. What status do both methods return, and what do you do next?
11. Name four stage messages and three failure messages.
12. What does `UpdateSkippedSameVersion` mean for the final HTTP status?
13. What does `AwaitToActivate` mean?
14. Why can the inventory still show the old version after a successful update?
15. What activates BMC firmware?
16. What is the difference between a DC and an AC power cycle?
17. What does BCM's `firmwaremanagemode` set?
18. What does `success: AC power cycle to activate` mean in BCM?
19. Why is the NVLink switch tray updated differently?
20. Why does the lab tool refuse to send anything without `--yes`?

## 13. Sources and review notes

- **Redfish Specification DSP0266 v1.21.0:** update service, SimpleUpdate and multipart push (12.6), asynchronous tasks (12.2), operation apply time (7.12), sensitive data (13.2). I read these clauses.
- **Redfish Resource and Schema Guide DSP2046 and the official JSON Schemas and registries:** `UpdateService` v1.17 (actions, `ApplyTime`, `TransferProtocolType`, `UpdateParameters`), `SoftwareInventory` v1.15 (`VersionScheme`, properties) and the **Update message registry** 1.5.0 (all stage and failure messages above).
- **BCM 11 Administrator Manual, section 14.5 (BIOS and firmware management):** the DGX H100 and GB200/GB300 firmware workflow, `firmwaremanagemode` values, `firmware info/status/flash`, the 30 GPU-tray components with IDs and versions, `AC power cycle` activation, NVOS REST for the NVLink switch tray, module `cm-nvfwupd`. I read the H100 and GB200 sections.
- **NVIDIA-DevOps notes:** volume 10 chapter 1 sections 4.1 to 4.5 (seven firmware groups, the throttling story, `nvfwupd`, per-component activation); volume 5 chapter 3 (the argument for BMC-driven updates). The numbers in the notes' story are illustrative. Volume 10 chapter 10 (coordinated cluster-wide change management) is routed to chapter 17.10 and not used here.
- **Run here:** `firmware_lab.py` (46 checks), `rf_firmware.py` (inventory, drift, update).
- **Not verified:** any real firmware package, `nvfwupd`, NVIDIA's activation rules and order, how `FullPowerCycle` behaves on real DGX BMCs, and whether DGX BMCs accept `SimpleUpdate` or only their own tools.
