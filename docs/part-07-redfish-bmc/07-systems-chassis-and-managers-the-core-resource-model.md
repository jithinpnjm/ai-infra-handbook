---
id: "c07-07"
title: "7.7 Systems, Chassis and Managers: the core resource model"
sidebar_label: "7.7 Systems, Chassis and Managers: the core resource model"
sidebar_position: 7
description: "The three core Redfish families explained for beginners: Systems (the computer), Chassis (the box) and Managers (the BMC), how they link to each other, what lives under each, how DPUs, blades and GPU baseboards fit, and tools that map and check a real service"
status: "drafted"
tier: "1b"
level: "I"
lab_venue: "GCP / GKE"
---

# 7.7 Systems, Chassis and Managers: the core resource model

| | |
|---|---|
| Level | Beginner to Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted (`rf_model.py` and `rf_inventory.py` run against mock and DMTF trees; **untested** on live BMC) |

## Why this matters for AI infrastructure

Almost everything you do with Redfish starts in one of three places: the **Systems** collection (the computer), the **Chassis** collection (the physical box) and the **Managers** collection (the BMC). A GPU server is more than one computer: a host, a GPU baseboard, maybe DPUs. If you understand how these three families connect, you can find a GPU's temperature, a power supply's status or a BMC's firmware version on any server, even one you have never seen.

## Prerequisites and outcomes

You need chapters 7.2 to 7.6. After this chapter you can:

- explain what a `ComputerSystem`, a `Chassis` and a `Manager` each stand for
- name the main things stored under each
- follow `Links` between them and check that they agree
- explain how blades, DPUs and GPU baseboards fit
- run a tool that prints an inventory from any service

## 1. Three questions, three families

Ask three different questions about a server:

| Question | Family | Think of it as |
|---|---|---|
| "What does the **software** see?" | `Systems` (`ComputerSystem`) | the computer: CPUs, memory, BIOS, boot, power state |
| "What is the **physical thing**?" | `Chassis` | the metal box: fans, power supplies, sensors, location |
| "Who is **managing** it?" | `Managers` (`Manager`) | the BMC: its network, users, logs, firmware |

The Redfish schema guide describes the chassis as "the sheet-metal confined spaces and logical zones such as racks, enclosures, chassis and all other containers". It adds that subsystems such as sensors, which work outside of the system's data plane, are linked through the chassis. So a temperature sensor belongs to the chassis because the BMC reads it directly, even when the host operating system is off.

```mermaid
flowchart LR
    SYS(["ComputerSystem<br/>the computer"])
    CH["Chassis<br/>the box"]
    MG{{"Manager<br/>the BMC"}}
    SYS -->|"Links.Chassis"| CH
    CH -->|"Links.ComputerSystems"| SYS
    SYS -->|"Links.ManagedBy"| MG
    MG -->|"Links.ManagerForServers"| SYS
    CH -->|"Links.ManagedBy"| MG
    MG -->|"Links.ManagerForChassis"| CH
```

Every relationship is normally written from **both sides**. That helps clients who start at either end: from a system you find its box, from a box you find its systems.

## 2. ComputerSystem: the computer

The schema calls it "a computer or system instance and the software-visible resources" of it. A `ComputerSystem` answer has:

**Identity.** `Model`, `Manufacturer`, `SerialNumber`, `PartNumber`, `SKU`, `UUID` (opaque, per RFC 4122), `HostName` (as reported by the OS), `AssetTag` (user set). `SystemType` says what kind: `Physical`, `Virtual`, `PhysicallyPartitioned`, `VirtuallyPartitioned`, `Composed`, `DPU`, and `OS` (deprecated since v1.21).

**State.** `PowerState` (`On`, `Off`, `PoweringOn`, `PoweringOff`, `Paused`) and `Status` with `State`, `Health` (`OK`, `Warning`, `Critical`) and `HealthRollup`. `HealthRollup` is the worst health of the resource and everything below it. When a chassis fan is bad the system health may show `Warning` even if the CPU is fine. `LastResetTime` tells you when it last restarted, and `BootProgress` gives the last boot state.

**Summaries.** `ProcessorSummary` and `MemorySummary` give a quick count and total (for example `TotalSystemMemoryGiB`). The schema says these cover only the processors that run system code, not offload processors. For detail follow the links below.

**Links to sub-collections**, each holding its own resources:

| Property | What it links to |
|---|---|
| `Processors` | CPUs and also GPUs, FPGAs and accelerators (`ProcessorType` is `CPU`, `GPU`, `FPGA`, `DSP`, `Accelerator`, `Core`, `Thread`, `Partition` or `OEM`) |
| `Memory`, `MemoryDomains` | DIMMs and memory regions |
| `Storage` | drives and storage controllers |
| `EthernetInterfaces`, `NetworkInterfaces` | the host's network interfaces |
| `Bios` | BIOS settings (chapter 7.9) |
| `SecureBoot` | Secure Boot state and keys (chapter 7.15) |
| `LogServices` | the system's logs (chapter 7.11) |
| `OperatingSystem` | information about the running OS |
| `TrustedModules` | TPM-type devices |

**Boot control.** `Boot` holds the one-time or continuous boot override: `BootSourceOverrideEnabled` (`Disabled`, `Once`, `Continuous`), `BootSourceOverrideTarget` (`None`, `Pxe`, `Hdd`, `Cd`, `Usb`, `BiosSetup`, `Diags`, `UefiShell`, `UefiTarget`, `UefiHttp`, `RemoteDrive`, `UefiBootNext`, `Recovery` and a few more; `UefiHttp` is the HTTP network boot from chapter 6.22) and `BootSourceOverrideMode` (`Legacy` or `UEFI`). This is how provisioning tools say "boot from the network once". Chapter 7.14 uses it.

**Other:** `PowerRestorePolicy` (what to do when power returns: `AlwaysOn`, `AlwaysOff`, `LastState`), `LocationIndicatorActive` (blink the identification light), `IndicatorLED` (deprecated).

**Actions:** `ComputerSystem.Reset` (chapter 7.5), `SetDefaultBootOrder`, and (in the schema version I read) `Decommission`, `AddResourceBlock` and `RemoveResourceBlock`. I did not use the last three.

### Systems that are not the main host

A single physical server may expose **more than one** `ComputerSystem`:

- A **DPU** (data processing unit, such as a SmartNIC) is its own small computer with `SystemType: DPU`. DMTF's SmartNIC example has a host system and a second system `Card1-SoC` of type DPU, managed by the same BMC.
- A **GPU baseboard** may appear as its own system. My mock follows the user's notes: a host system plus a second system for the GPU board, which holds the GPUs under `Processors`.
- A **blade** enclosure holds several blade servers. DMTF's example shows four systems with four blade BMCs, plus one enclosure manager.

So never assume one system per BMC. Loop over the whole collection.

## 3. Chassis: the physical box

The schema describes `Chassis` as the physical components of a system. What matters most:

**Identity and type.** `ChassisType` has these values: `Rack`, `Blade`, `Enclosure`, `StandAlone`, `RackMount`, `Card`, `Cartridge`, `Row`, `Pod`, `Expansion`, `Sidecar`, `Zone`, `Sled`, `Shelf`, `Drawer`, `Module`, `Component`, `IPBasedDrive`, `RackGroup`, `StorageEnclosure`, `ImmersionTank`, `HeatExchanger`, `PowerStrip`, `Other`. A server is usually `RackMount`. Cooling and power gear shows up here too, so a PDU, a power shelf and a coolant distribution unit are all `Chassis` resources.

**Place in the world.** `Location` (slot, rack, position), `AssetTag`, `Replaceable`, `HotPluggable`, `PhysicalSecurity` (intrusion state).

**Environment.** This is where most health and monitoring data lives:

| Property | What it links to |
|---|---|
| `Sensors` | all sensors: temperature, power, voltage, fan speed (chapter 7.8) |
| `ThermalSubsystem` | fans, heaters and a thermal summary |
| `PowerSubsystem` | power supplies, batteries, input and output power |
| `EnvironmentMetrics` | total power and energy, temperature summary |
| `Controls` | adjustable settings such as a power cap |
| `Assembly` | the replaceable parts with part numbers |
| `Drives`, `NetworkAdapters`, `PCIeDevices` | hardware inside this box |
| `Power`, `Thermal` | the older, deprecated ways to expose the same data |

**Containment.** A chassis can contain others. `Links.Contains` and `Links.ContainedBy` express this. An enclosure `Contains` blades, a server `Contains` a card.

## 4. Manager: the BMC itself

A `Manager` resource describes the managing controller. `ManagerType` says what it is:

| Value | Meaning |
|---|---|
| `BMC` | a controller managing one or more computer systems. This is a server's BMC |
| `EnclosureManager` | manages a chassis or group of systems (a blade enclosure) |
| `RackManager` | manages part or all of a rack |
| `ManagementController` | the generic value when none of the others fit |
| `AuxiliaryController` | manages one subsystem or device group |
| `Service` | a software service that provides management |

Under a manager you find the BMC's own world:

| Property | What it links to |
|---|---|
| `FirmwareVersion` | the BMC firmware version string |
| `EthernetInterfaces` | the BMC's network ports and addresses (IPs, DHCP, VLAN) |
| `NetworkProtocol` | which services the BMC runs: `HTTP`, `HTTPS`, `SSH`, `IPMI`, `SNMP`, `SSDP`, `NTP`, `Telnet`, `KVMIP`, `VirtualMedia`, `FTP`, `SFTP`, `RDP`, `RFB`, `Proxy` (chapter 7.15 turns off what you do not need) |
| `LogServices` | the BMC's event logs (chapter 7.11) |
| `HostInterfaces` | the private channel between BMC and host OS |
| `SerialInterfaces`, `CommandShell`, `GraphicalConsole`, `VirtualMedia` | console and media access (chapter 7.1) |
| `DateTime`, `DateTimeLocalOffset`, `TimeZoneName` | the BMC's clock. A wrong clock makes logs hard to match |
| `LastResetTime` | when the BMC last restarted |
| `Redundancy` | how it pairs with other managers |

**Actions:** `Manager.Reset` restarts the BMC (the schema says that if the manager provides the Redfish service it must send the answer before resetting to avoid client timeouts). `Manager.ResetToDefaults` takes `ResetAll`, `PreserveNetworkAndUsers` or `PreserveNetwork`, so a factory reset can keep the network and accounts. `ForceFailover` and `ModifyRedundancySet` apply to redundant managers.

`Manager.Reset` is the Redfish way to do what `ipmitool mc reset cold` does in the NVIDIA firmware notes (chapter 7.1).

The manager's `Links` list `ManagerForServers`, `ManagerForChassis` and `ManagerInChassis` (the box the BMC is physically in).

## 5. Seeing it: the model tool

`code/part07/rf_model.py` finds the three families from the service root, prints them and their links, and checks that the links agree. I ran it on DMTF's example of a blade enclosure. This is a clean redraw of what it found:

```mermaid
flowchart TB
    EM{{"MultiBladeBMC<br/>EnclosureManager"}}
    ENC["MultiBladeEncl<br/>Enclosure"]
    ENC -->|ManagedBy| EM
    ENC -->|Contains| B1["Blade1"]
    ENC -->|Contains| B2["Blade2"]
    ENC -->|Contains| B3["Blade3"]
    ENC -->|Contains| B4["Blade4"]
    B1 -->|ManagedBy| M1{{"Blade1BMC<br/>BMC"}}
    B2 -->|ManagedBy| M2{{"Blade2BMC<br/>BMC"}}
    B3 -->|ManagedBy| M3{{"Blade3BMC<br/>BMC"}}
    B4 -->|ManagedBy| M4{{"Blade4BMC<br/>BMC"}}
    S1(["System 529QB9450R6"]) -->|Chassis| B1
    S2(["System 529QB9451R6"]) -->|Chassis| B2
    S3(["System 529QB9452R6"]) -->|Chassis| B3
    S4(["System 529QB9453R6"]) -->|Chassis| B4
    S1 -->|ManagedBy| M1
    S2 -->|ManagedBy| M2
    S3 -->|ManagedBy| M3
    S4 -->|ManagedBy| M4
```

Five managers, five chassis, four systems. One enclosure manager looks after the box; each blade has its own BMC. This is why "one server equals one BMC" is a habit to unlearn.

### The link check

For each link A to B the tool looks for the matching B to A link. Results on the examples:

| Service | Result |
|---|---|
| my DGX-style mock (after I fixed it) | 0 findings |
| DMTF rack server | 0 findings |
| DMTF blade enclosure | 0 findings |
| DMTF PDU | 1 one-way link: the chassis says it is managed by the BMC but the manager does not list the chassis |
| DMTF power shelf | the same kind of one-way link |
| DMTF cooling unit | the same kind of one-way link |
| DMTF SmartNIC card | 1 dangling link: the host chassis `Contains` a `Card2` that is not in the collection |

My own mock failed the check at first with two one-way links, which I fixed. That is a good result for the lab: the checker catches the kind of slip that happens when someone builds a Redfish service by hand. The findings in DMTF's examples are not necessarily errors. The first three are the one-way ManagedBy kind that the spec does not forbid, and the dangling link may simply stand for an empty slot. **Treat each finding as a question, not a verdict.**

## 6. The inventory tool

`code/part07/rf_inventory.py` prints one line per computer system. It discovers everything from the root and skips what is missing. Output for my GPU-style mock:

```text
system=System_0  type=Physical  model=GPU-8  serial=SN0001  power=On  health=OK  cpus=2  mem_gib=2048  bmc=BMC_0  bmc_fw=1.0.0
system=HGX_Baseboard_0  type=Physical  power=On  health=OK  gpus=8  bmc=BMC_0  bmc_fw=1.0.0
```

and for DMTF's SmartNIC example (two systems, one BMC):

```text
system=437XR1138R2  type=Physical  model=3500  ... power=On  health=OK  bios=P79 v1.45 (12/06/2017)  cpus=2  gpus=0  mem_gib=96  bmc=BMC  bmc_fw=1.45.455b66-rev4
system=Card1-SoC  type=DPU  model=9900  ...  power=On  health=OK  cpus=1  gpus=0  mem_gib=8  bmc=BMC  bmc_fw=1.45.455b66-rev4
```

Add `--csv` to get a spreadsheet-friendly table. This is the seed of a fleet inventory (chapter 7.14): run it on every BMC and keep the result. Two things to know: `health` here uses `HealthRollup`, which includes everything under the system, and many fields are optional so some columns may be empty on a real BMC.

## 7. Present, absent and temporarily unavailable

The spec has rules (9.11) for empty slots and sleeping devices that help you read trees correctly:

- A resource can stay in the tree to show a **capability**, such as an empty DIMM socket or drive bay. Its `Status.State` is **`Absent`**. Required properties with no known value are `null`.
- If a new part is later put in that slot, the same resource now describes a **different physical thing**. Do not keep old read-only data such as the serial number.
- A device that is **temporarily unreachable** (for example a network card in low power) should show `Status.State` **`StandbyOffline`** and keep its URI.

So when you count DIMMs or drives, do not count resources, count those whose `State` is not `Absent`.

## 8. Steps for finding a value

Example: "What is the temperature of GPU 3 on a server I have never seen?"

1. `GET /redfish/v1/` and read the `Systems` link.
2. `GET` that collection and read every `Members` link. Open each system.
3. Look at `Processors` in each system and filter by `ProcessorType` equals `GPU`.
4. Open the GPU you want. Follow its `EnvironmentMetrics` link if present (the user's notes show this link for NVIDIA GPUs, chapter 7.13) or find the matching sensor under the chassis.
5. If neither exists, search the chassis `Sensors` by `PhysicalContext` (for example `GPU`).

Because the layout differs between makers, a robust tool tries a standard route first and falls back to a second one. Section 8 of chapter 7.8 returns to this.

## 9. DGX and HGX: what the notes say

The user's notes describe a DGX H100 like this. They are given as the notes state them, and I have not checked them against NVIDIA's documents:

- The DGX H100 and H200 use a system named `DGX`, a manager named `BMC` and a chassis named `DGX`.
- A second system, `HGX_Baseboard_0`, represents the GPU baseboard. GPU data is under `/redfish/v1/Systems/HGX_Baseboard_0/Processors/GPU_SXM_<id>/EnvironmentMetrics`.
- The notes call out a dual-tray design: a host motherboard tray and a GPU tray, with satellite controllers that report to the main BMC (chapter 7.1).
- The BCM manual's Redfish appendix shows a different naming: chassis such as `BMC_0`, `CBC_0`, `Chassis_0` on GB300 nodes. So names differ between DGX generations. This is the reason the discovery rule in chapter 7.2 exists.

My mock's `dgx` profile copies the shape (a host system, a baseboard system with eight GPU processors and per-GPU metrics, one chassis, one BMC) but the names inside are invented.

## 10. Exercises

1. Run `rf_model.py` on the mock and on a DMTF example (serve one with `redfish_mock.py --mockup`). Draw the graph by hand.
2. Run `rf_inventory.py --csv` against the blade example. Why are there four systems but five managers?
3. In the SmartNIC example find the DPU. What `SystemType` does it have and what manages it?
4. Write a function that, given a ComputerSystem, returns the list of its GPUs (by `ProcessorType`), without using any fixed URI.
5. Break one link in the mock on purpose (remove `ManagerForChassis`). Does the checker find it?
6. For a server in your own lab or a vendor demo, list which of `Power`/`Thermal` (old) or `PowerSubsystem`/`ThermalSubsystem` (new) are present.

## 11. Interview angles

- "What is the difference between a System, a Chassis and a Manager?" The computer, the box, the BMC. Say where sensors live (chassis) and where BIOS lives (system).
- "A GPU server has two Systems. Why?" A GPU baseboard or DPU can be its own system. Loop through the collection and filter by type.
- "How do you map a GPU to its temperature?" Follow links: system, processors, GPU, its metrics or the chassis sensors. Use discovery.
- "What does HealthRollup mean?" The worst health among the resource and everything beneath it. It is a summary, so open the children to find the cause.

## 12. Checkpoint questions (20)

1. What does the `Systems` family describe?
2. What does `Chassis` describe?
3. What does `Managers` describe?
4. Why do sensors live under the chassis?
5. What is `HealthRollup`?
6. What is `SystemType: DPU`?
7. How can a server have more than one `ComputerSystem`?
8. Name four sub-collections reachable from a system.
9. What do `Processors` contain besides CPUs?
10. What are the three settings of `BootSourceOverrideEnabled`?
11. Name three `ChassisType` values.
12. What are `ThermalSubsystem` and `PowerSubsystem` and what replaced them?
13. What do `Contains` and `ContainedBy` mean?
14. What is a `ManagerType` of `EnclosureManager`?
15. What does `NetworkProtocol` hold?
16. What does `Manager.Reset` do?
17. What does `PreserveNetworkAndUsers` do?
18. What does `State: Absent` mean and how should you count DIMMs?
19. Why check that links agree in both directions?
20. Why must scripts not assume one system and one BMC per server?

## 13. Sources and review notes

- **Redfish Resource and Schema Guide DSP2046 (2024.4), and the official JSON Schemas** (`ComputerSystem` v1.23.1, `Chassis` v1.26.0, `Manager` v1.20.0 and later, `Processor` v1.20.1, `ManagerNetworkProtocol` v1.10.1, `Resource`): property descriptions, enumerations (`SystemType`, `ChassisType`, `ManagerType`, `ProcessorType`, `State`, `Health`, `ResetType`) and the Manager actions.
- **Redfish Specification DSP0266 v1.21.0:** absent and transiently unavailable resources (9.11), resource tree stability and discovery (12.3, 12.4).
- **DMTF example trees** from `github.com/DMTF/Redfish-Publications` (commit `fa6d23d9`): rack server, blade enclosure, SmartNIC, PDU, power shelf, cooling unit, liquid-cooled server.
- **BCM 11 Administrator Manual**, appendix N: device naming on GB300 hardware.
- **NVIDIA-DevOps notes (volume 05 chapter 3, volume 10 chapter 1):** DGX system, chassis and manager names, `HGX_Baseboard_0`, the dual-tray description. Not verified.
- **Run here:** `rf_model.py` (8 services), `rf_inventory.py` (4 services), `schema_lab.py` (still 11 passes as the mock grew to 110 resources).
- **Not verified:** how a real DGX, HGX or GB200 tree looks, which of the optional links the BMC fills in, and whether its `Contains` links are complete. Part 9 and chapter 7.13 revisit this.
