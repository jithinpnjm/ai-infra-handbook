---
id: "c07-09"
title: "7.9 Storage, network adapters and PCIe devices"
sidebar_label: "7.9 Storage, network adapters and PCIe devices"
sidebar_position: 9
description: "How Redfish describes drives and volumes, network adapters and ports, and PCIe devices, and how to find the silent problems that cost AI performance: PCIe links trained down, ports running slower than their cable, and failing drives, with a tool and a 15-check lab"
status: "drafted"
tier: "1b"
level: "I"
lab_venue: "GCP / GKE"
---

# 7.9 Storage, network adapters and PCIe devices

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted (`hardware_lab.py`: 15 checks pass against mock and DMTF trees; **untested** on live BMC) |

## Why this matters for AI infrastructure

Suppose a GPU's PCIe link has trained down to a quarter of its full speed. Nothing crashes, and no alert fires. The job simply runs slower, or one slow node drags a whole training run behind it. The same thing happens when a network port negotiates 200 Gbps instead of 400, or when a boot drive is about to die. These problems are quiet, and that is what makes them expensive. A cluster team needs a cheap, automatic way to ask every machine whether all of its links run at full speed. The BMC can answer that question through Redfish, even before the operating system is installed.

## Prerequisites and outcomes

Read chapters 7.2 and 7.7 first, because this chapter builds directly on them. When you finish, you should be able to:

- find drives, volumes, network ports and PCIe devices on any Redfish service
- read PCIe speed and width, and spot a link that trained down
- read port state and speed, and spot a port running below its maximum
- read drive health signals
- run a tool that checks all of this and a lab that tests it

## 1. Where the hardware lives

When your script asks for a drive or a network card, it first has to know which branch of the tree to search. You will find hardware under both families from chapter 7.7. The system side shows the **logical** view, and the chassis side shows the **physical** one.

| Hardware | Where | Main resource types |
|---|---|---|
| Drives and volumes | `Systems/<id>/Storage` | `Storage`, `Drive`, `Volume`, `StorageController` |
| Old-style storage | `Systems/<id>/SimpleStorage` | `SimpleStorage` (simple, older) |
| Network adapters | `Chassis/<id>/NetworkAdapters` | `NetworkAdapter`, `Port`, `NetworkDeviceFunction` |
| Host network interfaces | `Systems/<id>/EthernetInterfaces` | `EthernetInterface` |
| PCIe devices | `Chassis/<id>/PCIeDevices` | `PCIeDevice`, `PCIeFunction`, `PCIeSlots` (deprecated) |
| GPUs and CPUs | `Systems/<id>/Processors` | `Processor` (chapter 7.7) |
| Memory | `Systems/<id>/Memory` | `Memory` |
| Fabric adapters | `Chassis/<id>/FabricAdapters` | `FabricAdapter` |

Remember from chapter 7.2 that names, positions and optional parts differ between makers. The DMTF examples show this clearly. Some trees keep storage under `Storage`, others only have `SimpleStorage`, and PCIe devices appear in only some of them. A tool therefore has to find resources by type and skip anything that is missing.

## 2. Storage: drives, volumes, controllers

Start with the drive, because it is the resource you will check most often. Each property answers one question about the disk, such as how big it is, whether it expects to fail, or how fast its link runs. The diagram shows how the storage resources fit together.

```mermaid
flowchart LR
    ST["Storage<br/>a storage subsystem"] --> SC["StorageController<br/>the RAID or NVMe controller"]
    ST --> DR["Drive<br/>one physical drive"]
    ST --> VO["Volume<br/>a logical disk or RAID set"]
    VO -. "built from" .-> DR
```

The `Drive` resource has these properties:

| Property | Meaning |
|---|---|
| `CapacityBytes`, `BlockSizeBytes` | size and the smallest addressable block |
| `MediaType` | `HDD`, `SSD` or `SMR` |
| `Protocol` | how it talks to the controller (`NVMe`, `SATA`, `SAS` and others) |
| `FailurePredicted` | **true** when the drive predicts failure soon |
| `PredictedMediaLifeLeftPercent` | how much of the write/read life is left, as a percentage |
| `CapableSpeedGbs`, `NegotiatedSpeedGbs` | the best link speed it supports, and the one it actually runs at |
| `EncryptionStatus` | encryption state |
| `Revision`, `Model`, `SerialNumber` | identity |
| `Operations` | jobs currently running on it, such as a rebuild |
| `Status` | `State` and `Health` |

A `Volume` is the logical view. It groups drives into a RAID set or a logical disk. Its `RAIDType`, `CapacityBytes`, `VolumeType`, `Encrypted` and read and write cache policy tell you what the volume is. Its `Operations` and `Status` show whether a rebuild or check is running. The `StorageController` describes the card that manages the drives. It lists the RAID types and protocols it supports. It also gives its firmware version, its speed and its own `PCIeInterface`. The standard also defines metrics resources, `DriveMetrics` and `StorageControllerMetrics`. They expose usage counters and NVMe SMART warnings such as `SpareCapacityWornOut` and `MediaInReadOnly`.

For an AI node, the boot and scratch NVMe drives matter less than shared storage, but they still count. A dead scratch drive stops a job, and local NVMe is the cache for datasets. Watch `FailurePredicted` and the remaining life of every drive, because those two signals warn you before a drive gives out.

## 3. Network: adapters, ports and functions

A network card can look healthy from the outside and still run slowly. Redfish splits the card into several resources, and you need all of them to see the whole picture. The table shows what each one is.

| Resource | What it is |
|---|---|
| `NetworkAdapter` | one physical card (for example a 400G NIC): model, serial number, firmware, `Controllers` (the chips on it), links to `Ports` and `NetworkDeviceFunctions` |
| `Port` | one connector: protocol, state, speed, width |
| `NetworkDeviceFunction` | a logical interface the card exposes: type (Ethernet, InfiniBand and so on), MAC address, SR-IOV virtual functions, which physical port it uses |
| `EthernetInterface` | an interface as the OS or BMC sees it: IP addresses, VLAN, DHCP |

The `Port` resource carries the fields you will read most often. The table lists them.

| Property | Meaning |
|---|---|
| `LinkState` | the **desired** state: `Enabled` or `Disabled` |
| `LinkStatus` | the **actual** state: `LinkUp`, `LinkDown`, `NoLink`, `Starting`, `Training` |
| `CurrentSpeedGbps` | the speed right now |
| `MaxSpeedGbps` | the maximum speed as currently configured |
| `ActiveWidth`, `Width` | active lanes and total lanes |
| `PortProtocol`, `LinkNetworkTechnology` | `Ethernet`, `InfiniBand`, `FibreChannel`, `GenZ`, `PCIe` |
| `SignalDetected` | is any signal seen on the link |
| `Metrics` | link to port counters (`PortMetrics`) |

Read `LinkState` and `LinkStatus` together. A port that is `Disabled` and `LinkDown` is fine, because someone turned it off on purpose. A port that is `Enabled` and `LinkDown` is a real problem. A port that shows `LinkUp` while `CurrentSpeedGbps` sits below `MaxSpeedGbps` still works, but it is slow. The usual causes are a bad cable, a bad optic or a negotiation problem.

DPUs and SmartNICs are also computers. They have their own `ComputerSystem` of type `DPU`, which chapter 7.7 covers. BlueField DPUs in DGX systems are one example from the notes this chapter draws on.

## 4. PCIe: the hidden speed limit

Every GPU, NIC and NVMe drive connects through PCI Express, and that link sets how much data can reach the device. Suppose a device built for Gen5 x16 has trained down to Gen3 x8. It now has a fraction of its bandwidth, and nothing says so unless you look. A PCIe link has a speed, which is the generation (Gen3, Gen4, Gen5), and a width, which is the number of lanes (x1, x4, x8, x16). Bandwidth is roughly the product of the two.

Here is the arithmetic. Gen5 gives 32 GT/s on each of 16 lanes, which is about 64 GB/s. Gen3 gives 8 GT/s on each of 8 lanes, which is about 8 GB/s. The degraded link keeps only about one-eighth of the original bandwidth. This can happen with a bad cable or riser, dust, a loose card, a BIOS setting, or power problems.

The `PCIeDevice` resource has a `PCIeInterface` block with exactly the numbers you need. The table lists its fields.

| Property | Meaning |
|---|---|
| `PCIeType` | the PCIe version **in use** now (`Gen1` to `Gen6`) |
| `MaxPCIeType` | the highest version this device supports |
| `LanesInUse` | lanes in use now |
| `MaxLanes` | lanes the device supports |

If `PCIeType` is lower than `MaxPCIeType`, or `LanesInUse` is lower than `MaxLanes`, the link is **degraded**. The same information appears in the `LnkCap` and `LnkSta` lines of `lspci -vv` on Linux. Redfish gives it to you without logging in. The same block also appears on `NetworkAdapter` controllers, on `StorageController` and on other resources. A `PCIeDevice` carries more: its `DeviceType` (`SingleFunction`, `MultiFunction`, `Simulated` or `Retimer`), its firmware version, its `Slot` information, and links to its `PCIeFunctions`.

The field notes this chapter draws on describe the same failure: a PCIe link running at Gen1 instead of Gen5. In a 512-node cluster, that link caused silent slowness. A related case involves links that fall back to Gen3 x8. The same notes recommend forcing the BIOS link speed instead of leaving it on `Auto`, a setting chapter 7.14 covers. Check the link speed and width of every GPU and NIC before you trust a node, because a degraded link gives no error.

## 5. The tool: find the degraded things

Checking each device by hand does not scale. A script can walk the Redfish tree, look at each resource and apply a few simple rules. That is the job of `code/part07/rf_hardware.py`. It walks the `Systems` and `Chassis` trees by following links, and it skips logs, sensors and certificates to save time. It looks at each resource by `@odata.type`, then applies the rules in the table.

| Group | Flag when |
|---|---|
| PCIe | `LanesInUse` below `MaxLanes`, or `PCIeType` older than `MaxPCIeType`, or health not OK |
| Ports | enabled but not `LinkUp`; or `CurrentSpeedGbps` below `MaxSpeedGbps`; or `ActiveWidth` below `Width`; or health not OK |
| Drives | `FailurePredicted`; life left under 10 percent; `NegotiatedSpeedGbs` below `CapableSpeedGbs`; health not OK |
| Volumes | health not OK |

The rules are simple, so you can check every flag by hand. The tool also warns when a resource's own `@odata.id` differs from the address it was fetched from. That can mean a broken tree or a copy-paste error in the service. The mock used for testing has 8 GPUs and 8 NICs, all on Gen5 x16, plus two NVMe drives. Here is the output of a real run against it.

```text
walked 60 resources
PCIe interfaces: 16   ports: 8   drives: 2   volumes: 0   storage subsystems: 1

0 flagged
```

Next is the DMTF tower-server example.

```text
walked 404 resources
PCIe interfaces: 10   ports: 18   drives: 18   volumes: 5   storage subsystems: 9
  PCIe   Chassis/Tower/NetworkAdapters/NIC1#controller    Gen2 x2 (max Gen3 x4)  link width x2 of x4; PCIe Gen2 of Gen3
  PCIe   Chassis/Tower/PCIeDevices/IntegratedNIC          Gen2 x4 (max Gen3 x4)  PCIe Gen2 of Gen3
  PCIe   Chassis/Tower/PCIeDevices/Slot4                  Gen2 x2 (max Gen3 x4)  link width x2 of x4; PCIe Gen2 of Gen3
  PCIe   Chassis/Tower/PCIeDevices/Slot3                  Gen2 x2 (max Gen3 x4)  link width x2 of x4; PCIe Gen2 of Gen3
4 flagged
```

All four flags are PCIe links that run below their maximum. Three of them also have a narrow width, x2 instead of x4. On the DMTF accelerator-card example, the tool flags two controllers running at Gen3 where Gen4 is possible. It also flags a port running at 25 of 50 Gbps. The SmartNIC example shows the same 25 of 50 Gbps port. Keep in mind that these DMTF trees are sample data. Their values may be varied on purpose to show the schema, so use them only as test material for the tool.

The SmartNIC example also triggers the `@odata.id` warning. Two ports under `Chassis/Card2/...` report an `@odata.id` that points at the `Card1` address. In DMTF's sample, this looks like a copy-and-paste error. Real BMCs can have bugs like this too. A script that trusts the ID inside the body, instead of the address it fetched, will mix up the two ports.

### The lab

Run the lab from the chapter's code folder.

```bash
cd code/part07
python3 hardware_lab.py
```

The lab runs 15 checks against the mock and against two DMTF trees. For the mock, it creates one fault at a time and confirms that the tool catches each one. Each line below is one check. When you see PASS, the tool caught the fault it was built to catch, and when you see a flag in real output, the rule that fired is in the table above.

```text
PASS  a GPU trained down to Gen3 x8 is flagged for both speed and width
PASS  only that one device is flagged
PASS  an enabled port that is LinkDown is flagged
PASS  a port that is administratively Disabled is not flagged
PASS  a 400G port running at 200G is flagged (cable or optics or negotiation)
PASS  a port with 2 of 4 lanes active is flagged
PASS  a drive predicting failure is flagged
PASS  a drive with 5 percent life left is flagged
PASS  a drive linked at 8 of 32 Gbps is flagged
PASS  a PCIe device with Health Warning is flagged
PASS  DMTF tower example: 4 PCIe devices run below their maximum link
...
15 passed, 0 failed
```

Use the lab across the fleet. Run the tool against every BMC after racking and after each maintenance window. A GPU node with one degraded link should stay out of the scheduler until that link is fixed. For depth, pair the tool with the host-side checks in Part 10, such as NVLink, `nvidia-smi` and DCGM. Make a clean run the condition for putting any node back into service.

## 6. What Redfish does not tell you

Suppose a node passes every Redfish check and still runs slowly. Redfish is a cheap first check, not the final word. It has blind spots, and you need to know them before you trust a clean result.

Redfish does not show how fast data actually moves. A link can run at full width and still be slow, because of congestion or a software setting. The speed and width it reports are the values the BMC reads. Some BMCs cannot see every device, since they only see what is wired to them or what the vendor mapped. A device missing from the list is therefore not proof that the device is absent.

GPU details such as NVLink counters, ECC counts and clock throttling usually come from the GPU driver, not from the standard schema. Vendors may add them as OEM data, which chapter 7.13 covers. Drive health from the BMC is only as good as the drive's own reporting.

So use Redfish for the cheap first check, and for machines whose operating system is not running. Once that check is done, move to the host tools for depth.

### 6.1 Anatomy of a silent PCIe link downgrade in distributed training

Why is `code/part07/rf_hardware.py` one of the most useful tools in this part of the handbook? The answer becomes clear when you follow one degraded PCIe link through a 64-node training cluster with 512 GPUs, step by step.

On an 8-GPU training server, each SXM GPU talks to its paired 400 Gbps ConnectX-7 network adapter over a dedicated PCIe Gen5 x16 link. At Gen5, each lane runs at 32 GT/s, and the link has 16 lanes. That gives a raw one-way bandwidth of 64 GB/s. The link has room to spare above the 50 GB/s line rate of a 400G InfiniBand or RoCEv2 port. During the backward pass of a large language model, GPUDirect RDMA streams gradient tensors straight out of GPU HBM memory. The data passes through the PCIe switch or retimer, into the ConnectX-7 HCA, which is the host channel adapter, and out onto the rail-aligned leaf switch at full line rate.

Now suppose a technician replaces a fan tray on `node042`. Slight vibration unseats a high-density PCIe riser cable by a fraction of a millimeter. Or a PCIe Gen5 retimer chip overheats during boot link training. The link-training logic, called the LTSSM, does not fail the boot or cause a kernel panic. PCIe is built to be resilient, so it negotiates down to the highest speed and lane width that still give a clean signal lock. If eight of the sixteen differential pairs have high bit-error rates at 32 GT/s, the link silently trains up at PCIe Gen3 x8. That is 8 GT/s across 8 lanes, or about 8 GB/s of one-way bandwidth.

The arithmetic is worth doing once. Gen5 x16 gave 64 GB/s, and Gen3 x8 gives about 8 GB/s. That is about one-eighth of the original bandwidth. Now look at what this looks like when `node042` rejoins the Slurm pool:

- The Linux OS boots cleanly.
- All eight GPUs appear healthy in `nvidia-smi` with `0` ECC errors.
- All eight `400G` InfiniBand ports show `State: Active` and `Rate: 400 Gb/sec` in `ibstat`. That is because the optical link between the NIC and the leaf switch is still `400G`.

Yet when a 64-node training job lands on `node042`, GPU 3 can push gradients to its `400G` NIC at only 8 GB/s, not 50 GB/s. That is 16 percent of the rated rate. Ring and tree `AllReduce` collectives make every GPU wait for the others at each micro-batch step. So **a single PCIe link running at `Gen3 x8` on one GPU throttles the effective network throughput of all 512 GPUs by more than 80%**.

Run `rf_hardware.py` against the BMC, and it catches this fault in two seconds, before the node ever enters Slurm. The script compares `PCIeInterface.PCIeType` (`"Gen3"`) against `MaxPCIeType` (`"Gen5"`). It also compares `LanesInUse` (`8`) against `MaxLanes` (`16`). It then flags the exact `PCIeDevice` URI and blocks the node at the acceptance gate.

### 6.2 Diagnosing optical and copper `Port` speed mismatches

The second silent problem in AI fabrics is a high-speed port that links up, but at a fraction of its rated speed or lane width. You will find these ports under `NetworkAdapter/Ports`. Modern 400 Gbps and 800 Gbps InfiniBand and Ethernet links are built from parallel lanes. Each lane is a SerDes circuit, which converts data to and from a serial signal. A typical link uses 4 lanes of 100 Gbps PAM4 signaling, or 8 lanes of 100 Gbps.

When you inspect a `Port` through Redfish, four properties tell the physical-layer story. Read them in this order.

1. **`LinkState` and `LinkStatus`:** If `LinkState` is `Enabled` and `LinkStatus` is `LinkDown` or `NoLink`, check `SignalDetected` next. When `SignalDetected` is `false`, no light reaches the receive fibers. Look for an unplugged cable, swapped TX and RX polarity, or a powered-off leaf switch port. When `SignalDetected` is `true` but `LinkStatus` stays at `Training` or `LinkDown`, the transceivers see light but cannot lock FEC or auto-negotiation. That often means a mismatched port protocol, such as InfiniBand against Ethernet mode set in `mlxconfig`, or an incompatible FEC setting on the switch.
2. **`CurrentSpeedGbps` versus `MaxSpeedGbps`:** If a `400G` port shows `LinkUp` with `CurrentSpeedGbps: 200` and `MaxSpeedGbps: 400`, the link negotiated down to half its speed.
3. **`ActiveWidth` versus `Width`:** Compare `ActiveWidth` (`2`) with `Width` (`4`), and you can see why `CurrentSpeedGbps` dropped. Two of the four optical lanes, inside the OSFP or QSFP-DD transceiver or the MTP fiber trunk, are dead or dirty. Cleaning the optical connector with a single-click fiber cleaner, or swapping the transceiver, restores all `4` lanes. That brings `CurrentSpeedGbps` back to `400`.
4. **`PortMetrics` (through the `Metrics` link):** Follow the `Metrics` link on a `Port` to reach the hardware counters. They cover RX and TX bytes, frame errors, symbol errors and optical power per lane, in `RXInputPowerMilliWatts` and `TXOutputPowerMilliWatts`. With these counters you can spot a fading laser diode before the lane drops out completely.

### 6.3 Proactive NVMe and boot drive lifecycle management

A local NVMe drive that fails in the middle of a job can crash a training run. Training checkpoints and datasets usually live on high-speed parallel filesystems such as Lustre, WekaFS and GPFS. Each GPU node still relies on local NVMe drives for two jobs, though. One is booting the local OS, unless the node runs diskless. The other is providing multi-terabyte local NVMe scratch or cache storage, such as `/lscratch` or GDS P2PDMA staging.

When a local NVMe drive fails in the middle of a job, the Linux kernel can do one of two things. It can remount the scratch filesystem read-only, or it can hang I/O worker threads in uninterruptible sleep, the `D` state. Either way, the training run crashes. The Redfish `Storage` and `Drive` model gives you four early signals. You find it under `/redfish/v1/Systems/{id}/Storage`, and also under `/redfish/v1/Chassis/{id}/Drives`. Use these signals to replace aging SSDs in a scheduled maintenance window, rather than in the middle of a job.

- **`FailurePredicted: true`** means the drive's internal SMART controller has crossed a pre-fail threshold, such as uncorrectable media errors or depleted spare blocks. Drain the node after the current job finishes, and schedule a drive swap.
- **`PredictedMediaLifeLeftPercent`** reports how much of the rated program and erase endurance, or P/E endurance, remains. A new drive shows `100`, and the value counts down toward `0`. On nodes that cache datasets heavily, an alert below `10%` helps prevent a surprise wear-out failure.
- **`NegotiatedSpeedGbs` versus `CapableSpeedGbs`** matters because U.2, U.3 and E3.S NVMe drives, like GPUs and NICs, connect over PCIe lanes. Suppose a drive capable of `32 Gbps`, which is PCIe Gen5, negotiates at `8 Gbps`, which is Gen3, because of a backplane fault. Local checkpoint staging then slows by $4\times$, which is 32 divided by 8.
- **`Volume.Operations`** matters on nodes that mirror their boot drives with a hardware RAID controller, or `StorageController`. Check `Status.Health` and `Operations` on the `Volume`. They show whether the mirror is degraded, or whether a background `"Rebuild"` is running.

Put these four signals into your alerting, and schedule a drive swap before a failure reaches a running job.

### 6.4 Integrating `rf_hardware.py` into Day-0 and Day-2 automation

Checks only help when they run every time. Wire `code/part07/rf_hardware.py` into three gates, so that every node in your cluster gets the same check across its life.

1. **Pre-OS Day-0 racking gate:** Right after the team that racks and cables the machines plugs in power and network cables, run `rf_hardware.py` against all BMC IPs from the head node. The script works entirely out of band over Redfish. So you get a full punch list of unseated PCIe risers, dark `400G` ports and missing NVMe drives. You get it before you configure DHCP or PXE for the host OS.
2. **Post-maintenance return-to-service gate:** After any board swap or firmware upgrade, do not run `scontrol update NodeName=<node> State=RESUME` or `kubectl uncordon` until `rf_hardware.py` exits `0` and reports `0 flagged`.
3. **Weekly fleet baseline diff:** Once a week, run `rf_hardware.py` across all nodes with `fleet_run.py`. Then compare the counts of `PCIeDevices`, `Ports` and `Drives` with your saved Day-1 JSON inventory. A device that vanishes from the PCIe bus also disappears from the BMC's `PCIeDevices` list, so the count mismatch catches it.

Start with the racking gate, since it runs before any OS work begins.

### 6.5 Correlating Redfish PCIe and NIC inventory with Linux `lspci`, `ethtool`, and `mlx5`

Redfish gives you an agentless, out-of-band view of every `PCIeDevice`, `NetworkAdapter` and `Drive`. In production, though, troubleshooting goes fastest when you know which Linux command matches each Redfish property, once the host OS has booted. The table gives that mapping.

| Subsystem & Check | Out-of-Band Redfish Property (`rf_hardware.py`) | In-Band Linux Command & Equivalent Field |
|---|---|---|
| **PCIe Link Speed & Width** | `PCIeDevice.PCIeInterface`: `PCIeType` vs `MaxPCIeType` (`Gen5`), `LanesInUse` vs `MaxLanes` (`16`) | `sudo lspci -vvv -s <bdf>` $\rightarrow$ `LnkSta: Speed 32GT/s, Width x16` vs `LnkCap: Speed 32GT/s, Width x16` |
| **PCIe Bus Errors** | `Status.Health` (`Warning`/`Critical`) and BMC `LogServices` AER entries | `dmesg -T \| grep -iE "aer\|pcieport"` and `/sys/bus/pci/devices/<bdf>/aer_dev_*` |
| **Network Port State & Speed** | `Port`: `LinkState` (`Enabled`), `LinkStatus` (`LinkUp`), `CurrentSpeedGbps` vs `MaxSpeedGbps` (`400`) | `ibstat` (`State: Active`, `Physical state: LinkUp`, `Rate: 400`) or `ethtool <iface>` (`Speed: 400000Mb/s`, `Link detected: yes`) |
| **Optical Lane Width & Power** | `Port`: `ActiveWidth` vs `Width` (`4`), `PortMetrics` RX/TX optical power (`mW`) | `mlxlink -d mlx5_0 -m` or `ethtool -m <iface>` (per-lane RX/TX dBm and bias current) |
| **NVMe Drive Health & Speed** | `Drive`: `FailurePredicted`, `PredictedMediaLifeLeftPercent`, `NegotiatedSpeedGbs` vs `CapableSpeedGbs` | `sudo nvme smart-log /dev/nvme0n1` (`critical_warning`, `percentage_used`) and `lspci -vvv` on the NVMe BDF |

Why keep both views? Each one catches failures the other misses. When a PCIe switch or GPU falls completely off the bus during a hard lockup, the host kernel panics, and `lspci` or `mlxlink` become unreachable. The BMC's out-of-band `PCIeDevices` and `Ports` tree is still queryable over Redfish, though. The opposite case happens too. A link can come up at full Gen5 x16 and 400 Gbps at boot, so Redfish reports `OK`. Then intermittent bit errors cause thousands of link-level PCIe replay events or RDMA symbol errors under heavy DMA load. In-band `nvidia-smi nvlink -e`, `mlxlink` and `perfquery` deltas expose that signal-integrity problem before the link ever drops its width.

### 6.6 Handling OEM topology quirks and `FabricAdapters`

Run `rf_hardware.py` across different server vendors and DMTF mockup trees, such as `public-tower`, `public-smartnic`, `public-nvmeof-jbof` and `public-localstorage`, and the tree changes shape. Every portable Redfish hardware scanner has to handle three structural variations gracefully.

1. **Where `PCIeInterface` sits:** On newer Redfish implementations, `PCIeInterface` lives directly on each `PCIeDevice`, under `/redfish/v1/Chassis/{id}/PCIeDevices/{dev}`. Its fields are `PCIeType`, `MaxPCIeType`, `LanesInUse` and `MaxLanes`. On older implementations, and on integrated network and storage cards, the block sits inside the `Controllers[]` array of a `NetworkAdapter`, or inside a `StorageController`. That is why `rf_hardware.py` checks `@odata.type` across all three resource types. It does not look only in `PCIeDevices`.
2. **Ports under `NetworkAdapter` or under `FabricAdapters`:** Standard Ethernet and InfiniBand NICs show their ports under `Chassis/{id}/NetworkAdapters/{nic}/Ports`. Switches, NVLink fabric boards, CXL enclosures and JBOF storage fabrics often differ. They expose ports under `Chassis/{id}/FabricAdapters/{fa}/Ports`, or at the top level under `/redfish/v1/Fabrics/{fabric}/Switches/{sw}/Ports`. The script walks every `@odata.id` link from `Systems` and `Chassis`, and it matches resources by `@odata.type == "Port"`, not by URL path. So it checks link state and speed no matter which parent collection holds the `Port`.
3. **Cross-card `@odata.id` aliasing bugs:** The DMTF `public-smartnic` mockup shows the problem. Two ports fetched under `Chassis/Card2/...` returned `"@odata.id": "/redfish/v1/Chassis/Card1/..."` in their JSON bodies. Real BMC firmware sometimes has templating bugs like this when a server holds several identical adapter cards. Key your inventory and fault reports by the actual URI you fetched. Also log a warning when `res.get("@odata.id")` disagrees with the request URI. That way, a firmware copy-paste bug on Card 2 cannot overwrite the status of Card 1 in your database.

Build the scanner to trust the address it fetched, not the ID inside the body.

## Exercises

Work through these six tasks in order. The first one uses the lab you already ran, and the rest build on the same tools and mock trees.

1. Start with the 15-check suite in `code/part07/hardware_lab.py`. Run `python3 code/part07/hardware_lab.py` and confirm that `12` / `15` checks pass. Then open `code/part07/rf_hardware.py` and read it. Explain why a GPU with `PCIeType: "Gen3"`, `MaxPCIeType: "Gen5"`, `LanesInUse: 8` and `MaxLanes: 16` is flagged for both speed and width degradation.
2. Audit the NVMe and SAS drives in the `public-localstorage` mockup. Serve `$REDFISH_PUBLICATIONS/mockups/public-localstorage` with `redfish_mock.py --mockup`, then run `python3 code/part07/rf_hardware.py http://127.0.0.1:8443 admin adminpass --all`. Write down each drive the script finds, with its `Protocol`, `MediaType`, `CapacityBytes`, `FailurePredicted` and `PredictedMediaLifeLeftPercent`.
3. Extend `code/part07/rf_hardware.py` so that it notices an active RAID rebuild. Any `Volume` whose `Operations` array is not empty should produce a warning during pre-job health checks. An entry such as `"OperationName": "Rebuild"` with `"PercentageComplete": 42` is the case to catch.
4. Triage a link that drops from Gen5 to Gen4 or Gen3. A GPU on `node019` reports `PCIeType: "Gen4"` while `MaxPCIeType` is `"Gen5"`. Name three physical or firmware causes, such as riser or retimer signal integrity, BIOS PCIe speed left on `Auto` instead of `Gen5`, or thermal and power state. Then list the host-side commands, `lspci -vvv` and `dmesg | grep -i aer`, that you would run to match what Redfish shows.
5. A 400G port can negotiate at 100G or 200G, so you need to find out why. Here is a `NetworkAdapter` `Port` that reports `LinkState: "Enabled"`, `LinkStatus: "LinkUp"`, `CurrentSpeedGbps: 200`, `MaxSpeedGbps: 400`, `ActiveWidth: 2` and `Width: 4`. Explain what `ActiveWidth: 2` of `4` tells you about the optical transceiver or DAC cable lanes.
6. Explain why `rf_hardware.py` flags `{LinkState: "Enabled", LinkStatus: "LinkDown"}` as an error, yet treats `{LinkState: "Disabled", LinkStatus: "LinkDown"}` as healthy. Then explain why an `@odata.id` mismatch, such as the `Card2` port in `public-smartnic` that claims a `Card1` `@odata.id`, must still be logged.

## 8. Interview angles

- "A node is slower than its twins and DCGM looks fine. What do you check?" Start with the PCIe link speed and width on each GPU and NIC. Then look at port speeds, thermal state and power, and compare everything with a healthy node.
- "How do you check hardware health before a node joins the cluster?" Run a Redfish sweep first. It looks for degraded links, firmware problems, health status and drive state. Then run host tests for the GPU and the network.
- "What is the difference between `LinkState` and `LinkStatus`?" `LinkState` is what you asked the port to do. `LinkStatus` is what the link is actually doing.
- "Why is a degraded PCIe link dangerous even when nothing errors?" It silently cuts bandwidth, and nothing reports it as a failure. Training synchronises on the slowest member, so one slow link slows the whole job.

## Checkpoint questions (20)

<details>
<summary>1. Under which Redfish top-level collections do `Storage` (`Drive`, `Volume`) versus `NetworkAdapters` and `PCIeDevices` typically reside?</summary>

`Storage`, with its `Drive` and `Volume` resources, sits under **`Systems/{id}/Storage`**. Physical drive slots also show up under `Chassis/{id}/Drives`. If you are looking for a NIC or a PCIe device, go to **`Chassis/{id}`**. There you find `NetworkAdapters`, with their `Port` and `NetworkDeviceFunction` resources, and `PCIeDevices`, with `PCIeFunction`. `FabricAdapters` also sit under `Chassis`.
</details>

<details>
<summary>2. What is the difference between `Storage` and `SimpleStorage` on a `ComputerSystem`?</summary>

`Storage` is the modern, full-featured model. It gives you separate `StorageController`, `Drive` and `Volume` resources, with RAID actions, NVMe metrics and PCIe link details. `SimpleStorage` is the older option. It is a flat summary that lists basic device names and capacities in an array, and it suits simple SATA and USB controllers.
</details>

<details>
<summary>3. Name four properties on a `Drive` resource that provide early warning of a failing or degraded disk.</summary>

1. **`FailurePredicted`** is `true` when SMART or telemetry predicts a failure soon.
2. **`PredictedMediaLifeLeftPercent`** shows the remaining write endurance. A value such as `< 10%` is a warning sign.
3. **`NegotiatedSpeedGbs` versus `CapableSpeedGbs`** shows a link that trained slower than the drive can run.
4. **`Status.Health`** reads `Warning` or `Critical`.
</details>

<details>
<summary>4. What does it mean when a `Drive` reports `NegotiatedSpeedGbs: 8` and `CapableSpeedGbs: 32`?</summary>

The drive and backplane can run at `32 Gb/s`, which is PCIe Gen5 NVMe or SAS-4. The link, however, negotiated down to `8 Gb/s`, which is PCIe Gen3. That cuts sequential I/O bandwidth to a quarter of the rated speed.
</details>

<details>
<summary>5. What is a `Volume` resource under `Storage`, and what does its `Operations` array indicate?</summary>

A `Volume` is a logical disk, namespace or RAID array built from one or more physical `Drive` resources. Its fields include `RAIDType`, `CapacityBytes` and `Encrypted`. The `Operations` array lists the background tasks running on the volume right now, such as a RAID rebuild or consistency check, along with each task's `PercentageComplete`.
</details>

<details>
<summary>6. How do `NetworkAdapter`, `Port`, `NetworkDeviceFunction`, and `EthernetInterface` relate to one another?</summary>

- `NetworkAdapter` lives under `Chassis`. It is the physical NIC or HCA board, such as a ConnectX-7, with its ASICs (listed as `Controllers`), serial number and PCIe interface.
- `Port` sits under `NetworkAdapter/Ports`. It is the physical cage or connector, such as `OSFP` or `QSFP`, and it reports the optical link status, lane width and speed, such as `400 Gbps`.
- `NetworkDeviceFunction` sits under `NetworkAdapter/NetworkDeviceFunctions`. It is the logical function configured on the adapter, such as `Ethernet` or `InfiniBand`, with its MAC or WWN and SR-IOV virtual functions.
- `EthernetInterface` sits under `Systems/{id}/EthernetInterfaces`. It is the interface the OS sees, with its IPv4 and IPv6 addresses, MTU and VLANs.
</details>

<details>
<summary>7. On a `Port` resource, what is the difference between `LinkState` and `LinkStatus`?</summary>

- `LinkState` is the administrative, or desired, state of the port. It is either `Enabled` or `Disabled`.
- `LinkStatus` is the operational, or actual, state of the physical link. It can read `LinkUp`, `LinkDown`, `NoLink`, `Starting` or `Training`.
</details>

<details>
<summary>8. What does it indicate when an enabled `Port` is `LinkUp` but `CurrentSpeedGbps` (`200`) is lower than `MaxSpeedGbps` (`400`)?</summary>

The port could not auto-negotiate its full line rate. The usual causes are a damaged DAC or AOC cable, a dirty optical ferrule, a mismatched speed or FEC setting on the switch port, or a dead lane, which shows up as `ActiveWidth` below `Width`.
</details>

<details>
<summary>9. What do `ActiveWidth` and `Width` represent on a high-speed network `Port`?</summary>

`Width` is the total number of electrical or optical SerDes lanes in the port. A 400G port, for example, has 4 lanes of 100G PAM4. `ActiveWidth` is how many of those lanes actually trained up. If `ActiveWidth` is `2` of `4`, half the lanes are dead, and the port runs at half speed, or `200G`.
</details>

<details>
<summary>10. What two physical parameters determine the bandwidth of a PCIe link?</summary>

Two parameters set the bandwidth. The first is the generation, shown as `PCIeType`, which sets the transfer rate per lane. Gen3 runs at 8 GT/s per lane, Gen4 at 16 GT/s, Gen5 at 32 GT/s and Gen6 at 64 GT/s. The second is the width, `LanesInUse`, which counts the active lane pairs, such as `x1`, `x2`, `x4`, `x8` or `x16`. Multiply the per-lane rate by the lane count. A Gen5 x16 link gives about 64 GB/s.
</details>

<details>
<summary>11. Which four properties inside the `PCIeInterface` object of a `PCIeDevice` let you detect a downgraded link without logging into the host OS?</summary>

`PCIeType` shows the speed the link runs at now. `MaxPCIeType` shows the fastest speed the device supports. `LanesInUse` shows the width the link uses now, and `MaxLanes` shows the most lanes the device supports. A gap between the current value and the maximum means the link is degraded.
</details>

<details>
<summary>12. State the exact boolean condition that `code/part07/rf_hardware.py` uses to flag a degraded PCIe link.</summary>

The script flags a PCIe interface when any of three conditions is true. First, `LanesInUse < MaxLanes` means the width dropped. Second, `GEN_RANK[PCIeType] < GEN_RANK[MaxPCIeType]` means the generation dropped, unless the device sits in a motherboard slot whose capabilities are lower. Third, `Status.Health != "OK"` means the device reports a problem.
</details>

<details>
<summary>13. Give three physical or configuration causes of a GPU or ConnectX HCA training down from PCIe Gen5 x16 to Gen3 x8.</summary>

The first cause is signal integrity: a loose SXM or PCIe riser card, dust or debris in the connector, or a failing PCIe Gen5 retimer chip. The second is BIOS policy. The PCIe link speed was left on `Auto`, or ASPM power saving was on, instead of a forced Gen5. The third is thermal or electrical stress, such as a hot retimer or a voltage droop while the link trains at boot.
</details>

<details>
<summary>14. Why might a PCIe device visible in Linux `lspci` be missing from `/redfish/v1/Chassis/{id}/PCIeDevices` on some BMCs?</summary>

The BMC learns the PCIe layout in one of two ways. It may use out-of-band SMBus or MCTP wiring, or it may read the BIOS SMBIOS and BDF tables that are handed over during POST. A device that is not wired to a management bus, or that is not reported before POST completes, can be missing from the BMC's `PCIeDevices` collection.
</details>

<details>
<summary>15. What does an `@odata.id` mismatch warning in `rf_hardware.py` mean (such as the one found in DMTF's `public-smartnic` example)?</summary>

If you see this warning, the URI the resource was fetched from, such as `/redfish/v1/Chassis/Card2/...`, does not match the `"@odata.id"` string inside the returned JSON body, such as `"/redfish/v1/Chassis/Card1/..."`. That suggests a firmware templating or copy-paste bug in the BMC's Redfish provider.
</details>

<details>
<summary>16. Why does `rf_hardware.py` skip `LogServices`, `Sensors`, and `Certificates` subtrees when walking a BMC for hardware degradation?</summary>

Log collections and sensor trees often hold hundreds of URIs. Some have 75 or more system event log (SEL) entries, and others have 40 or more sensors. None of them contain `Drive`, `Port` or `PCIeDevice` resources. Skipping them cuts the crawl time from seconds to milliseconds per node.
</details>

<details>
<summary>17. Why is `{LinkState: "Disabled", LinkStatus: "LinkDown"}` considered healthy by `rf_hardware.py`?</summary>

An administrator shut the port down on purpose, because `LinkState` is `Disabled`. In that case, having no carrier, or `LinkDown`, is the expected state. It does not point to a cable or switch failure.
</details>

<details>
<summary>18. Why is checking `PCIeInterface`, `Port`, and `Drive` health via Redfish valuable during Day-0 bare-metal bring-up before Linux is installed?</summary>

It catches unseated riser cables, dead optical transceivers, wrong port speeds and dead-on-arrival NVMe drives across all racks right after power-on. You find these problems before you spend hours on OS images or on multi-node NCCL jobs.
</details>

<details>
<summary>19. What aspects of network and GPU interconnect performance can Redfish NOT measure?</summary>

Redfish reports static link negotiation, such as `Gen5 x16` or a `400 Gbps` link that is `LinkUp`. It cannot measure the things that matter most for a job: actual end-to-end data throughput, RDMA packet loss under congestion, PFC pause storms, or GPU-to-GPU NVLink fabric bandwidth. For those you need active in-band benchmarks, such as `ib_write_bw`, `nvbandwidth` and `all_reduce_perf`.
</details>

<details>
<summary>20. At which three points in a compute node's operational lifecycle should `rf_hardware.py` be executed automatically?</summary>

Run the script at three points. The first is Day-0 acceptance, right after racking, cabling and firmware baselining. The second is after maintenance or a reboot, once any BIOS or firmware update or part swap is done and before the node returns to Slurm or Kubernetes. The third is a periodic fleet audit, or straggler triage, whenever a multi-node job shows slow step times without a fatal error.
</details>

## Sources and review notes

- **Redfish Resource and Schema Guide DSP2046 (2024.4) and the official JSON Schemas** (`Drive` v1.22, `Volume` v1.11, `Storage` v1.23, `StorageController` v1.12, `NetworkAdapter` v1.14, `NetworkDeviceFunction` v1.11, `Port` v1.20, `PCIeDevice` v1.23): property descriptions and enumerations including `PCIeTypes` (`Gen1` to `Gen6`) and `LinkStatus`.
- **DMTF example trees** (`public-tower`, `public-acd`, `public-smartnic`, `public-localstorage`, `public-nvmeof-jbof`, `public-rackmount1`) at commit `fa6d23d9`.
- **NVIDIA-DevOps notes:** the PCIe downgrade scenario (volume 10 chapter 1, scenario 1) and the volume 20 chapter on DMA engine failures and PCIe issues (routed to other chapters, whose escalation rule mentions links that stay trained down at Gen3 x8). Those notes' terminal outputs are marked illustrative by their authors.
- **Run here:** `rf_hardware.py` on seven services and `hardware_lab.py` (15 checks).
- **Not verified:** how a real GPU server reports its PCIe devices through Redfish (which devices appear, under which names), whether GPUs expose `PCIeInterface`, or how Redfish values compare to `lspci`. Verify on one real node before building automation on it.
