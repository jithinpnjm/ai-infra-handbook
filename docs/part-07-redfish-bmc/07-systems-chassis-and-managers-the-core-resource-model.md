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
| Status | Drafted (`rf_model.py`, `rf_inventory.py`, and `model_inventory_lab.py` 3/3 self-checks pass against mock and DMTF trees; **untested** / **not verified** on live BMC) |

## Why this matters for AI infrastructure

Picture a GPU server that runs hot in the middle of a training job. The run is slowing down, the fans sound louder than usual, and someone asks you for the GPU's temperature, the state of its power supplies and the BMC firmware version. The catch is that you have never logged into this machine before. You have a web address, a login and a few minutes. Redfish is the web interface that gets you those answers, and every search through it starts in one of three places: the `Systems` collection (the computer), the `Chassis` collection (the physical box) and the `Managers` collection (the BMC). Once you know which of the three holds which fact, you can find a temperature, a power supply's status or a firmware version on any server, including one you have never seen.

The reason three places are needed is that a GPU server is more than one computer. It may hold a host CPU computer, a GPU baseboard with its own processors, and a few network cards that run their own operating systems. Each of those has parts of its own. The metal box they sit in, however, has fans and power supplies that belong to none of them alone. The BMC (baseboard management controller, a small computer on the board that watches over the rest) sits to one side and watches all of it. Splitting the server into three families gives each question one clear home, so you do not have to dig through a single long list of properties to find an answer.

## Prerequisites and outcomes

Before you start, work through chapters 7.2 to 7.6. They give you the background this chapter builds on, so the names and links below will feel familiar rather than new. This chapter then takes the three core families one at a time. It explains what a `ComputerSystem`, a `Chassis` and a `Manager` each stand for, which parts sit under each one, and how the `Links` join them together. It also shows how blades, DPUs and GPU baseboards fit into the picture, and it ends with a tool that prints an inventory from any Redfish service.

## 1. Three questions, three families

When you look at a server, you are really asking three different questions. Each question has its own family, and knowing which family to open saves you from searching the wrong place. Think of a help desk. A caller might say "the server is hot", "the server will not boot" or "who do I call about the fan". Each complaint points at a different part of the system, and a good technician knows where to look for each one.

The table gives each question, the family that answers it and a plain picture of what that family holds.

| Question | Family | Think of it as |
|---|---|---|
| "What does the **software** see?" | `Systems` (`ComputerSystem`) | the computer: CPUs, memory, BIOS, boot, power state |
| "What is the **physical thing**?" | `Chassis` | the metal box: fans, power supplies, sensors, location |
| "Who is **managing** it?" | `Managers` (`Manager`) | the BMC: its network, users, logs, firmware |

The Redfish schema guide describes a chassis as "the sheet-metal confined spaces and logical zones such as racks, enclosures, chassis and all other containers". Sensors are the part that matters most here. The guide says that subsystems such as sensors work outside the system's data plane, which is the part of the machine that runs your workload. Because of that, sensors are linked through the chassis. A temperature sensor therefore belongs to the chassis, because the BMC reads it directly, even when the host operating system is off. If you have ever seen a server show a temperature on its management page while its operating system is powered down, this is why.

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

Every relationship is normally written from both sides. The system points to its box, and the box points back to the system. That lets a client start at either end. From a system you find its box, and from a box you find its systems. Think of a two-way street sign, where the road names the town at one end and the town names the road at the other. If only one side is written down, a script that starts from the other end walks into a dead end. Section 5 of this chapter shows a tool that checks for exactly that kind of gap.

## 2. ComputerSystem: the computer

Suppose a job runs slowly and you want to know what the operating system actually sees. Maybe the scheduler reports fewer cores than the node's spec sheet promised. The schema calls a `ComputerSystem` "a computer or system instance and the software-visible resources" of that machine. Reading one resource tells you a lot before you open anything else, so it is the natural first stop for almost any question about the host.

Start with identity. A `ComputerSystem` carries `Model`, `Manufacturer`, `SerialNumber`, `PartNumber`, `SKU`, `UUID`, `HostName` and `AssetTag`. These fields answer the question "which machine is this?" The `UUID` is opaque and follows RFC 4122, which is a standard format for unique identifiers. Treat it as a label and never try to read meaning into its characters. `HostName` is whatever the operating system reports, so it can differ from the name in your inventory system. `AssetTag` is set by a person, so it is only as accurate as the last person who typed it. `SystemType` says what kind of computer this is. It can be `Physical`, `Virtual`, `PhysicallyPartitioned`, `VirtuallyPartitioned`, `Composed`, `DPU` or `OS`. The `OS` value has been deprecated since v1.21, so you may still see it on older firmware, but new services should use the other values.

Next comes state, which is the answer to "is it on, and is it healthy?" `PowerState` can be `On`, `Off`, `PoweringOn`, `PoweringOff` or `Paused`. `Status` holds `State`, `Health` (`OK`, `Warning` or `Critical`) and `HealthRollup`. `HealthRollup` is the worst health of the resource and everything below it. That means a bad chassis fan can make the system show `Warning` even when the CPU is fine. The roll-up works like a report card with one red mark. The summary turns red, and you still have to look at the subject that failed. `LastResetTime` tells you when the system last restarted, which is useful when a machine rebooted overnight and nobody knows why. `BootProgress` gives the last boot state the firmware reported.

`ProcessorSummary` and `MemorySummary` give you a quick count and total, such as `TotalSystemMemoryGiB`. The schema says these cover only the processors that run system code, not offload processors. So a GPU count in the summary may be missing, and you should follow the links when you need detail. Each link in the table below points to a sub-collection that holds its own resources. Think of the system as a front door with labelled rooms behind it. The summary tells you how big the house is, and the links take you into each room.

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

Boot control lives in `Boot`. This is where the one-time or continuous boot override sits. It is the switch a provisioning tool flips when it wants a server to start from somewhere other than its usual disk, such as the network. `BootSourceOverrideEnabled` can be `Disabled`, `Once` or `Continuous`. `BootSourceOverrideTarget` names where to boot from, with values such as `None`, `Pxe`, `Hdd`, `Cd`, `Usb`, `BiosSetup`, `Diags`, `UefiShell`, `UefiTarget`, `UefiHttp`, `RemoteDrive`, `UefiBootNext`, `Recovery` and a few more. `UefiHttp` is the HTTP network boot from chapter 6.22. `BootSourceOverrideMode` is either `Legacy` or `UEFI`, which describes the firmware style the machine should use for that boot. Provisioning tools use these three fields together to say "boot from the network once". Chapter 7.14 uses them in a real workflow.

A few other fields are worth knowing. `PowerRestorePolicy` decides what happens when power returns, with the values `AlwaysOn`, `AlwaysOff` and `LastState`. It answers the question "what should this server do after a power cut?" `LocationIndicatorActive` turns on the identification light, which helps a technician find the right server in a crowded row. `IndicatorLED` is deprecated, so prefer `LocationIndicatorActive` in new scripts. The actions include `ComputerSystem.Reset` (chapter 7.5) and `SetDefaultBootOrder`. The schema version used for this chapter also lists `Decommission`, `AddResourceBlock` and `RemoveResourceBlock`. None of those three appears in the labs here, so you can read about them and move on.

### Systems that are not the main host

One physical server can expose more than one `ComputerSystem`. This surprises most people the first time they see it, because the habit from ordinary servers is one box and one computer. Once you know to look for it, the extra systems are easy to spot. You will meet three common cases.

- Can a network card count as a computer? Yes, when it is a DPU (data processing unit, such as a SmartNIC). A DPU is a small computer of its own, with `SystemType: DPU`. It has its own cores and its own operating system, and the server's BMC manages it too. DMTF's SmartNIC example has a host system and a second system, `Card1-SoC`, of type DPU. The same BMC manages both.
- Does a GPU board ever appear as its own system? Yes, and this is common in dense GPU servers. The practice mock in this chapter follows the NVIDIA-DevOps notes. It has a host system plus a second system for the GPU board, which holds the GPUs under `Processors`.
- What about a blade enclosure? A blade enclosure holds several blade servers that slide into one shared frame. DMTF's example shows four systems with four blade BMCs, plus one enclosure manager.

So never assume one system per BMC. Loop over the whole collection. A script that reads only the first member will miss the second system, and it will report a half-empty picture without raising any error. That kind of silent gap is harder to catch than a crash.

## 3. Chassis: the physical box

Think of a chassis as the metal you could touch. The schema describes `Chassis` as the physical components of a system. When a technician walks down a row with a cart, they are really looking at chassis. Two things matter most: what kind of box it is, and what it holds.

`ChassisType` tells you the box type. The values are `Rack`, `Blade`, `Enclosure`, `StandAlone`, `RackMount`, `Card`, `Cartridge`, `Row`, `Pod`, `Expansion`, `Sidecar`, `Zone`, `Sled`, `Shelf`, `Drawer`, `Module`, `Component`, `IPBasedDrive`, `RackGroup`, `StorageEnclosure`, `ImmersionTank`, `HeatExchanger`, `PowerStrip` and `Other`. A server is usually `RackMount`. Cooling and power gear also appears here, so a PDU (power distribution unit, the strip of outlets inside a rack), a power shelf and a coolant distribution unit are all `Chassis` resources. The type matters because a script often needs to skip anything that is not a server.

`Location` gives the slot, rack and position, which is the answer to "where is it?" `AssetTag`, `Replaceable` and `HotPluggable` describe the part itself. `Replaceable` says whether a technician is allowed to swap the part out. `HotPluggable` says whether the part can be swapped while the power stays on. `PhysicalSecurity` reports the intrusion state, which tells you whether a cover or door has been opened.

Most health and monitoring data lives under the environment properties. The table shows where to look for each kind of reading.

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

A chassis can hold other chassis. `Links.Contains` and `Links.ContainedBy` express this nesting. For example, an enclosure `Contains` blades, and a server `Contains` a card. Read it the way you would read a shipping carton that holds smaller boxes. The outer box lists what is inside, and each inner box names the carton it sits in. If a temperature reading looks wrong, start at `Sensors`. If a fan or a power supply looks wrong, go to `ThermalSubsystem` or `PowerSubsystem`. Those two starting points save you from scanning the whole tree every time something looks odd.

## 4. Manager: the BMC itself

Here is the question a `Manager` answers: which controller is looking after this box? When a server will not respond to a remote login, that is the first thing you need to know, because the BMC may still be running even when the host is not. A `Manager` resource describes that managing controller. Its `ManagerType` property says what kind of controller it is.

| Value | Meaning |
|---|---|
| `BMC` | a controller managing one or more computer systems. This is a server's BMC |
| `EnclosureManager` | manages a chassis or group of systems (a blade enclosure) |
| `RackManager` | manages part or all of a rack |
| `ManagementController` | the generic value when none of the others fit |
| `AuxiliaryController` | manages one subsystem or device group |
| `Service` | a software service that provides management |

Under a manager you find the BMC's own world. The BMC is a small computer of its own, with its own firmware, its own network port and its own clock, so it has its own set of properties. The table lists what the controller knows about itself and what it exposes.

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

`Manager.Reset` restarts the BMC. The schema says that if the manager provides the Redfish service, it must send the answer before resetting, so the client gets a clean reply. That rule exists because the client is waiting on the web response. If the BMC resets before the answer leaves, the client sees a timeout and cannot tell whether the reset worked. `Manager.ResetToDefaults` takes `ResetAll`, `PreserveNetworkAndUsers` or `PreserveNetwork`, so a factory reset can keep the network and the accounts. Keeping those two is the difference between a reset you can recover from remotely and one that locks you out of a machine in another building. `ForceFailover` and `ModifyRedundancySet` apply to redundant managers, which are pairs of controllers that take over for each other.

`Manager.Reset` is the Redfish way to do what `ipmitool mc reset cold` does in the NVIDIA firmware notes (chapter 7.1). `ipmitool` is the older command-line tool for the same job, so you can think of this action as the same reset with a web address instead of a command. The manager's `Links` list `ManagerForServers`, `ManagerForChassis` and `ManagerInChassis`. The last one names the box the BMC is physically in, which is useful when a BMC sits on a shared board and you need to know which rack slot it belongs to.

## 5. Seeing it: the model tool

Reading a service tree by hand gets tedious quickly. A single server can hold dozens of collections, and each collection can hold more links. `code/part07/rf_model.py` does the walking for you. It finds the three families from the service root, prints them with their links, and checks that the links agree with each other.

Running it against DMTF's example of a blade enclosure gives the picture below. The drawing is a clean version of what the tool found, with the links laid out so you can follow them.

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

Look at the counts. There are five managers, five chassis and four systems. One enclosure manager looks after the whole box, and each blade has its own BMC. This is why "one server equals one BMC" is a habit you need to unlearn. The habit does no harm on a single pizza-box server, but it breaks down in a dense rack. A script built on it will quietly miss hardware, and you may not notice until a count looks wrong.

### The link check

The tool checks every link. For each link from A to B, it looks for the matching link from B back to A. A missing partner is a one-way link, and a link that points at a resource that does not exist is dangling. Here are the results on the examples. These results come from the mock and DMTF trees, and they were not run against a live BMC.

| Service | Result |
|---|---|
| practice DGX-style mock (after its fix) | 0 findings |
| DMTF rack server | 0 findings |
| DMTF blade enclosure | 0 findings |
| DMTF PDU | 1 one-way link: the chassis says it is managed by the BMC but the manager does not list the chassis |
| DMTF power shelf | the same kind of one-way link |
| DMTF cooling unit | the same kind of one-way link |
| DMTF SmartNIC card | 1 dangling link: the host chassis `Contains` a `Card2` that is not in the collection |

The practice mock failed the check at first, with two one-way links. Both were fixed. That is a good result for the lab, because the checker catches the kind of slip that happens when someone builds a Redfish service by hand. The findings in DMTF's examples are not necessarily errors. The PDU, power shelf and cooling unit findings are the one-way `ManagedBy` kind, which the spec does not forbid. The dangling SmartNIC link may simply stand for an empty slot whose card was never installed. **Treat each finding as a question, not a verdict.** Ask why the link is one-way before you decide that the vendor got it wrong.

## 6. The inventory tool

Once you can see the tree, you usually want a flat list, one line per server, that you can sort and compare. `code/part07/rf_inventory.py` prints one line per computer system. It discovers everything from the root and skips whatever is missing, so it does not stop on the first gap in the tree. Here is the output for the GPU-style practice mock.

```text
system=System_0  type=Physical  model=GPU-8  serial=SN0001  power=On  health=OK  cpus=2  mem_gib=2048  bmc=BMC_0  bmc_fw=1.0.0
system=HGX_Baseboard_0  type=Physical  power=On  health=OK  gpus=8  bmc=BMC_0  bmc_fw=1.0.0
```

Notice that the second line has no `model` or `serial` value. The baseboard is a system in its own right, but the vendor did not fill in those fields for it, so the tool prints nothing there. For DMTF's SmartNIC example, which has two systems and one BMC, the output looks like this.

```text
system=437XR1138R2  type=Physical  model=3500  ... power=On  health=OK  bios=P79 v1.45 (12/06/2017)  cpus=2  gpus=0  mem_gib=96  bmc=BMC  bmc_fw=1.45.455b66-rev4
system=Card1-SoC  type=DPU  model=9900  ...  power=On  health=OK  cpus=1  gpus=0  mem_gib=8  bmc=BMC  bmc_fw=1.45.455b66-rev4
```

Add `--csv` if you want a table you can open in a spreadsheet. This output is the seed of a fleet inventory (chapter 7.14). Run the tool on every BMC and keep the results, so you can compare firmware versions next month and see which servers are behind. Two things to watch for. The `health` column uses `HealthRollup`, which includes everything under the system, so a warning in this column does not point at one part. Many fields are optional, so some columns may be empty on a real BMC. An empty cell is not a failure, and you should not treat it as one.

## 7. Present, absent and temporarily unavailable

Empty slots can mislead you when you count hardware. Picture a technician who counts memory sticks by counting the entries under a server's memory collection. The number may include sockets with nothing in them, so the count comes out too high. Suppose you count the DIMMs (dual inline memory modules, the memory sticks that plug into a motherboard) in a server by counting the resources under `Memory`. The number you get may include sockets with nothing in them. Section 9.11 of the Redfish spec sets out rules for empty slots and for devices that are asleep. Those rules help you read a tree correctly, and they are worth a few minutes of reading before you write any inventory script.

- A resource can stay in the tree to show a capability, such as an empty DIMM socket or drive bay. Its `Status.State` is `Absent`, and required properties with no known value are `null`. Why keep an empty slot at all? Because the tree describes what the machine could hold, not only what it holds today.
- If a new part is later put in that slot, the same resource now describes a different physical thing. Do not keep old read-only data such as the serial number. Otherwise a fresh DIMM would carry the old stick's identity, and your inventory would be wrong about it.
- A device that is temporarily unreachable, for example a network card in low power, should show `Status.State` `StandbyOffline` and keep its URI. The URI is the device's address in the tree, so the device stays findable when it wakes up.

So when you count DIMMs or drives, do not count resources. Count only those whose `State` is not `Absent`.

## 8. Steps for finding a value

Here is a question you may face on a server you have never seen: what is the temperature of GPU 3? You do not need to know the layout in advance. The steps below walk from the front door of the service to the number, one link at a time. Start at the service root, which is the entry point every Redfish service shares.

1. `GET /redfish/v1/` and read the `Systems` link.
2. `GET` that collection and read every `Members` link. Open each system.
3. Look at `Processors` in each system and filter by `ProcessorType` equals `GPU`.
4. Open the GPU you want. Follow its `EnvironmentMetrics` link if it is present. The NVIDIA-DevOps notes show this link for NVIDIA GPUs, in chapter 7.13. If the link is not there, find the matching sensor under the chassis.
5. If neither exists, search the chassis `Sensors` by `PhysicalContext`, for example `GPU`.

The layout differs between makers, so a robust tool tries the standard route first and falls back to a second one if it fails. A fallback works a bit like a spare key. You hope you will not need it, but you keep it on the ring because the first key sometimes breaks. Build your own lookup the same way. Section 8 of chapter 7.8 returns to this idea with sensor-specific examples.

## 9. DGX and HGX: what the notes say

Real GPU servers are harder to read than the examples in this chapter. DGX is NVIDIA's full GPU server, and HGX is its GPU baseboard design, which vendors place inside their own servers. The NVIDIA-DevOps notes describe a DGX H100 as follows. The notes are quoted as written. They have not been checked against NVIDIA's own documents, so treat them as a starting point for your own discovery work.

- The DGX H100 and H200 use a system named `DGX`, a manager named `BMC` and a chassis named `DGX`.
- A second system, `HGX_Baseboard_0`, represents the GPU baseboard. GPU data sits under `/redfish/v1/Systems/HGX_Baseboard_0/Processors/GPU_SXM_<id>/EnvironmentMetrics`.
- The notes call out a dual-tray design, with a host motherboard tray and a GPU tray. Satellite controllers report to the main BMC (chapter 7.1).
- The BCM manual's Redfish appendix uses different names. It lists chassis such as `BMC_0`, `CBC_0` and `Chassis_0` on GB300 nodes. Names therefore differ between DGX generations, and that is the reason the discovery rule in chapter 7.2 exists.

The `dgx` profile in the practice mock copies the shape of the DGX layout. It has a host system, a baseboard system with eight GPU processors and per-GPU metrics, one chassis and one BMC. The names inside it are invented, so they should not be read as NVIDIA's real names. The point of the profile is to give you something to practise on, and the names are there only to make the tree readable.

### 9.1 Why Redfish splits a server into `Systems`, `Chassis`, and `Managers`

When engineers first move from Linux host tools such as `lscpu`, `lspci` and `ipmitool` to Redfish, the split into `Systems`, `Chassis` and `Managers` can feel abstract. On a simple pizza-box server, you might ask why the CPUs, fans, power supplies and BMC IP address are not all in one big JSON object. The question is fair, and the answer only becomes obvious once you look at a dense rack.

Step into an AI data center and the answer changes. In dense infrastructure, **logical computers (`Systems`), physical enclosures (`Chassis`), and management controllers (`Managers`) do not map one-to-one**. One box can hold several computers, one computer can span several boxes, and one controller can look after both. Four real topologies make this clear. You will meet all four in an AI factory, and each one uses the same three Redfish collections and their reciprocal `Links`.

1. A multi-blade enclosure (`public-bladed-system`). One physical rack enclosure, `Chassis/MultiBladeEncl`, holds four independent server blades, `Chassis/Blade1` through `Chassis/Blade4`. Each blade contains one logical computer, `Systems/529QB9450R6` through `Systems/529QB9453R6`, and its own blade BMC, `Managers/Blade1BMC` through `Managers/Blade4BMC`. A fifth controller, `Managers/MultiBladeBMC` with `ManagerType: "EnclosureManager"`, manages the shared fans and power supplies of the outer enclosure. If Redfish merged `Chassis` and `Systems`, there would be nowhere to put the shared enclosure fans or the enclosure manager.
2. A dual-tray 8-GPU server (DGX H100 or HGX). One physical `8U` sheet-metal enclosure, or a pair of linked host and GPU trays, houses a host CPU computer, `Systems/System_0` or `Systems/DGX`. The same enclosure also houses an 8-GPU accelerator baseboard, `Systems/HGX_Baseboard_0`. The primary BMC, `Managers/BMC_0`, manages both logical systems, and the chassis thermal subsystem cools them.
3. A server equipped with BlueField-3 DPUs (`public-smartnic`). The PCIe network card inside the host server is itself a complete ARM computer. It runs its own Linux OS and has its own CPU cores, DDR5 memory, UEFI BIOS and boot order. In Redfish, the host server appears as one `ComputerSystem` with `SystemType: "Physical"`. The DPU card appears in the same `Systems` collection as a second `ComputerSystem`, with `SystemType: "DPU"`. Both point, through `Links.ManagedBy`, to the server's BMC.
4. Rack-level power and cooling gear (`public-pdu`, `public-power-shelf`, `public-cooling-unit`). A smart rack PDU, a 33 kW NVL72 power shelf or a liquid-cooling coolant distribution unit (CDU) does not run user jobs or boot a host OS. Its `Systems` collection is therefore empty or absent. It still has a physical enclosure, a `Chassis`, packed with voltage, current, flow and leak sensors under `Sensors`. It also has a network-connected controller under `Managers`. Because sensors and power supplies belong to `Chassis` rather than `Systems`, the same monitoring script, `rf_sensors.py`, that reads temperatures on a GPU server also reads outlet currents on a PDU and coolant flow on a CDU. You do not change a single line of code.

### 9.2 Deep dive into `ComputerSystem`: boot progress, watchdogs, and composition

Beyond CPU and memory counts, the `ComputerSystem` schema has operational properties that help you diagnose stuck reboots and automate bare-metal fleets. Bare metal means a server with no hypervisor or cloud layer in between, which is the usual state of a GPU node in a training cluster.

- `BootProgress`, with `LastState` and `LastStateTime`. Suppose a compute node takes ten minutes to reboot after a firmware update. Is it stuck in memory training, waiting on a slow PXE DHCP timeout, or already booting the Linux kernel? You do not have to open a serial console on fifty nodes by hand. Inspect the `BootProgress` object on `ComputerSystem` instead. Its `LastState` property reports structured progress milestones, such as `None`, `PrimaryProcessorInitializationStarted`, `MemoryInitializationStarted`, `PCIResourceConfigStarted`, `SystemHardwareInitializationComplete`, `PXEBootStarted`, `OSBootStarted` and `OSRunning`. `LastStateTime` gives the time of that state, and `OemLastState` holds vendor-specific POST codes. POST stands for power-on self-test, the checks the firmware runs at start-up, and each vendor adds its own codes on top of the standard milestones.
- `HostWatchdogTimer`, with `FunctionEnabled`, `TimeoutAction` and `Status`. A hardware watchdog timer on the BMC checks whether the host OS is still alive and petting the watchdog. The host OS does that by resetting the timer on a schedule. If the Linux kernel deadlocks in an interrupt storm and stops resetting the timer, the BMC carries out the action set in `TimeoutAction` and logs a Watchdog event in the SEL (system event log). `TimeoutAction` can be `None`, `ResetSystem`, `PowerCycle` or `PowerDown`. You can inspect or configure this policy declaratively through `HostWatchdogTimer` on `ComputerSystem`.
- `SerialConsole` and `GraphicalConsole`. As noted in chapter 7.1, Redfish does not carry interactive terminal or video streams inside JSON responses. Instead, `ComputerSystem` and `Manager` include `SerialConsole` blocks that show `SSH`, `Telnet`, the `IPMI` SOL enabled status, the port and `MaxConcurrentSessions`. They also include `GraphicalConsole` blocks for `KVMIP` and `RFB`. Automation can then verify whether console redirection is enabled or disabled across the whole fleet, which is a quick way to find the machines that someone left open to remote access.
- `TrustedModules` lists the hardware Trusted Platform Modules (TPM 2.0) installed on the host motherboard. A TPM is a small security chip that stores keys and measurements of the boot process. The list shows their `FirmwareVersion`, their `InterfaceType` (`TPM2_0`) and their `Status`. Check this list before you enable measured boot and hardware attestation (chapter 7.15).

### 9.3 Deep dive into `Manager`: the Host Interface (`DSP0270`) and network hardening

`ComputerSystem` models the host, and `Chassis` models the physical enclosure. The `Manager` resource shows the BMC microcontroller itself. Two subtrees under `/redfish/v1/Managers/{id}` deserve your attention, because they decide who can reach the BMC and how.

The first is `HostInterfaces`, at `/redfish/v1/Managers/{id}/HostInterfaces`. Chapter 7.1 showed how traditional IPMI uses the older motherboard KCS interface, `/dev/ipmi0`, for in-band talk between the host Linux OS and the local BMC. In-band means the traffic runs inside the machine, not over the network cable. The DMTF Redfish Host Interface Specification (DSP0270) modernizes this in-band path. The BMC emulates a point-to-point USB-NIC (LAN-over-USB) or PCIe network interface that the host OS can see. Tools running on the host, such as `nvsm` or `curl`, can then talk Redfish over HTTPS straight to the local BMC, without crossing the external switch fabric. The `HostInterfaces` collection lets you inspect three things. You can see whether this internal Host Interface is enabled (`InterfaceEnabled`). You can see which authentication modes it requires (`AuthNone`, `BasicAuth`, `RedfishSessionAuth`, `FirmwareAuth`). And you can judge whether a compromised host OS could use it to reconfigure the BMC. That last question is the one a security reviewer will ask first.

The second is `EthernetInterfaces` and `NetworkProtocol`. Under `Managers/{id}/EthernetInterfaces` you find the BMC's out-of-band network port, which is the separate path you use to reach the BMC when the host is down. The port shows `MACAddress`, `SpeedMbps`, `IPv4Addresses`, `DHCPv4`, `VLAN` and `FQDN`. Under `Managers/{id}/NetworkProtocol` you find the switchboard for every network daemon in the BMC: `HTTPS`, `HTTP`, `SSH`, `IPMI`, `SNMP`, `SSDP`, `Telnet`, `VirtualMedia`, `KVMIP` and `NTP`. When you bring a new rack into service, read these two resources to check three things. Every BMC should have a static or reserved IP, so it never changes under you. `NTP` should be enabled and point at your management time servers, so the logs line up. The insecure legacy protocols, `Telnet`, plain `HTTP` and `SSDP`, should be turned off, because every open daemon is one more door to check.

### 9.4 Auditing graph integrity across vendors with `rf_model.py`

Why build `code/part07/rf_model.py` to check reciprocal links? Each link has a partner that must point back to it, and vendors do not always keep both sides in step. The pairs are these.

- `Links.Chassis` ↔ `Links.ComputerSystems`
- `Links.ManagedBy` ↔ `Links.ManagerForServers` or `Links.ManagerForChassis`
- `Links.Contains` ↔ `Links.ContainedBy`

Your tools will start from different points in the resource graph, depending on the task. Suppose an inventory script starts at `Systems`. It follows `Links.Chassis` to find the physical rack slot that holds the system. It follows `Links.ManagedBy` to record the BMC firmware version. Now suppose a thermal alert fires on a fan sensor inside `Chassis/Blade3/Sensors`. The responder starts at `Chassis/Blade3` and follows `Links.ComputerSystems` to find which Slurm compute node must be drained before the blade overheats. Slurm is the scheduler that runs jobs on the cluster, and draining a node tells it to finish current work and accept no new jobs. Each script uses the same links, but from a different starting point.

Now imagine a BMC firmware bug that fills in `System -> Chassis` but forgets `Chassis -> ComputerSystems`. That is a `ONE-WAY` link. If it points `Links.Contains` at a URI that returns `404 Not Found`, that is a `DANGLING` link. In both cases one direction of your automation works while the reverse direction silently fails. The script that starts from the other end gets no error and simply finds nothing, which is the hardest kind of bug to notice. Running `rf_model.py` against any new server model or firmware release maps the whole System–Chassis–Manager topology in seconds. It generates a visual Mermaid diagram with `--mermaid`, and it tells you which directional links you can rely on in your production scripts.

In practice, running `rf_model.py` and `rf_inventory.py` together gives your platform team a Day-0 topology fingerprint for every new hardware SKU. Day-0 means the moment the hardware first arrives, before any operating system is installed. When a vendor delivers a new batch of GPU servers, DPUs or liquid-cooling manifolds, capture their System–Chassis–Manager graph before any host OS is installed. Verify that every `Status.State` is `Enabled`, not `Absent` or `StandbyOffline`. Then commit the resulting CSV and Mermaid map to your cluster architecture repository, so the next person to touch the rack starts from a known picture.

## Exercises

Each exercise uses either the mock services or the DMTF example trees from this chapter. Work through them in order, and keep the output of each one, because later exercises refer back to it.

1. Start with the link checker, `code/part07/model_inventory_lab.py`. Run `python3 code/part07/model_inventory_lab.py`. You should see `3/3` checks pass. Next, start `redfish_mock.py` with `--profile dgx`. Then run `python3 code/part07/rf_model.py http://127.0.0.1:18441 admin adminpass --mermaid`. The goal is to print the complete `System` ↔ `Chassis` ↔ `Manager` graph. Does every arrow have a partner going back?
2. Serve the DMTF multi-blade enclosure mockup, `$REDFISH_PUBLICATIONS/mockups/public-bladed-system`, with `redfish_mock.py --mockup`. Then run `rf_inventory.py --csv` from `code/part07/rf_inventory.py`. Why does the enclosure expose `4` `ComputerSystem` instances (`Blade1` to `Blade4`)? Why does it also expose `5` `Manager` instances? Name the five managers as `4` blade BMCs and `1` `MultiBladeBMC` with `ManagerType: "EnclosureManager"`.
3. Serve the DMTF SmartNIC mockup, `$REDFISH_PUBLICATIONS/mockups/public-smartnic`, and inspect `/redfish/v1/Systems/Card1-SoC`. What is its `SystemType`? Note that it should read `"DPU"`. How many CPUs and how much memory does it report? Expect `1` CPU and `8 GiB` of RAM. Then find which `Manager` controls both the host system (`437XR1138R2`) and the DPU, by reading `Links.ManagedBy`.
4. Write a 12-line Python function, `find_all_gpus(client)`. It starts at `/redfish/v1/`, walks every member of `Systems`, and looks through each system's `Processors` collection. It returns every processor where `ProcessorType == "GPU"`. Do not hard-code `"HGX_Baseboard_0"`. The function has to work on any generation of hardware, and a hard-coded name would break on the next one.
5. Open Check 3 in `code/part07/model_inventory_lab.py`. There, removing `ManagerForChassis` from `BMC_0` triggers `ONE-WAY /redfish/v1/Chassis/Chassis_0 --ManagedBy--> /redfish/v1/Managers/BMC_0`. Now point `Links.Chassis` at a URI that does not exist, `"/redfish/v1/Chassis/Ghost"`. Then test what `rf_model.check()` outputs. The label you should expect is `DANGLING`.
6. Write a short Python snippet that reads `/redfish/v1/Systems/System_0/Memory`. Count the total DIMM slots from `Members@odata.count`. Then count the populated ones using `Status.State != "Absent"`, which follows the rule in DSP0266 section 9.11. Sum `CapacityMiB` across the populated slots only. Leave out the empty sockets, because they have no capacity to add.

## 11. Interview angles

Use these as talking points when someone asks you about the core resource model. Each one starts from a question an interviewer might really ask.

- "What is the difference between a System, a Chassis and a Manager?" Answer that they are the computer, the box and the BMC. Say that sensors live under the chassis and that BIOS lives under the system.
- "A GPU server has two Systems. Why?" A GPU baseboard or a DPU can be its own system. Loop through the collection and filter by type, so your answer shows you know the server may hold more than one computer.
- "How do you map a GPU to its temperature?" Follow the links: the system, its processors, the GPU, and then its metrics or the chassis sensors. Use discovery, not hard-coded names, and say why that matters across generations.
- "What does HealthRollup mean?" It is the worst health among the resource and everything beneath it. It is a summary, so open the children to find the actual cause.

## Checkpoint questions (20)

<details>
<summary>1. What does the `Systems` (`ComputerSystem`) resource family represent in Redfish?</summary>

It is the logical computer that software sees. It holds the CPUs and accelerators (`Processors`), system RAM (`Memory`), `Bios`, `SecureBoot`, the `Boot` order and override settings, `Storage`, the host `EthernetInterfaces`, and `PowerState` (DSP2046 `ComputerSystem`).
</details>

<details>
<summary>2. What does the `Chassis` resource family represent in Redfish?</summary>

It is the physical enclosure: a sheet-metal box, tray, rack or container, such as `RackMount`, `Blade`, `Enclosure`, `Sled`, `Sidecar`, `ImmersionTank` or `PowerStrip`. It also holds the out-of-band physical telemetry (`Sensors`, `ThermalSubsystem`, `PowerSubsystem` and `EnvironmentMetrics`) and the physical slots (`PCIeDevices`, `NetworkAdapters` and `Drives`).
</details>

<details>
<summary>3. What does the `Managers` (`Manager`) resource family represent in Redfish?</summary>

It is the management controller itself, such as a server's `BMC`, an `EnclosureManager`, a `RackManager` or an `AuxiliaryController`. It holds the controller's `FirmwareVersion`, its out-of-band `EthernetInterfaces`, the `NetworkProtocol` services it runs, its `SerialInterfaces`, its `VirtualMedia` and its `LogServices`, such as the `SEL`.
</details>

<details>
<summary>4. Why do temperature, fan, and power sensors belong under `Chassis` rather than under `ComputerSystem`?</summary>

The sensors are wired directly to the BMC or chassis management buses, such as `I2C`, `SMBus` and `PMBus`. They work outside the host OS, so you can still read them when the logical `ComputerSystem` is powered off.
</details>

<details>
<summary>5. What is `Status.HealthRollup` on a `ComputerSystem` or `Chassis`, and how should an operator act when `Health` is `OK` but `HealthRollup` is `Warning`?</summary>

`HealthRollup` shows the worst health across the resource itself and everything beneath it, such as `Processors`, `Memory`, `Storage` and `Sensors`. If `Health` is `OK` but `HealthRollup` is `Warning`, the top-level system is still running. At least one child, such as a degraded DIMM or a fan, has a warning. Walk the subordinate collections, and you will find the faulty component.
</details>

<details>
<summary>6. What does `SystemType: "DPU"` mean on a `ComputerSystem` resource?</summary>

It means the `ComputerSystem` is a Data Processing Unit (DPU) or SmartNIC, such as an NVIDIA BlueField-3 card. The card has its own ARM cores, memory, OS and boot lifecycle. It is modeled as a separate `ComputerSystem` next to the host server's `Physical` system.
</details>

<details>
<summary>7. Give three architectural reasons why a single BMC endpoint might expose more than one `ComputerSystem` in `/redfish/v1/Systems`.</summary>

1. **Dual-tray GPU servers (DGX / HGX):** One `ComputerSystem` (`DGX` or `System_0`) is the host CPU tray. A second one (`HGX_Baseboard_0`) is the 8-GPU and NVSwitch baseboard.
2. **DPUs and SmartNICs:** One `ComputerSystem` with `SystemType: "Physical"` is the x86 host. Each installed DPU adds another `ComputerSystem` with `SystemType: "DPU"`.
3. **Multi-node and blade enclosures:** An enclosure manager exposes one `ComputerSystem` for each installed server blade, from `Blade1` to `Blade4`.
</details>

<details>
<summary>8. Name six subordinate collections or resources directly linked from a `ComputerSystem` resource.</summary>

`Processors`, `Memory`, `Storage`, `Bios`, `SecureBoot` and `EthernetInterfaces`. The list can also include `LogServices`, `NetworkInterfaces`, `TrustedModules`, `OperatingSystem` and `VirtualMedia`.
</details>

<details>
<summary>9. Which resource collection under `ComputerSystem` holds GPUs and FPGAs, and which property distinguishes them from host CPUs?</summary>

The `Processors` collection, at `/redfish/v1/Systems/<id>/Processors`, holds them. Each member's `ProcessorType` property tells you whether it is a `"CPU"`, a `"GPU"`, an `"FPGA"`, a `"DSP"`, an `"Accelerator"` or an `"OEM"` part.
</details>

<details>
<summary>10. Which three properties inside `ComputerSystem.Boot` control a one-time PXE or UEFI HTTP network boot?</summary>

1. `BootSourceOverrideEnabled`: set it to `"Once"` for a single boot, or to `"Disabled"` or `"Continuous"`.
2. `BootSourceOverrideTarget`: the place to boot from, such as `"Pxe"`, `"UefiHttp"`, `"Hdd"`, `"Cd"`, `"BiosSetup"`, `"UefiTarget"` or `"None"`.
3. `BootSourceOverrideMode`: `"UEFI"` or `"Legacy"`.
</details>

<details>
<summary>11. Name six `ChassisType` enumeration values used in AI data centers (DSP2046 `Chassis`).</summary>

`RackMount` (a standard 1U to 8U server), `Blade`, `Enclosure`, `Sled`, `Rack`, `ImmersionTank`, `HeatExchanger` (a CDU or rear-door unit), `Shelf` (a power shelf) and `PowerStrip` (a rack PDU). Any six of these answer the question.
</details>

<details>
<summary>12. Which four modern `Chassis` properties expose thermal, power, and sensor data, and which two older `Chassis` properties did they deprecate?</summary>

The modern properties are `Sensors`, `ThermalSubsystem`, `PowerSubsystem` and `EnvironmentMetrics`. They replaced the deprecated `Power` and `Thermal` resources, so use the modern four when you read a tree.
</details>

<details>
<summary>13. How does Redfish represent physical nesting when a rack enclosure contains four server blades or a host chassis contains a GPU expansion tray?</summary>

It uses bidirectional links inside `Chassis.Links`. The outer enclosure lists its child chassis in `Links.Contains`. Each child chassis points back to its parent enclosure through `Links.ContainedBy`.
</details>

<details>
<summary>14. What are the six standard `ManagerType` values on a `Manager` resource?</summary>

They are `BMC`, `EnclosureManager`, `RackManager`, `ManagementController`, `AuxiliaryController` and `Service`.
</details>

<details>
<summary>15. What does `/redfish/v1/Managers/<id>/NetworkProtocol` contain, and why is it central to BMC security hardening?</summary>

It lists every network management protocol the BMC supports: `HTTPS`, `HTTP`, `SSH`, `IPMI`, `SNMP`, `SSDP`, `Telnet`, `KVMIP`, `VirtualMedia` and `NTP`. For each one it shows whether it is enabled (`ProtocolEnabled`) and which port it uses. This is where you turn off legacy protocols. You can `PATCH` `IPMI`, `Telnet`, `HTTP` and `SSDP` to `false` (chapter 7.15).
</details>

<details>
<summary>16. What is the Redfish equivalent of `ipmitool mc reset cold`, and what rule must the BMC follow when responding to it?</summary>

It is the `#Manager.Reset` action, called at `/redfish/v1/Managers/<id>/Actions/Manager.Reset` with `ResetType` set to `"GracefulRestart"` or `"ForceRestart"`. If the resetting manager also hosts the Redfish web service, it must send the HTTP `200 OK` response before it reboots its network stack. Otherwise the client fails with a connection timeout.
</details>

<details>
<summary>17. What are the three `ResetType` values supported by `#Manager.ResetToDefaults`, and why is `PreserveNetworkAndUsers` useful in remote data centers?</summary>

The three values are `ResetAll`, `PreserveNetworkAndUsers` and `PreserveNetwork`. `PreserveNetworkAndUsers` resets a corrupt BMC configuration to factory defaults. It keeps the BMC's out-of-band IP address and administrator credentials, so you do not lose remote access.
</details>

<details>
<summary>18. Under DSP0266 §9.11, how does Redfish represent an empty DIMM socket or empty drive bay, and how must inventory scripts count installed hardware?</summary>

An empty slot is a resource whose `Status.State` is `"Absent"`, and its unknown properties are set to `null`. Inventory scripts should filter for `Status.State != "Absent"`, such as `"Enabled"` or `"StandbyOffline"`. Counting `Members@odata.count` alone gives the wrong answer.
</details>

<details>
<summary>19. Which four pairs of reciprocal `Links` does `code/part07/rf_model.py` verify across `Systems`, `Chassis`, and `Managers`?</summary>

1. `ComputerSystem.Links.Chassis` ↔ `Chassis.Links.ComputerSystems`
2. `ComputerSystem.Links.ManagedBy` ↔ `Manager.Links.ManagerForServers`
3. `Chassis.Links.ManagedBy` ↔ `Manager.Links.ManagerForChassis`
4. `Chassis.Links.Contains` ↔ `Chassis.Links.ContainedBy`
</details>

<details>
<summary>20. On an NVIDIA DGX H100/H200 vs a GB300 system in BCM, how do the `Systems` and `Chassis` member names illustrate the need for dynamic link discovery?</summary>

On a DGX H100 or H200, the host and the GPU baseboard appear as `Systems/DGX` and `Systems/HGX_Baseboard_0`. The chassis is `Chassis/DGX`, and the manager is `Managers/BMC`. BCM's GB300 examples use different names, such as `BMC_0`, `CBC_0` and `Chassis_0`. Walking from `/redfish/v1/` and reading `SystemType`, `ProcessorType` and `Links` works across every generation, so you never need hard-coded names.
</details>

## Sources and review notes

- **Redfish Resource and Schema Guide DSP2046 (2024.4), and the official JSON Schemas** (`ComputerSystem` v1.23.1, `Chassis` v1.26.0, `Manager` v1.20.0 and later, `Processor` v1.20.1, `ManagerNetworkProtocol` v1.10.1, `Resource`): property descriptions, enumerations (`SystemType`, `ChassisType`, `ManagerType`, `ProcessorType`, `State`, `Health`, `ResetType`) and the Manager actions.
- **Redfish Specification DSP0266 v1.21.0:** absent and transiently unavailable resources (9.11), resource tree stability and discovery (12.3, 12.4).
- **DMTF example trees** from `github.com/DMTF/Redfish-Publications` (commit `fa6d23d9`): rack server, blade enclosure, SmartNIC, PDU, power shelf, cooling unit, liquid-cooled server.
- **BCM 11 Administrator Manual**, appendix N: device naming on GB300 hardware.
- **NVIDIA-DevOps notes (volume 05 chapter 3, volume 10 chapter 1):** DGX system, chassis and manager names, `HGX_Baseboard_0`, the dual-tray description. Not verified.
- **Run here:** `rf_model.py` (8 services), `rf_inventory.py` (4 services), `schema_lab.py` (still 11 passes as the mock grew to 110 resources).
- **Not verified:** how a real DGX, HGX or GB200 tree looks, which of the optional links the BMC fills in, and whether its `Contains` links are complete. Part 9 and chapter 7.13 revisit this.
