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
| Status | Drafted (`firmware_lab.py`: 46 checks pass against mock; **untested** on live BMC) |

## Why this matters for AI infrastructure

A 512-GPU training job slows down over a long run. Nothing in the code changed, and no alarm fires. Days later someone notices that four replacement nodes, fitted after board swaps, run an older GPU firmware than the rest of the cluster. That firmware throttled under sustained load and cut the job's throughput by 14 percent. Treat those numbers as an illustration, not a measurement.

A GPU cluster is many parts that must work together. Those parts include the BIOS (the basic input and output system, the first code that runs when the server powers on), the BMC (the baseboard management controller, a small computer on the board that handles remote power and monitoring), the GPU firmware, the NVSwitch firmware, the NIC firmware, the PCIe switches and more. The NVSwitch chips link the GPUs to one another, the NIC is the network card, and the PCIe switches route traffic between the cards inside the server. If one node runs older firmware than the rest, it may be slower, or it may fail in odd ways. A training step ends only when every GPU has finished its share of the work, so one slow node holds the whole job back. Everyone then waits for the slowest node.

That gives you two jobs. The first is to know exactly what is installed on every machine. This is called **inventory and drift**. The second is to change that firmware safely, which is called update. Redfish, the standard web interface that a BMC offers for remote management, handles both through one service. Firmware updating is the riskiest thing you do with a BMC, so this chapter takes it slowly.

## Prerequisites and outcomes

This chapter builds on chapters 7.2 to 7.5 and 7.7, so read those first. It then walks through the work in the order you meet it on a real node. It starts with listing every firmware version on a machine and comparing that list with a baseline. Next it covers the two ways to send an image, how to follow an update task and read its messages, and why an update can finish yet stay inactive until something activates it. It ends with how BCM's `firmware` commands do the same work, and how to write a safe update procedure for a whole fleet.

## 1. What is "firmware" in a GPU server?

Picture a support ticket that says one rack runs slower than the others. The first question is always the same: what is installed on each part of that box? Firmware is the answer to that question, so it helps to know what it is before you go looking for it.

Firmware is software that lives on a chip inside a part, such as a GPU or a network card. It sits in the chip's own memory, so it runs before the operating system starts and keeps running after the operating system stops. An AI cluster has to keep seven groups of firmware consistent. The table below shows what each group controls and why you should care.

| Group | Why it matters |
|---|---|
| System BIOS or UEFI | boot code, PCIe settings, memory training |
| BMC firmware | the management controller itself (sensor tables, fan curves) |
| GPU VBIOS and firmware | clocks, power and thermal behaviour of each GPU |
| NVSwitch firmware | NVLink routing and error recovery |
| NIC and DPU firmware (ConnectX, BlueField) | RDMA, congestion control |
| PCIe retimer and switch firmware | signal quality for fast links |
| NVMe drive firmware | wear handling and bug fixes |

Read the table as a map of where a node can drift. A mismatch in any one group can change how fast a GPU runs, how it talks to its neighbors, or whether it boots at all. A row that looks minor, such as the retimer, can be the one that quietly lowers the speed of a fast link.

The BCM manual's DGX H100 example makes the count concrete. After one GPU-tray update, it lists these components, each with its own version: `HGX_FW_BMC_0`, `HGX_FW_FPGA_0`, `HGX_FW_ERoT_BMC_0`, `HGX_FW_ERoT_FPGA_0`, four `HGX_FW_ERoT_NVSwitch_n`, `HGX_FW_ERoT_PCIeSwitch_0`, eight `HGX_FW_GPU_SXM_n`, four `HGX_FW_NVSwitch_n`, eight `HGX_FW_PCIeRetimer_n` and `HGX_FW_PCIeSwitch_0`. Add up the groups and you get **30** components in the GPU tray alone: 4 + 4 + 1 + 8 + 4 + 8 + 1 = 30. ERoT means external root of trust, which is a security chip. A root of trust is a small chip that checks other firmware before that firmware is allowed to run. The motherboard tray adds more, such as `CPLDMB_0` and `EROT_BIOS_0`.

Imagine typing those thirty version strings for every node in a rack, once a month. You would make mistakes, and after a while you would stop doing it. A script does not get tired, so plan to collect every version with a script, not by hand.

## 2. Inventory: UpdateService and FirmwareInventory

A new server arrives from the vendor, and your manager asks which firmware it carries before it goes into production. You could click through a web page, but a script can ask the same question for every node in the rack. To write that script, you first need to know the path the data takes through the Redfish tree.

Start at the service root. It links to `UpdateService`, and `UpdateService` links to `FirmwareInventory`. The service root is the front door of the tree, and each link you follow takes you one level deeper. `FirmwareInventory` is a collection, which is a list of resources of one kind. Each item in that list is a `SoftwareInventory` resource, one for each updatable component. The schema defines these properties on each `SoftwareInventory`:

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

Each property answers a different question. `Id` and `Name` tell you which component you are looking at. `Version` is the string you compare against your baseline. `Updateable` tells you whether this service can change the component at all, and `WriteProtected` tells you whether writes are blocked right now. Pay the most attention to `Version`, and to `Status`, which shows `Updating` while an update runs.

The `UpdateService` resource itself tells you what the service can do. It lists the actions `SimpleUpdate` and `StartUpdate`, the upload address `MultipartHttpPushUri`, the size limit `MaxImageSizeBytes`, and `ServiceEnabled`. Read it before you write any update code, because it tells you which methods this particular BMC actually supports.

The diagram below shows the whole flow, from the drift audit to the final check of the inventory. Read it from the top. The admin script first audits drift, then sends the image by one of two paths, then follows the task through its stages. Once the component is activated, the flow loops back to the inventory.

```mermaid
flowchart TD
    ADMIN["Automation / rf_firmware.py<br/>(--baseline / --yes)"]
    subgraph UPDATE["/redfish/v1/UpdateService"]
        INV["FirmwareInventory<br/>(34 SoftwareInventory items)"]
        PULL["Action: SimpleUpdate (Pull)<br/>BMC fetches ImageURI over HTTPS/HTTP"]
        PUSH["MultipartHttpPushUri (Push)<br/>UpdateParameters JSON + UpdateFile binary"]
    end
    subgraph TASK["/redfish/v1/TaskService/TaskMonitors/{id}"]
        STAGES["202 Accepted Task Stages:<br/>Transferring -> Verifying -> Installing -> AwaitToActivate"]
    end
    subgraph ACTIVATE["Component-Specific Activation Reset"]
        ACT_BMC["BMC Firmware:<br/>Manager.Reset / ipmitool mc reset cold"]
        ACT_BIOS["System BIOS:<br/>ComputerSystem.Reset (GracefulRestart / ForceRestart)"]
        ACT_HGX["30 HGX GPU-Tray Components & Retimers/ERoT:<br/>FullPowerCycle / AC Power Cycle (PDU)"]
    end
    ADMIN -->|"1. Audit drift"| INV
    ADMIN -->|"2a. Pull"| PULL
    ADMIN -->|"2b. Push"| PUSH
    PULL & PUSH --> STAGES
    STAGES -->|"3a"| ACT_BMC
    STAGES -->|"3b"| ACT_BIOS
    STAGES -->|"3c"| ACT_HGX
    ACT_BMC & ACT_BIOS & ACT_HGX -->|"4. Re-read Version"| INV
```

Notice that the last step returns to the inventory, so the inventory is both where you start and where you finish. You read it before the update to record the old state, and you read it again after activation to confirm the new one. The lab tool reads the whole inventory in one call:

```bash
python3 rf_firmware.py inventory http://<bmc> <user> <password>
```

The mock prints 34 lines: the four base components and the 30 GPU-tray components. Each line gives a component, its version and whether the service can update it. One of those lines looks like this: `HGX_FW_GPU_SXM_1  HGX_FW_GPU_SXM_1  96.00.70.00.01  updateable=True state=Enabled`. That single line is the kind of record a fleet script collects from every node.

### Drift: comparing with a baseline

On a Monday check across a rack, a few nodes report a different GPU version from the rest. Nobody remembers touching them. That gap between what a machine runs and what it should run is **drift**, and the rest of this section shows how to catch it automatically.

Drift is what you get when a machine no longer matches what you decided it should be. You record that decision in a baseline file, which lists each component with its expected version. The tool compares the live inventory against a file like this:

```json
{ "BIOS": "1.28", "BMC": "1.00.0", "HGX_FW_GPU_SXM_5": "96.00.74.00.01" }
```

```bash
python3 rf_firmware.py drift http://<bmc> <user> <password> --baseline baseline.json
```

Each line of the report gets one of four results. `ok` means the version matches. `DRIFT` means the version differs. `MISSING` means the baseline names something the machine does not have. `not in baseline` means the machine has something you did not list. The exit code is non-zero whenever something is wrong, so a pipeline can stop on it instead of quietly carrying on.

Here is how a drift run reads in practice. Suppose the baseline lists `HGX_FW_GPU_SXM_5` at `96.00.74.00.01`, and one node reports `96.00.70.00.01` for the same component. That line comes out as `DRIFT`, the report shows the gap, and the exit code is non-zero. A cron job or a pipeline step that checks the exit code can then send a warning or stop the rollout, instead of someone finding the gap weeks later in a training log.

The harder question is where the baseline comes from. It should be the validated bundle from your vendor for your platform, not "whatever is on the first node." A node that happens to be installed first is not a reference. It is just one more machine that could also be wrong. Take the versions from that bundle and keep the file in version control. Version control also gives you a history, so when the baseline changes you can see who changed it and why.

## 3. Two ways to send an image

You have a new firmware package and 100 BMCs to update. The package has to reach every one of them, and there are two ways to make that happen. In one, the BMC fetches the file itself from a web address you give it. In the other, your script sends the whole file inside the request. Both are defined in the Redfish spec, in clause 12.6.2. A service may offer either method or both.

The table compares them.

| | SimpleUpdate (pull) | Multipart HTTP push |
|---|---|---|
| Who moves the file | the **BMC downloads** it from a URL you give | **you upload** it in the request |
| Needs a file server | yes, reachable from the BMC | no |
| Request | `POST` the action `UpdateService.SimpleUpdate` | `POST` to `MultipartHttpPushUri` with `multipart/form-data` |
| Parameters | `ImageURI` (required), `TransferProtocol`, `Targets`, `ExcludeTargets`, `ForceUpdate`, user name and password for the file server | a JSON part named `UpdateParameters` (same fields) and a binary part named `UpdateFile` |
| Answer | `202` with a task monitor | `202` with a task monitor; `413` if the image is bigger than `MaxImageSizeBytes`; `411` if a length is required and missing |

A useful way to choose is to ask where the bytes will come from. If your management network already has a small, reliable file server that every BMC can reach, pull keeps your script light and lets the BMCs do the copying. If there is no such server, or if the BMCs cannot reach one, push is the fallback, even though your own machine then carries the whole load.

**Which to use.** Pull scales well. 100 BMCs can fetch the same file from one server in parallel, and your script only sends small requests. The cost is a file server on the management network that every BMC can reach. Push needs no file server, but your script moves the whole image for every machine. The BCM examples show packages of 100 to 135 MB. Multiply 100 machines by 135 MB and your script uploads 13.5 GB. The legacy `HttpPushUri` also exists, but its format is vendor specific, so it is harder to write one script for every vendor.

Several parameters decide what an update touches, so understand each one before you send a request. `Targets` holds the URIs of the inventory items to update. If you give none, the service applies the image to every applicable target it finds. Picture a script that leaves `Targets` out on a node with two GPU trays, and the image lands on parts you never meant to touch. Always give targets in scripts. `ExcludeTargets` works the other way, but it is ignored when `Targets` has members.

`ForceUpdate` tells the service to bypass update policies such as "do not downgrade." Use it with care, because the policy exists for a reason. `TransferProtocol` names how the BMC fetches the file. The schema lists `CIFS`, `FTP`, `SFTP`, `HTTP`, `HTTPS`, `NFS`, `SCP`, `TFTP` and `OEM`. A service lists what it supports in the action's `TransferProtocol@Redfish.AllowableValues`. Prefer HTTPS, because a user name and password sent in a request must only travel over HTTPS, as clause 13.2 says.

`@Redfish.OperationApplyTime` controls when the update applies. The `UpdateService` values are `Immediate`, `OnReset`, `AtMaintenanceWindowStart`, `InMaintenanceWindowOnReset`, `OnStartUpdateRequest` and `OnTargetReset`. With `OnStartUpdateRequest`, the update is **registered** now and starts only when you call `StartUpdate`.

That last value is useful in a cluster. You can stage the same update on a whole rack, check that every request was accepted, and only then call `StartUpdate` on each node. In the lab mock, a staged task stays `Pending` for as long as you wait, until `StartUpdate` is called. Always pass `Targets` from your scripts, and use `OnStartUpdateRequest` when you want to stage a whole rack before starting any of it.

## 4. The task and its messages

You send a `SimpleUpdate` request, the BMC answers `202`, and your script prints "accepted." Is the update done? Not yet. The `202` only means the BMC accepted the job. The job itself lives in a task, and the task's messages tell you how it went.

Both methods answer with `202` and a task monitor, which chapter 7.5 covers. The task's `Messages` tell you how the update went. They come from the **Update message registry**, a standard list of messages that the DMTF defines for all Redfish services. The stage messages below follow the image from the first transfer to the wait for activation.

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

Some messages end the story without success, and some are not failures at all. The table below lists those endings, including the skips and the warning. A skip is the BMC saying it looked at the image and chose not to flash it, which is different from a failure.

| Message | Severity | Meaning |
|---|---|---|
| `TransferFailed`, `VerificationFailed`, `ApplyFailed`, `ActivateFailed`, `StageFailed`, `CleanupFailed` | Critical | that stage failed |
| `UpdateSkippedSameVersion` | OK | the same version is already installed |
| `UpdateSkippedVersionTooLow` | OK | the image is older than allowed |
| `UpdateSkipped` | OK | skipped for another reason |
| `UpdateNotApplicable` | Warning | this image does not fit that device |
| `AutomaticRecoveryInitiated`, `AutomaticRecoveryFailed`, `AutomaticRecoverySuccessful` | | the device tried to roll back |

In a script, the pattern is simple to describe and easy to get wrong. Poll the task monitor until its state is final. Then read the last message and its severity, and only after that look at the inventory. A script that stops polling too early reads a message from the middle of the update and reports a result that is not final yet.

Your tool must read these messages. A `200` at the end of a task does **not** mean a new version is running, because a skipped update also ends in `200`. In the lab mock, a skipped downgrade finished with HTTP 200 and an unchanged version. So read the final message first, then re-read the inventory. That order keeps you from declaring victory on a task that did nothing.

Here is what the lab tool printed on the mock. It did a dry run first, then a real run with `--yes`:

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

Read that output as a story: the plan, the progress lines, then the activation and the new version. The tool is a **dry run unless you pass `--yes`**, because a firmware update you start by mistake is expensive. The first pass only shows what would happen, and the second pass does the work. Treat a `200` as the start of verification, not the end of the job.

## 5. Staged is not active: activation

A script reports success at night. In the morning the GPU still shows the old version, and nothing looks broken. The new firmware is sitting in a spare area, waiting for the right reset. This is the most common surprise in firmware work, so it helps to understand it before it happens to you.

A task can report success while the inventory still shows the old version. That is expected when the firmware is written to a spare area and used only after a reset. The old firmware keeps running until then. Your task ends in `AwaitToActivate`, and the inventory keeps showing the old version. Which reset you need depends on the component.

| Component | What activates it |
|---|---|
| BMC firmware | a BMC restart: the Redfish `Manager.Reset`, or `ipmitool mc reset cold` |
| BIOS and the GPU tray (notes) | a cold reset of the system |
| PCIe switches, retimers, ERoT, CPLDs (notes) | an **AC power cycle** |
| DGX H100 GPU firmware (BCM manual) | an **AC power cycle**: the manual says a regular DC power cycle from `cmsh` "is not enough to initialize some of the components" |

The BCM manual defines the two power-cycle terms. A **DC power cycle** is a board-level reset. An **AC power cycle** cuts every AC input to the system, which you can do by switching off the PDU outlets or by pulling the mains cables. The PDU is the power distribution unit that feeds the rack. The closest `ResetType` values are `PowerCycle` and `FullPowerCycle`. The first is closest to removing power and restoring it, and the second is closest to removing the utility power lines. Chapter 7.5 covers both. Confirm on your own hardware whether the BMC's `FullPowerCycle` really removes AC power on a given DGX before you rely on it.

The mock models this. BMC firmware needs a `Manager.Reset`, BIOS needs a host restart, and the GPU-tray package needs a `FullPowerCycle`. The lab checks these rules, and its output shows them passing:

```text
PASS  BMC firmware is NOT activated by a host reset
PASS  a Manager.Reset (BMC restart) activates it
PASS  one GPU-tray package stages all 30 GPU-tray entries
PASS  a normal host restart does NOT activate the GPU tray firmware
PASS  a board-level power cycle (PowerCycle) still does not activate it
PASS  a FullPowerCycle (AC power removed) activates all 30 entries
PASS  tool: a normal restart leaves the GPU firmware NOT active and the tool says so (exit 7)
```

Walk through a real night with this in mind. The script sends the update, the task reaches `AwaitToActivate`, and the script reports success and moves on. Nothing has changed on the GPU yet. The next morning, someone checks the inventory and finds the old version still in place. The fix is not to rerun the update. The fix is to schedule the correct power cycle in the maintenance window, then check the inventory again.

The last line matters most. A tool that stops at "update finished" would leave nodes half-updated while reporting success. Instead, the lab tool re-reads the inventory afterwards, says `NOT ACTIVE`, and exits with code 7. A script that checks the exit code can then stop before it moves on to the next node.

One package can change many inventory items at once. The mock's GPU-tray package updates 30 entries in a single step, just as the BCM manual's single `nvfw_dgx-hgx-h100x8_...fwpkg` file does. If you want only one member changed, `Targets` lets you limit the update to it. Match each component to its reset before you schedule the window, because a wrong reset leaves the new version inactive. A window that ends without the right reset looks finished on the task page and still runs the old code.

## 6. How BCM does it

Many clusters do not send raw Redfish calls by hand. They run NVIDIA Base Command Manager (BCM), the software that provisions and manages the nodes, and BCM wraps this whole flow in its `firmware` commands. Section 14.5.2 of the BCM 11 Administrator Manual gives the steps for a DGX H100:

1. Put the `.fwpkg` files from NVIDIA's DGX support portal on the head node, in `/cm/local/apps/cmd/etc/htdocs/bios/firmware/`, in the subdirectory for your platform (`h100`, `gb200`, `gb200sw` and so on). The head node is the BCM server that holds the packages for the rest of the cluster. The manual's examples run about 100 to 135 MB each, such as `nvfw_DGX-H100_0003_230817.1.1_custom_prod-signed.fwpkg` for the motherboard tray and `nvfw_DGX-HGX-H100x8_0002_230705.1.1_prod-signed.fwpkg` for the GPU tray.
2. Configure the BMC network and the BMC settings (user name, user id and password). Then set **`firmwaremanagemode`** to your platform. The choices include `auto`, `h100`, `b200`, `b300`, `gb200`, `gb200sw`, `gb300`, `gb300sw`, `iLO` and `none`. This setting tells BCM which platform's update rules to follow.
3. `firmware info` lists the packages on the head node, with state `available`. `firmware status -n node001` shows each component's version, its state (`current`, `pending`, `completed`) and a Result text. Run these two commands before you flash anything, so you know what you are starting from.
4. `firmware flash <package>.fwpkg` on a device starts the update. The manual says progress shows in `firmware status` as a percentage. The GPU rows show a transition such as `96.00.70.00.01 -> 96.00.74.00.01`. That arrow display is BCM's view. Redfish itself just gives the old version until activation.
5. When the flash is done, the GPU rows say **`success: AC power cycle to activate`** with state `pending`. After the AC power cycle, they say **`success: activated`** with state `completed` and the new version.

The manual adds details that matter in practice. Only the components in the chosen package get updated. The manual says that "the non-GPU-related firmware components are not updated" by the GPU-tray package. On GB200 and GB300 racks, a compute tray needs two packages, a DGX-side one and an HGX-side one, and an NVLink switch tray needs three. The NVLink **switch tray** is not updated through Redfish. It goes through the **NVOS REST API**, so its credentials belong in `accesssettings`, not `bmcsettings`.

BCM uses a module called `cm-nvfwupd`. The manual says release 11.34.0 brings module version 2.1.2, with support for the GB200 NVL72 rack and Rubin-generation platforms. For each platform, the manual points you to NVIDIA's own update guide, and that guide is the authority.

So BCM adds package management, execution across many nodes and status tracking on top of the same flow. Part 8 goes deeper into BCM. If you run BCM, let it handle the packages and the status tracking, and keep the vendor guide open beside it.

## 7. NVIDIA's own tool, `nvfwupd`

Imagine a DGX H100 that the support team asks you to update, and the vendor's own command-line tool is the path they want. `nvfwupd` is that tool. It comes from the NVIDIA Enterprise Support Portal, and it updates DGX H100 and H200 systems out-of-band, which means it talks to the BMC over the management network instead of going through the host operating system. The Redfish API is the other documented route, and the same steps and known issues apply to it. Typical commands look like this:

```bash
nvfwupd --target ip=<bmc-ip> user=<user> password=<password> show_version -p <package>.fwpkg
nvfwupd -t ip=<bmc-ip> user=<user> password=<password> update_fw -p <package>.fwpkg -y -s update_bmc.json
```

Five points matter, and you should read each one before you run anything. First, `show_version -p` compares the installed versions with a package, so you see the gap before you change anything. Second, `update_fw -s <file>.json` limits the update to the targets in that file. Third, stop GPU activity first, because `nvidia-smi` can block a VBIOS update. Fourth, add no extra load, such as jobs, diagnostics or monitoring, while the update runs. Last, downgrades follow a `ForceUpdate` procedure, so do not attempt one from memory.

Before you run anything from this list, check the details for `nvfwupd` against NVIDIA's documentation. The tool's flags and behavior can change from one release to the next, and a command copied from an old forum post may no longer match the version your support team hands you. A container image and an `update_fw all --preview` command sometimes appear in informal descriptions. Neither appears in NVIDIA's documentation, so this chapter does not use them. Treat the commands above as a starting point to check, not as a procedure you can copy.

## 8. A safe fleet procedure

Suppose you must bring a rack of nodes to the same firmware in one maintenance window. A maintenance window is a planned time when the nodes can stop taking jobs. The steps below keep a bad update from reaching the whole cluster. Work through them in order:

1. **Decide the baseline.** Take it from the vendor's validated bundle for your platform, and write it to a file in version control.
2. **Read the vendor's update guide** for this exact platform and release. Check the prerequisites, the known issues, the order of components, and which activation each component needs.
3. **Take a snapshot** of the firmware inventory, the health data and, if you can, the vendor's support bundle. This is your before picture.
4. **Drain** the node in the scheduler (chapter 6.14) and wait until its jobs end. If the guide says so, stop the monitoring agents and GPU tools too.
5. **Test on one node** first, then move to a small group, then to waves. Never update the whole cluster at once.
6. **Stage and verify.** Send the update, follow the task, and stop at the first failed stage.
7. **Activate** each component with its own reset, in the order the vendor gives. BMC first is common, but the guide decides.
8. **Verify** by re-reading the inventory and comparing it with the baseline. Run the health checks from chapters 7.8, 7.9 and Part 10 before the node goes back.
9. **Return the node** to the scheduler only after it passes.
10. **Record** who ran the update, what changed, when, the versions before and after, and the task result.
11. **Plan the rollback** before you start. Decide which package you would use, whether `ForceUpdate` applies, and what you will do if the BMC stops responding. Chapter 7.14 covers recovery steps for a bricked BMC.

Think of the rollout as a sequence of waves. The first wave is one canary node, which is a machine you update first to see what the update does on your hardware. If the canary behaves, the next wave is a small group. Each wave has its own stop condition. A failed stage, a version that did not change, or a node that does not return to the scheduler all count as reasons to stop and look before you go on.

Notice how much of the procedure happens before and after the flash itself. The flash is often the shortest part of the work. The snapshot, the drain, the verification and the record are what let you explain a failure later, and they are what let you stop a bad rollout early.

Why not update over SSH from the host OS? SSH is the remote login session into the host operating system. One argument is that an SSH session can drop in the middle of a write, and a half-written image is a serious problem. A BMC-driven update does not depend on the host OS staying healthy. The argument is reasonable, but it is not a guarantee. The vendor's guide decides how each component is updated, and some components need the host side to stay quiet during the transfer.

Firmware windows that also touch the InfiniBand fabric and parallel storage need extra ordering and Subnet Manager care. Those steps belong with the fabric and storage chapters in Parts 12 and 13, not here.

## 9. The lab

Before you point any of these tools at a real BMC, you want to see them behave. The lab gives you a mock BMC on your laptop, and it sends the same kinds of requests a real one would receive. Start the lab from the chapter's code folder. The groups below show what the 46 checks cover, so you know what a failure means.

```bash
cd code/part07
python3 firmware_lab.py
```

The 46 checks pass against the mock. They have not been run against a live BMC, so treat a pass here as a rehearsal, not as proof for your hardware. The lab is most useful as a place to break things safely. Try a bad image, a missing target or a wrong reset type, and watch how the tool reports each one before you ever point it at a real node.

1. **Inventory and drift** read the 34 components and compare them with the baseline. The checks cover drift, missing items and extra items.
2. **The happy path** runs an update from start to finish. It checks for a `202`, an `Updating` state while the update runs, and the stage messages in order. It also checks `AwaitToActivate`, the old version and the new version.
3. **Different activation** checks each reset type you will meet: a BMC reset, a host reset, a board power cycle and a full power cycle.
4. **Failure and skip cases** cover a corrupted image, a file that is not a package, an unreachable image and a wrong target. They also cover the same version, a downgrade, the minimum-version rule, a missing `ImageURI` and a bad transfer protocol. A read-only user's request must be refused.
5. **Cancel and staging** stop a running update, and stage one with `OnStartUpdateRequest` and `StartUpdate`.
6. **Multipart push** covers success, a missing part, a file that is too large, and a wrong content type.
7. **The tool** checks a dry run, a skipped update, the failure exit code and a timeout reported as unknown. It also checks the inactive and active cases (exit 7 for the inactive one).
8. Last, the Task with its messages and the `Updating` inventory item validate against the official DMTF schemas. DMTF is the Distributed Management Task Force, the standards group that publishes Redfish.

One bug showed up on the first run, and it matters because real BMCs behave the same way. The update took longer than the simulated session timeout, so the client got a 401 halfway through. A 401 means the session token is no longer accepted. The lab's Redfish client now has automatic **session renewal**. When it gets a 401 while holding a token, it logs in again once and repeats the request. Real BMCs time sessions out too, and a long update is exactly when that happens.

## Exercises

Work through these in order. Each one uses the lab from section 9, and each one asks for a single decision.

1. **Run the 46-check lifecycle suite.** Run `python3 code/part07/firmware_lab.py`, which should report all 46 checks passing. Your team wants proof that the lab works before anyone trusts it. Next, run `python3 code/part07/rf_firmware.py inventory` against the mock. Which components need `Manager.Reset`? Which need a host `ComputerSystem.Reset`? Which need `FullPowerCycle` (AC power cycle)?
2. **Audit fleet drift with `rf_firmware.py drift`.** Save a JSON baseline that matches the mock's post-update GPU tray versions (`96.00.74.00.01`). Then change one GPU's expected version on purpose. Run `rf_firmware.py drift --baseline <file>`. Check that the tool flags `DRIFT` and exits non-zero.
3. **Check that cancelling an update cleans up.** Read how `code/part07/firmware_lab.py` cancels an update in progress, with a `DELETE` on the Task Monitor URI. That tells you what the test really checks. Then confirm that the target `SoftwareInventory` item's `Status.State` goes from `"Updating"` back to `"Enabled"`.
4. **Compare pull and push.** Write out the exact `curl` commands for updating `HostBIOS_0` in two ways. One uses `SimpleUpdate` with `ImageURI` and `Targets`. The other posts to `MultipartHttpPushUri` with `-F UpdateParameters=... -F UpdateFile=@...`. Then say which one you would choose for a `100–135 MB` `.fwpkg` bundle across 128 nodes, and why.
5. **Design a canary rollout.** Apply the 11-step procedure in Section 8 to a 128-node cluster. The cluster rolls out in this order: `1` canary node → `1` rack of `8` nodes → `1` SU of `32` nodes → remaining SUs. An SU is a scalable unit, a block of nodes that is planned together. Write down the exact stop condition between each wave.
6. **Map BCM `firmware status` onto Redfish.** Compare the columns of BCM's `cmsh` `firmware status -n node001` output with the Redfish fields that hold the same information. The BCM columns are `component`, `version`, `state: current/pending/completed` and `Result: success: AC power cycle to activate`. Your answer should cover each column. The Redfish side is `SoftwareInventory` (`Id`, `Version`, `Status.State`) and `Task.Messages` (`Update.1.0.AwaitToActivate`, `Update.1.0.UpdateSuccessful`).

## 10. Interview angles

These are the questions that come up most. Each answer below starts with the short version, then gives the reason.

- "How do you update firmware on 500 DGX nodes?" Start with a baseline from the vendor. Drain the nodes, then roll out in small waves with BMC-driven updates and `Targets`. Verify the inventory and health before you return the nodes, and mention activation and rollback too.
- "The update task finished with 200. Are you done?" Not yet. Read the final message to see whether the update was skipped or is waiting for activation, then re-read the inventory.
- "What is drift and why does it matter for training?" Drift means a machine no longer matches the version you decided on. Nodes on different firmware behave differently, and collectives run at the speed of the slowest GPU.
- "Why `Targets`?" Without them, the service may apply the image to every applicable device it finds.
- "How do you stage an update across a rack and start it together?" Set `@Redfish.OperationApplyTime: OnStartUpdateRequest`, then call `StartUpdate`.
- "Why can't you just reboot to activate?" Some parts need a DC cycle and some need an AC cycle. The vendor lists which one each part needs. A normal reboot restarts the host, but it may leave a GPU tray or a BMC on the old firmware, so the reset has to match the component.
- "What do you do with a node that fails halfway through?" Stop the rollout, keep the node drained, and read the failed stage message. Do not start another update on the same node until you know which component is in an unknown state and what the rollback plan says.

## Checkpoint questions (20)

<details>
<summary>1. Name the seven firmware groups in an AI GPU server that must be kept on a validated baseline.</summary>

1. **System BIOS / UEFI**
2. **Motherboard BMC firmware**, along with the GPU-tray satellite HMC and FPGA firmware
3. **GPU VBIOS / InfoROM**
4. **NVSwitch firmware**
5. **Network adapter and DPU firmware**, such as `ConnectX-7` and `BlueField-3`
6. **PCIe switch and retimer firmware**, plus CPLDs and `ERoT` roots of trust
7. **NVMe SSD firmware**
</details>

<details>
<summary>2. What is `/redfish/v1/UpdateService/FirmwareInventory`, and what schema type is each member?</summary>

It is a collection. Each member is a **`SoftwareInventory`** resource, one for each updatable or readable firmware image on the server. The DGX H100 mock has `34` components: `4` host components and `30` HGX GPU-tray components. Each member exposes `Id`, `Name`, `Version`, `Updateable`, `LowestSupportedVersion`, `RelatedItem` and `Status`.
</details>

<details>
<summary>3. What do `Updateable`, `WriteProtected`, and `LowestSupportedVersion` mean on a `SoftwareInventory` resource?</summary>

- **`Updateable`** is a yes or no flag. It tells you whether `UpdateService` can flash this component.
- **`WriteProtected`** is also yes or no. It says whether hardware or a jumper is blocking writes right now.
- **`LowestSupportedVersion`** is the oldest version this component may be downgraded to. It guards against anti-rollback fuse violations.
</details>

<details>
<summary>4. What is firmware drift, why can four drifted nodes degrade a 512-GPU training job by 14%, and how does `rf_firmware.py drift` detect it?</summary>

Drift happens when some nodes, often after an RMA board replacement, run a different firmware version than the rest of the cluster. Say an older GPU VBIOS throttles clocks under heavy FP8 GEMM load on 4 nodes. All 512 GPUs then stall at every synchronous `AllReduce` barrier, because they wait for those 4 nodes. `rf_firmware.py drift` compares each node's live `FirmwareInventory` with a version-controlled JSON baseline. It flags `DRIFT` or `MISSING`, and it exits non-zero.
</details>

<details>
<summary>5. Where should your cluster's firmware baseline JSON come from?</summary>

It should come from the hardware vendor's published, co-validated firmware qualification matrix or bundle for that exact server model and software release. Do not copy whatever versions you happen to find on the first server delivered.
</details>

<details>
<summary>6. Compare `UpdateService.SimpleUpdate` (pull) and `MultipartHttpPushUri` (push) across network flow, parameters, and fleet scalability.</summary>

- **`SimpleUpdate` (pull):** You send a small JSON request (`ImageURI`, `TransferProtocol`, `Targets`) to `/redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate`. Each BMC then downloads the `.fwpkg` image asynchronously from your local HTTP or HTTPS server. It scales cleanly to hundreds of nodes, and the orchestrator is not a bottleneck.
- **`MultipartHttpPushUri` (push):** Your client uploads the whole binary, `100–135 MB` per node, as `multipart/form-data` with an `UpdateParameters` JSON part and an `UpdateFile` binary part. You need no file server on the OOB network, but all that bandwidth goes through the orchestrator.
</details>

<details>
<summary>7. What does the `Targets` array parameter do in an update request, and why should scripts always populate it explicitly?</summary>

`Targets` lists the exact `@odata.id` URIs in `FirmwareInventory` that the package should be applied to. If you leave it out, the BMC applies the image to every applicable device it finds. That can flash components you never meant to touch, so scripts should always fill it in.
</details>

<details>
<summary>8. What does `"ForceUpdate": true` do in `SimpleUpdate` or `UpdateParameters`?</summary>

It tells the BMC to bypass the normal version-comparison guards. The BMC will re-flash an identical version, instead of skipping it with `UpdateSkippedSameVersion`. It can also perform a supported downgrade to an older version, but that downgrade still cannot go below `LowestSupportedVersion`.
</details>

<details>
<summary>9. How do `"@Redfish.OperationApplyTime": "OnStartUpdateRequest"` and the `#UpdateService.StartUpdate` action work together across a rack of servers?</summary>

Setting `OperationApplyTime` to `"OnStartUpdateRequest"` makes each BMC stage and register the update. The task stays in `TaskState: "Pending"`, and nothing is flashed yet. Once every node in the rack has staged the package, the orchestrator calls `POST /redfish/v1/UpdateService/Actions/UpdateService.StartUpdate` across the rack, so execution starts on all of them together.
</details>

<details>
<summary>10. What HTTP status code do `SimpleUpdate` and `MultipartHttpPushUri` return when accepted, and what happens if a pushed image exceeds `MaxImageSizeBytes`?</summary>

Both return **`202 Accepted`** with a `Location` header that points to a Task Monitor URI. If a multipart push is larger than `MaxImageSizeBytes`, the BMC rejects it with **`413 Payload Too Large`**. It returns **`411 Length Required`** instead when `Content-Length` is missing.
</details>

<details>
<summary>11. Name four progress messages and three failure messages from the DMTF `Update` Message Registry (`Update.1.x`).</summary>

The progress messages include `TargetDetermined`, `TransferringToComponent`, `VerifyingAtComponent`, `InstallingOnComponent` or `ApplyingOnComponent`, `AwaitToActivate` and `UpdateSuccessful`. The failure messages are `TransferFailed`, `VerificationFailed` and `ApplyFailed`, plus `StageFailed` and `ActivateFailed`.
</details>

<details>
<summary>12. Why does a final HTTP `200 OK` from an update Task Monitor NOT prove that the new firmware version is installed and running?</summary>

A skipped update, such as `UpdateSkippedSameVersion` or `UpdateSkippedVersionTooLow`, still completes the task with `200 OK`, and the old version stays in place. A staged update also ends with `AwaitToActivate` and `200 OK`. In that case the new image is written to inactive flash, and it does not run until the required reset happens.
</details>

<details>
<summary>13. What does `Update.1.0.AwaitToActivate` mean in a completed Task's `Messages` array?</summary>

It means the image was transferred, verified and written to the component's staging flash bank. The new firmware now waits for the right reset, whether that is a BMC reset, a host reboot or an AC power cycle, before it becomes the running version.
</details>

<details>
<summary>14. Why does `FirmwareInventory` continue to report the OLD version string even after the update task finishes with `AwaitToActivate`?</summary>

In Redfish, `SoftwareInventory.Version` reports the **currently active, running firmware version** of the component. Until the activation reset happens and the component boots from the new flash bank, the old version is still the one running in silicon.
</details>

<details>
<summary>15. Which specific reset action activates newly flashed BMC firmware versus System BIOS firmware?</summary>

- **BMC firmware:** Reset the BMC with Redfish **`#Manager.Reset`** (`GracefulRestart` or `ForceRestart`), or run `ipmitool mc reset cold`. If you only reboot the host OS, BMC firmware stays inactive.
- **System BIOS:** Reset the host with **`#ComputerSystem.Reset`** (`GracefulRestart` or `ForceRestart`).
</details>

<details>
<summary>16. What is the physical difference between a DC power cycle and an AC power cycle, and why does the DGX H100 GPU tray require an AC power cycle after flashing (`bcm11-admin` §14.5.2)?</summary>

A **DC power cycle** turns off only the main host power rails. The `5V` and `12V` auxiliary standby rails stay on. An **AC power cycle**, which is `FullPowerCycle` or switching the rack PDU outlets off and on, removes all input power, so the standby rails discharge completely. The GPU tray needs that full discharge to reload its complex auxiliary parts, which are `30` components including the `ERoT` security roots of trust, CPLDs, FPGAs, NVSwitches and PCIe retimers.
</details>

<details>
<summary>17. In NVIDIA Base Command Manager (`cmsh`), where are `.fwpkg` files placed on the head node, and what are the four main `firmware` subcommands (§14.5.2)?</summary>

Packages go under **`/cm/local/apps/cmd/etc/htdocs/bios/firmware/<platform>/`**, and `firmwaremanagemode` must match the platform, such as `h100`, `b200`, `gb200`, `gb200sw` and so on. The four main commands are `firmware info`, which lists available packages, and `firmware status`, which shows each component's current, pending or completed version. The other two are `firmware flash <pkg>.fwpkg`, and `power` with an AC cycle to activate.
</details>

<details>
<summary>18. On a rack-scale NVIDIA GB200 or GB300 NVL72 system managed by BCM, how does updating an NVLink switch tray (`gb200sw`) differ from updating a compute tray?</summary>

A compute tray is updated through Redfish, using `bmcsettings` and two `.fwpkg` bundles, the DGX-side one and the HGX-side one. An NVLink switch tray takes three packages, and it is updated through the switch's **NVOS REST API**. Its credentials go in `accesssettings`, not in Redfish `bmcsettings`.
</details>

<details>
<summary>19. Why is `OnStartUpdateRequest` useful when you update a whole rack?</summary>

You can stage the same image on every node and check that each request was accepted. Only then do you call `StartUpdate` on each node. A staged task stays `Pending` until `StartUpdate` arrives, so a rejected request is found before any node starts flashing.
</details>

<details>
<summary>20. Why does the lab tool exit with code 7 after an update that finished with `AwaitToActivate`?</summary>

A task that ends with HTTP 200 does not mean the new version is running. The tool re-reads the inventory, sees the old version, reports `NOT ACTIVE` and exits with 7, so that a script cannot mistake a half-updated node for a finished one.
</details>

## Sources and review notes

- **Removed section (W4 rework 2026-11-12):** an earlier section 8.1 on coordinated storage, fabric and compute rollouts was deleted from this chapter. Its claims were not carried over and were never verified: UFM Subnet Manager default priority of 15 (OpenSM's own default is 0), `mstflint` unbundling from `MLNX_OFED 24.07`, and a `nvidia-fs 2.25.6` P2P bug. Anyone restoring them in Parts 12 or 13 must check the vendor release notes first.

- **Redfish Specification DSP0266 v1.21.0:** update service, SimpleUpdate and multipart push (12.6), asynchronous tasks (12.2), operation apply time (7.12), sensitive data (13.2). I read these clauses.
- **Redfish Resource and Schema Guide DSP2046 and the official JSON Schemas and registries:** `UpdateService` v1.17 (actions, `ApplyTime`, `TransferProtocolType`, `UpdateParameters`), `SoftwareInventory` v1.15 (`VersionScheme`, properties) and the **Update message registry** 1.5.0 (all stage and failure messages above).
- **BCM 11 Administrator Manual, section 14.5 (BIOS and firmware management):** the DGX H100 and GB200/GB300 firmware workflow, `firmwaremanagemode` values, `firmware info/status/flash`, the 30 GPU-tray components with IDs and versions, `AC power cycle` activation, NVOS REST for the NVLink switch tray, module `cm-nvfwupd`. I read the H100 and GB200 sections.
- **NVIDIA-DevOps notes:** volume 10 chapter 1 sections 4.1 to 4.5 (seven firmware groups, the throttling story, `nvfwupd`, per-component activation); volume 5 chapter 3 (the argument for BMC-driven updates). The numbers in the notes' story are illustrative. Volume 10 chapter 10 (coordinated cluster-wide change management) is routed to chapter 17.10 and not used here.
- **Run here:** `firmware_lab.py` (46 checks), `rf_firmware.py` (inventory, drift, update).
- **Not verified:** any real firmware package, `nvfwupd`, NVIDIA's activation rules and order, how `FullPowerCycle` behaves on real DGX BMCs, and whether DGX BMCs accept `SimpleUpdate` or only their own tools.
