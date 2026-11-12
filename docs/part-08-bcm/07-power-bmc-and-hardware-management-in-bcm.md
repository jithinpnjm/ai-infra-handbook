---
id: "c08-07"
title: "8.7 Power, BMC and hardware management in BCM"
sidebar_label: "8.7 Power, BMC and hardware management in BCM"
sidebar_position: 7
description: "How BCM turns servers on and off and looks after the hardware under the operating system: power control methods and scheduling, BMC networks and credentials, identifying nodes, BIOS settings with their four states, firmware flashing with AC-power-cycle activation, serial over LAN, hardware inventory and leak detection, with the manual's rules reproduced in a tested model"
status: "drafted"
tier: "1b"
level: "I"
lab_venue: "Nebius GPU"
---

# 8.7 Power, BMC and hardware management in BCM

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 8: NVIDIA Base Command Manager |
| Status | Drafted (`hardware_lab.py`: 45 checks pass; cluster commands **untested** on live BCM) |

## Why this matters for AI infrastructure

It is three in the morning and a GPU node has stopped answering. You cannot SSH in, because the operating system is the part that hung. A GPU server is more than an operating system. Under it sit a BMC, a BIOS, GPU and switch firmware, power feeds and cooling.

When a node hangs, the way back in runs through the BMC, so you power-cycle the machine from there. When you roll out new GPU firmware, a wrong activation step can leave the old firmware running while everyone believes it was updated. BCM puts all of these jobs under one tool, so you can handle a whole rack at a time. Part 7 of this handbook explains the Redfish protocol underneath. This chapter shows how BCM wraps it.

## Prerequisites and outcomes

Before you start, you should have chapters 8.1 to 8.5 behind you, and ideally Part 7. When you finish this chapter, you should be able to:

- choose a power control method, and explain what BCM does with each one.
- power nodes on and off in batches without causing a power surge.
- set up a BMC network and its credentials, and audit which credentials each node really uses.
- identify a node, read its BMC event log, and reset its BMC.
- manage BIOS settings with the four-state model.
- flash firmware, and explain why an AC power cycle is needed.
- set up serial over LAN, so a console works even when the network does not.
- list hardware, GPUs and PCI devices from the BMC, and handle leak detection.

## 1. The power control methods (4.1)

Suppose a node will not respond, and you need to know which path BCM uses to cut or restore its power. The answer lives in one property. BCM stores the method in the device's **`powercontrol`** property, and the table below lists the values you can set.

| Method | `powercontrol` | Notes |
|---|---|---|
| PDU outlet | `apc` | The node's power cable is plugged into a PDU port; BCM switches the port. The PDU must be a device in BCM and reachable. Set `powerdistributionunits mypdu:1`. Several ports per node (redundant feeds) are handled in the right order |
| BMC (IPMI) | `ipmi0` | Normal for servers. **Any PDU ports listed are ignored.** |
| BMC (others) | `ilo0`, `drac0`, `cimc0`, `rf0` | HPE iLO, Dell DRAC, Cisco CIMC, Redfish. Treated like IPMI with different interface names |
| Custom | `custom` | Your own script (section 2) |

For a server with a BMC, `ipmi0` is the normal choice, and the BMC does the switching. The vendor variants in the table are treated like IPMI, with different interface names. In that case BCM ignores any PDU ports listed for the node, and that detail catches people out.

The manual adds a few details that matter in practice. Twin nodes often share one PDU port, and then a power operation on one of them applies to all the nodes on that port. A dumb PDU, meaning one BCM cannot manage, makes the node's BMC state unknown if you assign it. Record such a PDU in the node's `notes` or `userdefined1` field instead.

You can also combine PDU and BMC control. With `PowerOffPDUOutlet = true` in `cmd.conf`, BCM switches the PDU outlet off after a BMC power-off. That cuts power to the BMC too, which draws a few watts per node. The node's BIOS must then be set to power on when power is restored, or the node never comes back. With shared ports, the outlet goes off only when every node on it is off.

A BMC with a DHCP-assigned address is not power-managed by BCM. The address can change, so that node needs a custom script, as section 2 explains. On Dell hardware, BCM calls `racadm` with `serveraction powerstatus` and `hardreset`. If the `bright` user lacks the privilege it needs, the manual shows raising it with `racadm ... set iDRAC.Users.4.Privilege 511`.

On a Redfish BMC, `power on`, `off` and `reset` perform a DC power cycle, and they assume AC power to the BMC is on. An AC power cycle, where you cut all AC inputs, is a different operation. Some firmware needs it, as section 7 explains.

Start with the BMC method for any server that has one, and keep the PDU method for the cases the BMC cannot cover.

## 2. Custom power scripts (4.1.4)

Sometimes a device fits none of the built-in methods, such as a smart plug with its own control interface. Then you write your own script and tell BCM to call it. Set `powercontrol custom` and `custompowerscript /path/to/script`. BCM then runs the script in this form:

```bash
myscript <operation> <device> [custompowerscriptargument]
```

The `operation` argument is `ON`, `OFF`, `RESET` or `STATUS`. Your script must exit with **0 on success** and a non-zero code on failure, because that exit code is how BCM knows what happened.

CMDaemon also sets environment variables, such as `CMD_MAC`. A Wake-on-LAN script can call `wakeonlan $CMD_MAC` with no extra argument. The manual ships an example at `/cm/local/examples/cmd/custompower`, and the lab runs a real script to show the same contract.

## 3. Power operations (4.2)

Suppose a rack has just come back from maintenance and every node needs power. The tempting move is to power them all at once. The delays and batches in this section exist to stop you from doing that.

```bash
device power -n node001,node018..node033 on        # in device mode of cmsh
device power -c default -d 0.1 off
device power status -g mygroup
device power history                                # last 8 by default
device power on -p 3 rack[01-12]                    # in batches of 3 racks
power off --at 23:55            power off --after 10m
```

The first guard is the delay between devices. It is 1 second by default, set with `-d`, and it protects you from power surges. Do not use `-d 0` for many nodes unless you have considered the surge.

For larger groups, `-p N` starts N items at once, with no delay inside a batch. Batches are spaced 20 seconds apart (`--parallel-delay`). Take the manual's example of 12 racks in batches of 3. That gives four waves, which start at 0, 20, 40 and 60 seconds. The lab shows the same schedule. `--parallel-dry-run` only prints the times, so use it to check a plan before you run it.

BCM uses 32 threads for power work by default, set with `PowerThreadPoolSize`. Closed devices are skipped unless you add `-f`. You cannot run these commands inside `foreach` or `range` (chapter 8.5). Instead, give the selection to the power command itself with `-n`, `-c`, `-g`, `-r` or `-s`.

`power status` reports one of `ON`, `OFF`, `RESET`, `FAILED` or `UNKNOWN`. `RESET` means the power was off only briefly during a reset. `FAILED` means communication broke down, and `UNKNOWN` means the request timed out. DGX racks report their own set: `DONE`, `GOOD`, `BUSY`, `FAIL`, `PENDING` and `CANCELLED`. The output arrives as an event, so `power status` prints nothing if private events are off.

Scheduled operations are managed with `power list`, `power wait` and `power cancel`. An operation can be waiting, busy, cancelled or done. If an operation fails, `--retry-count` and `--retry-delay` retry it, and the retry delay defaults to 3 s. `--port pdu1:3` works on a PDU port directly.

A switch must keep dynamic speed negotiation turned on. Otherwise a NIC that drops its speed to save power can lose a node or BMC link, and BCM may misread the node's state (4.5). PDU metrics `PDUBankLoad` and `PDULoad` feed monitoring (chapter 8.11). For an overview, use `pduoverview`, `cduoverview` (coolant temperatures, pressures and flow, from a building management system) or `powershelfoverview` (per-PSU power, current, voltage, fan and temperature on rack-scale systems).

Before a large power-on, run the dry run and read the schedule first.

## 4. BMC networks and credentials (3.7)

Before BCM can manage a BMC, the BMC needs an address on a network the head node can reach, and it needs a login. This section covers both, starting with the picture below.

```mermaid
flowchart LR
  H[head node: alias or interface on BMC network] --- N[bmcnet 10.148.0.0/16]
  N --- B1[node001 BMC ipmi0 10.148.0.1]
  N --- B2[node002 BMC ipmi0 10.148.0.2]
  NI[node installer] -->|configures at boot| B1
  CM[CMDaemon] -->|power, sensors, firmware| B1
```

A BMC interface is a special interface type, `bmc`, that sits on a dedicated network. The recommended network names are `bmcnet`, `ilonet`, `ipminet`, `dracnet`, `cimcnet` or `rfnet`. The default base is `10.148.0.0`, with 16 bits. Interface names start with `ipmi`, `ilo`, `drac`, `cimc` or `rf`.

For many nodes, you add the interfaces in one command: `addinterface -n node001..node150 bmc ipmi0 bmcnet 10.148.0.1`, followed by `commit`. Use `--increment` to change the step between addresses.

The head node also needs an address on the BMC network. If the BMCs share the internal network, add an alias interface. If the BMC network is separate, use a physical interface. To test it, run a ping loop. A 100 percent loss means you have a connectivity problem.

The node installer (chapter 8.4) sets each BMC's network settings and credentials at boot. The defaults are user `bright`, a random password made at install, user ID 4, administrator privilege, and a reset delay of 0. You set these in `partition use base; bmcsettings`, per category or per node. A node setting overrides a category setting, and a category setting overrides the partition. `bmcsettings --show` prints the effective values and tells you where each one comes from.

`credentialsoverview` in device mode lists the effective access and BMC credentials for each device, and where each one comes from. It never shows a real password. Each password appears as a short SHA-256 fingerprint, salted for each cmsh session. Within one session, equal passwords look equal, so a node with a different password stands out. A copied fingerprint is useless in another session. The `--inverse` option groups devices by identical credentials and lists the outliers first. Without the right tokens, fields show as `-`. This is BCM's answer to which BMC passwords have drifted, and chapter 7.14 does the same job over Redfish.

If BMC authentication fails, check `/var/log/node-installer` first, because the reason is often recorded there.

## 5. Looking at and resetting the hardware

When a machine misbehaves, you often need to find it in the rack, read what its BMC has recorded, or reset the BMC without touching the operating system. The table lists the device-mode commands for those jobs.

| Command (device mode) | Purpose |
|---|---|
| `identify -n node001 on` / `off` / `status` | blink the identification LED, to find a machine in the rack |
| `bmceventlog -n node001` | the BMC event log by Redfish (`--tail N`, `--clear`); fan failures, power events, sensor thresholds |
| `bmcreset -n node001` | hardware reset of the BMC. Out-of-band access drops for a few minutes; the node's power state and OS are **not** affected |
| `hardwareinventoryinfo` | components by Redfish: manufacturer, model, serial, part number (asset tracking, capacity planning) |
| `lspci`, `lseeprom`, `accelerators` | PCI devices (flags DPUs and accelerators), transceiver EEPROM data, accelerator count |
| `redfishsubscriptions` | which Redfish event subscriptions BCM holds for devices such as GB300 compute trays and NVLink switches |
| `rconsole` | the serial console (section 8) |
| `leakdetection enable\|disable`, `leakinfo` | coolant leak sensors via the BMC |

Use the table as a lookup. The one to be careful with is `bmcreset`. It drops out-of-band access for a few minutes, but the node keeps its power state and its OS.

Liquid-cooled systems have leak detection enabled by default. If a leak sensor is broken or reports falsely, `leakdetection disable` on that device stops an unwanted power-off until the sensor is replaced. The status line then shows `leak:disabled`. Leak detection does not apply to devices without sensors. Remember to turn it back on with `leakdetection enable`.

If you do not have BCM's tools, the head node can still talk to the BMC with `ipmitool`, from the `ipmitool` module. For example, `ipmitool -U <user> -P <pass> -H <ip> chassis identify 1` works, and so does `mc reset cold`. The IPMI port is 623/UDP, which you can test with `nc -vz -u <ip> 623`. A BMC that is up but not serving requests may need a cold reset. The manual also says pulling the power cable is the physical way to reset it, and that shutting a server down usually does not power down the BMC.

## 6. BIOS settings: four states (14.5.2)

A new Boot Mode setting can look saved and still do nothing. BCM keeps a BIOS setting in four places, and it helps to know which one you are looking at. BCM manages BIOS settings through Redfish, using JSON templates for each vendor model. Those templates live under `/cm/local/apps/cm-bios-tools/templates/`. The manual lists templates for Dell 14g, 15g AMD and Intel, R730, and HPE DL110 and DL380 Gen10.

```mermaid
flowchart LR
  A[cmsh or Base View: set] -->|commit| B[CMDaemon database: Configured]
  B -->|bios apply| C[BIOS: Pending]
  C -->|reboot| D[BIOS: Live]
```

Model comes first. Set `model` in `biossettings`, on a device or a category, before anything else.

The `status` command shows three columns. Configured is the value in the CMDaemon database. Pending is the value stored in the BIOS. Live is the value the BIOS is actually running. A configured value of `<default>`, which is null after `clear`, does nothing. Only the values you set change the BIOS.

To change Boot Mode, set it, then run `commit` to save it to the database. Run `bios apply` to stage it in the BIOS as pending, and reboot so it becomes live. `cm-bios-manage` is the underlying utility.

This is the same pending-versus-live idea as the Redfish Settings resource in chapter 7.9. After `bios apply`, check that the value shows as Pending, and wait for the reboot before you call the change done.

## 7. Firmware (14.5.3)

Firmware updates are where a node can end up half-updated, so follow the steps in order. For Redfish systems such as HPE iLO and DGX, set **`firmwaremanagemode`** in `bmcsettings`, on a device, category or partition. The values are `auto`, `b200`, `b300`, `gb200`, `gb200sw`, `gb300`, `gb300sw`, `h100`, `iLO` or `none`. HPE DL380a Gen 12 follows the same Redfish procedure as earlier HPE generations.

The manual's DGX H100 example runs as follows.

1. Download the `.fwpkg` packages from the DGX support portal, and copy them to `/cm/local/apps/cmd/etc/htdocs/bios/firmware/<platform>/` on the head node.
2. Configure the BMC network, `bmcsettings` (username, user ID, password and firmware mode), and the node's BMC interface.
3. Run `firmware info` to list the packages. Run `firmware status -n node001` to see every component with its version and state.
4. Run `firmware flash <package>` on the node. The status shows `flashing` with a progress percentage, and then the versions in transition, for example `96.00.70.00.01 -> 96.00.74.00.01`.
5. When the update finishes, the State column shows `pending`, and the Result column says `success: AC power cycle to activate`.
6. Perform an **AC power cycle** by cutting all AC inputs, for example with a PDU that turns the whole system off, or by pulling every mains lead. A normal `power reset` is a DC, board-level power cycle, and it does not activate some components.
7. Run `firmware status` again. It should show `success: activated` and the new versions.

For HPE iLO there are extra `list`, `upload` and `remove` operations. The package goes to a special flash storage first, and then you run `flash`. Older systems can flash a BIOS from a DOS image served through the PXE menu, which the manual describes in `bios/menu.conf`. Rewrite the BIOS settings afterwards, because a new BIOS version may not understand the old stored configuration.

The lab models the pending-to-active flow. You will see why the word "success" is not enough. Do not read "success" as "active". Before you call a firmware update finished, check the new version and the `activated` result.

## 8. Serial over LAN (14.7)

When SSH is impossible, for example after bad network settings or a hung boot, the BMC can carry the serial console over the LAN. This is serial over LAN, or SOL. It only works when three places agree on the same settings.

1. The BMC BIOS, with SOL enabled and matching speed, flow control and port.
2. The node kernel, through the software image's SOL settings. Run `softwareimage use default-image; set enablesol yes`, and `show | grep SOL` lists enable, flow control, port and speed.
3. The node BIOS, with its serial port enabled and the same settings.

The manual gives some rules of thumb. Use 115200 bps. Higher speeds work, but they fail more often. Turn flow control on. COM1 is `ttyS0` on x86_64, or `ttyAMA0` on aarch64, and COM2 is `ttyS1` or `ttyAMA1`. Use the terminal type VT100 or ANSI. Turn console redirection on before and during POST, and off after POST.

Two traps catch many people. BCM can configure the BMC's network and users, but it does not configure the SOL settings in the BMC BIOS. A factory reset can therefore break the match. Also, if BMC LAN traffic shares the NIC, a client plugged into the dedicated BMC port sees no console.

To connect, use `rconsole` in device mode, or `minicom`. `conman` logs serial consoles. A node installer can freeze at `freeing unused kernel memory` if SOL is on in the BIOS and the hardware cannot keep up. Disabling SOL is the workaround, as chapter 8.4 explains.

Set up all three layers before you need the console. The moment you need it is usually the moment SSH has already failed.

## 9. A routine for a hung node

A node has hung, and a ticket is waiting. The routine below strings together the commands from this chapter.

1. Check the node's status with `ds node001`, and its power with `power status -n node001`.
2. Read the BMC event log with `bmceventlog -n node001 --tail 20` for fan, power or memory events.
3. If you need the console, open it with `rconsole`.
4. Turn on the identify light with `identify -n node001 on`, so the person at the rack can find it.
5. Close the node with `close -m "hung, ticket 123" -n node001`. If the scheduler is involved, drain the node first (chapter 8.4).
6. Run `power reset -n node001`, which is a DC cycle. If the node does not come back, check the BMC with `bmcreset`.
7. After the repair, run `open` and `undrain`, and do a short burn if you replaced hardware (chapter 8.2).

## 10. Common first mistakes

Most early mistakes come from a few habits. People mix up PDU and BMC settings, or they treat a pending change as a finished one. The ten below come up again and again.

Mistakes 1 to 5 involve power. Mistake 1 is listing PDU ports on a node and expecting them to be used with `ipmi0`. Mistake 2 is assigning a dumb PDU, which makes the BMC state unknown. Mistake 3 is using `power on` with delay 0 on a whole rack. Mistake 4 is forgetting that `PowerOffPDUOutlet` needs "power on after AC loss" in the BIOS. Mistake 5 is treating pending firmware as active, or trying a DC reset for something that needs an AC cycle.

Mistakes 6 to 10 are habits of the workflow. Mistake 6 is configuring the BIOS but forgetting `bios apply` and the reboot. Mistake 7 is leaving a BMC password drifted on one node. Mistake 8 is assuming BCM copies SOL settings into the BMC BIOS. Mistake 9 is leaving leak detection disabled after a sensor swap. Mistake 10 is using a DHCP address for BMCs and then expecting BCM power control to work.

### 10.1 Deep dive: How BCM orchestrates Redfish, IPMI, and PDUs across a rack

Chapters 7.1 through 7.15 showed how to speak Redfish and IPMI to one BMC, or to a list of endpoints. In an NVIDIA Base Command Manager cluster, though, you rarely run standalone `curl` or `ipmitool` loops for daily work. `CMDaemon` acts as a stateful, topology-aware Redfish and IPMI proxy for the whole cluster. To see what BCM adds, follow what happens when an operator runs `device power on -p 3 rack[01-12]` or `firmware flash nvfw_DGX-HGX-H100x8_...fwpkg` in `cmsh`.

First, BCM resolves the target node's BMC address from its `bmc` interface (`ipmi0` or `rf0` on `bmcnet` `10.148.0.0/16`). It then finds the username, password, user slot ID (`4`), and `firmwaremanagemode` (`h100`, `b200`, `gb200`, `gb300`). It does this by walking the inheritance chain from `partition[base]` → `category` → `device`. Instead of reading passwords from a flat file on disk, it resolves them through that chain.

Second, BCM staggers power-on to protect the electrical supply. When a cooling row or Scalable Unit comes back from a planned facility maintenance window, powering on a hundred `10.2 kW` or `14.3 kW` GPU servers at the same instant creates a massive inrush current surge at the transformers and breakers. The default is a 1-second stagger between nodes (`-d 1`). You can also start `-p 3` racks at a time, with a 20-second pause (`--parallel-delay`) between rack waves. Either way, CMDaemon smooths the electrical ramp across the data-center PDUs.

Third, BCM coordinates a BMC and PDU power-off. In high-security or energy-saving modes, you may want even the BMC's standby rail off when a node is down. Set `PowerOffPDUOutlet = true` in `cmd.conf` for that. CMDaemon then issues a clean BMC power-off, waits for the host to power down, and checks whether a twin node shares the same PDU outlet (`mypdu:1`). Only then does it switch the physical outlet off. Powering back up reverses the sequence. The PDU outlet comes on first, and then BCM waits for the BMC to boot, with the BIOS set to `Always On`.

Fourth, BCM gathers telemetry across power and cooling. On liquid-cooled GB200 and GB300 NVL72 racks, power and cooling are no longer limited to single compute nodes. CMDaemon subscribes to Redfish event streams (`redfishsubscriptions`) from compute trays (`GB300`) and NVLink switch trays (`GB200SW`). It polls `33 kW` power shelves (`powershelfoverview`). It takes Coolant Distribution Unit (CDU) flow and pressure metrics from the facility Building Management System over MQTT (`cduoverview`). It also monitors tray-level leak sensors (`leakdetection` / `leakinfo`), all within one object model.

### 10.2 End-to-end runbook: Flashing and activating DGX H100/B200 firmware via BCM

A DGX firmware update touches more than thirty independent microcontrollers: BIOS, BMC, CPLD, FPGA, ERoT roots of trust, 8x SXM GPU VBIOS, 4x NVSwitches and 8x PCIe retimers. The steps below run in `cmsh`, and they keep nodes from being left in a half-updated `pending` state.

1. Stage the vendor `.fwpkg` bundles on the active head node. Download the co-validated motherboard-tray and GPU-tray `.fwpkg` archives from the NVIDIA Enterprise Support Portal, and place them in `/cm/local/apps/cmd/etc/htdocs/bios/firmware/<platform>/`, for example `h100/` or `b200/`. Run `cmsh -c "device; firmware info"` to confirm both packages show state `available`.
2. Check reachability, credentials and the firmware mode. Run `credentialsoverview --inverse` in `device` mode to confirm that no target node has a drifted BMC password. Then verify that `bmcsettings -> get firmwaremanagemode` is set to the matching platform (`h100`, `b200`, `gb200`, or `auto`).
3. Drain and close the canary node, or the rack wave. Drain the nodes in Slurm with `drain -n node001..node008`, and wait for running jobs to finish with `jobs; list`. If the platform release notes require it, stop any in-band GPU polling agents first. Then mark the nodes closed with `close -m "FW upgrade ticket CHG-402" -n node001..node008`.
4. Record the baseline. Run `firmware status -n node001` and archive the output, so you have a full record of the pre-change versions for all thirty-plus components.
5. Flash the canary node first. Run `firmware flash nvfw_DGX-HGX-H100x8_...fwpkg -n node001`, and watch `firmware status -n node001`. The state moves from `flashing`, with a percentage, to `pending`, with the result `success: AC power cycle to activate`.
6. Do a true AC power cycle, not a warm reset. Section 7 explained that a normal `power reset` in `cmsh` only performs a DC board-level reset, and it will not activate GPU-tray `ERoT`, CPLD, FPGA, NVSwitch or retimer firmware. Shut the host down cleanly. Then trigger a full AC power cycle through the rack PDU outlets, or the platform's documented virtual AC cycle procedure. Wait at least sixty seconds for the standby capacitors to discharge before you restore AC power.
7. Verify before you undrain. When `node001` boots back to `[ UP ]`, run `firmware status -n node001`. Every component should show state `completed`, result `success: activated`, and the new version string. Run `lspci` and `accelerators`, and a quick `dcgmi diag -r 2` check. Then run `open` and `undrain` the node before you move to the next rack wave.

### 10.3 Troubleshooting common BMC, SOL, and power-control failures in BCM

When a power, console or firmware command fails in `cmsh` device mode, the table below helps you narrow the cause quickly.

| Symptom in `cmsh` | Root Cause | Diagnostic & Remediation Steps |
|---|---|---|
| `power status -n node001` returns **`UNKNOWN`** | `CMDaemon` timed out reaching the BMC or PDU | 1. Check whether a non-manageable ("dumb") PDU was accidentally assigned to `powerdistributionunits` (clear it and record in `notes`).<br/>2. Ping the node's `ipmi0`/`rf0` IP from the active head node (`10.148.x.y`).<br/>3. Run `credentialsoverview --inverse` to check if `node001`'s BMC password drifted. |
| `power status` prints nothing at all on the terminal | Private event display is turned off in your `cmsh` session | Because `power status` returns its result asynchronously as a private event, run **`events on private`** (or `events on`) in `cmsh` and retry. |
| `rconsole node001` connects, but prints garbled text or hangs at `freeing unused kernel memory` | Baud rate / port mismatch across BMC BIOS, Node BIOS, and Software Image (`enablesol`), or hardware UART lockup | Verify all three layers use **`115200` bps**, flow control on, and **`ttyS0`** (`x86_64`) or **`ttyAMA0`** (`aarch64`). If the node-installer hangs at `freeing unused kernel memory`, disable SOL in the node BIOS during installation. |
| `firmware status` stays at `pending` (`AC power cycle to activate`) after `power reset` | `power reset` only performs a DC board-level reset, leaving standby rails energized | Perform a true **AC power cycle** by switching off the node's PDU outlets (or virtual AC cycle) so `5V`/`12V` standby rails discharge completely. |
| Node powers off cleanly with `PowerOffPDUOutlet = true`, but never boots on `power on` | Node BIOS `Power Restore Policy` is set to `Always Off` | When `CMDaemon` re-energizes the PDU outlet, the server waits for a physical button press unless its BIOS is set to **`Power On` (`Always On`) after AC power loss**. |

Find the row that matches your symptom, then check the cause it names before you change anything.

## Exercises

Work through these in order. The first one runs the lab, so start there.

1. Run `python3 hardware_lab.py`. Choose four checks, and explain each rule in your own words.
2. Write the cmsh commands from this chapter (untested) that give 150 nodes BMC interfaces on a new BMC network and set the BMC credentials cluster-wide. Then add one category that overrides them.
3. Use `power_schedule` to work out how long it takes to power on 40 racks in batches of 4, and what the first nodes see.
4. Write a custom power script for a device with a smart plug that has an HTTP API. What would `STATUS` print?
5. Draw the BIOS state diagram for changing the NUMA setting on 8 nodes. Include the commands for each step.
6. List the five checks that prove a GPU firmware update is really active.

## 12. Interview angles

These are the questions interviewers tend to ask about this material, with the answers worth having ready.

- "Walk me through updating GPU firmware across a rack." Stage the packages on the head node and check their status. Flash in small batches, confirm `pending`, do an AC power cycle, then confirm `activated` and the versions. Run a GPU test, draining before the update and undraining after.
- "A node shows `power status` UNKNOWN." That is a timeout from the BMC or PDU. Check BMC reachability and credentials with `credentialsoverview`, then check the BMC network and the head node's interface on it.
- "Why do BCM and Redfish both exist in your toolbox?" BCM holds the inventory, credentials and policy, and it fans out to many nodes. Redfish is the protocol each BMC speaks, and Part 7 covers it.
- "How do you power on a rack without tripping the breakers?" Use the delay and batch options. PDU limits come first, so know them before you power anything on.
- "How do you find which node has a different BMC password?" Run `credentialsoverview --inverse`.

## Checkpoint questions (20)

<details>
<summary>1. Which `powercontrol` property values does BCM support on a device?</summary>

You can set **`apc`** for a managed PDU outlet, **`ipmi0`** for an IPMI BMC, **`ilo0`** for HPE iLO, **`drac0`** for Dell iDRAC, **`cimc0`** for Cisco CIMC, **`rf0`** for a Redfish BMC, and **`custom`** for a script set through `custompowerscript`.
</details>

<details>
<summary>2. What happens to any `powerdistributionunits` ports configured on a node when its `powercontrol` is set to `ipmi0`?</summary>

They are **ignored** for normal power operations, unless `PowerOffPDUOutlet = true` is explicitly enabled in `cmd.conf`.
</details>

<details>
<summary>3. What does `PowerOffPDUOutlet = true` in `cmd.conf` do, and what BIOS setting does it require on the compute nodes?</summary>

After a node is shut down through its BMC, BCM also switches off the node's PDU outlet, which cuts standby power to the BMC as well. The node's BIOS **`Power Restore Policy` must be set to `Always On`**, that is, power on after AC loss. Otherwise the node stays off when the PDU outlet is turned back on.
</details>

<details>
<summary>4. What happens if two twin nodes share a single PDU outlet port and you issue a PDU power operation on one of them?</summary>

With `powercontrol = apc`, switching the shared outlet affects **all nodes plugged into that port**. With `PowerOffPDUOutlet = true`, BCM turns the shared outlet off only after all the nodes sharing it are powered off.
</details>

<details>
<summary>5. What command-line arguments and environment variables does a `custompowerscript` receive, and what exit code indicates success?</summary>

If you write one, BCM runs it as **`<script> <operation> <device> [custompowerscriptargument]`**. The operation is `ON`, `OFF`, `RESET` or `STATUS`, and CMDaemon sets `CMD_*` variables such as `CMD_MAC` and `CMD_IP` in the environment. Exit code **`0`** means success, and any non-zero code means failure.
</details>

<details>
<summary>6. What is the default per-device delay (`-d`) in `device power on`, and how do `-p N` and `--parallel-delay` schedule batch power-ons?</summary>

The default delay between devices is **`1` second** (`-d 1`). `-p N` starts N items at once in a batch, with no delay inside the batch. Batches are **`20` seconds** apart (`--parallel-delay`). So if you start 12 racks with `-p 3`, they begin at 0, 20, 40 and 60 seconds.
</details>

<details>
<summary>7. Why are `power` commands blocked inside `foreach` and `range` loops in `cmsh`?</summary>

Loop timing across hundreds of objects can stack power-on spikes or cloud API bursts by accident. Pass `-n`, `-c`, `-g` or `-r` directly to `device power` instead.
</details>

<details>
<summary>8. What are the five standard power status values returned by `device power status`?</summary>

They are **`ON`**, **`OFF`**, **`RESET`** (briefly off during a reset cycle), **`FAILED`** (a BMC or PDU communication failure), and **`UNKNOWN`** (a timeout).
</details>

<details>
<summary>9. What is the default subnet for `bmcnet` in BCM, and what naming prefixes are used for BMC interfaces?</summary>

The default subnet is **`10.148.0.0/16`**. BMC interface names start with **`ipmi`**, **`ilo`**, **`drac`**, **`cimc`** or **`rf`**, for example `ipmi0` or `rf0`.
</details>

<details>
<summary>10. What are BCM's default BMC username, user slot ID, and privilege level, and which component configures them on the node's BMC?</summary>

The default username is **`bright`**, with a random password generated at cluster install, User ID **`4`**, and Administrator privilege. The **`node-installer`** configures these on each node's BMC at boot.
</details>

<details>
<summary>11. In what precedence order do partition, category, and node `bmcsettings` apply, and which flag shows the effective source?</summary>

**Node overrides category, which overrides partition (`base`)**. Running `bmcsettings --show` displays the effective settings and which level supplied each one.
</details>

<details>
<summary>12. How does `credentialsoverview --inverse` in `cmsh` `device` mode help spot drifted BMC passwords?</summary>

In practice, it hashes each device's effective credentials into a **per-session salted SHA-256 fingerprint**. It then groups devices with identical fingerprints and lists the smallest groups, the outliers, first. Cleartext passwords are never shown.
</details>

<details>
<summary>13. What does `bmcreset -n node001` do, and does it reboot the running Linux OS on `node001`?</summary>

`bmcreset` performs a hardware cold reset of the node's **BMC microcontroller only**. Out-of-band BMC access drops for a couple of minutes while the BMC reboots. The host's power state and its running Linux OS are **completely unaffected**.
</details>

<details>
<summary>14. What are the four states and three transitions for managing BIOS settings in BCM (§14.5.2)?</summary>

1. Edit in `cmsh` or Base View, after setting `model`, in `biossettings`.
2. **`commit`** saves it in the CMDaemon database as **`Configured`**.
3. **`bios apply`** stages it to the BMC through Redfish as **`Pending`**.
4. A **node reboot** lets UEFI apply it at POST, and it becomes **`Live`**.
</details>

<details>
<summary>15. In BCM `biossettings`, what happens to a BIOS attribute whose Configured value is `<default>` (`null`, after `clear`)?</summary>

BCM **leaves that BIOS attribute untouched** on the server. Only attributes with explicit non-default Configured values are pushed during `bios apply`.
</details>

<details>
<summary>16. What does `firmwaremanagemode` in `bmcsettings` configure, and list six supported platform values?</summary>

If you set it, it tells BCM which Redfish or platform firmware workflow to use for the device, such as `cm-nvfwupd` or iLO. Supported values include **`auto`**, **`h100`**, **`b200`**, **`b300`**, **`gb200`**, **`gb200sw`**, **`gb300`**, **`gb300sw`**, **`iLO`**, and **`none`**.
</details>

<details>
<summary>17. After `firmware flash <pkg>.fwpkg` completes on a DGX H100, why does `firmware status` show state `pending` with `success: AC power cycle to activate`, and why is `power reset` insufficient?</summary>

The new firmware is staged in inactive flash. It needs all AC input power cut, through the rack PDU outlets or mains cords, so the standby rails discharge. That reinitializes the GPU tray's **`ERoT`**, **`CPLD`**, **`FPGA`**, **`NVSwitch`** and retimer chips. A standard `power reset` in `cmsh` performs only a **DC board reset**, which leaves the old firmware running.
</details>

<details>
<summary>18. Which three places must have matching baud rate, port, and flow-control settings for Serial over LAN (`SOL` / `rconsole`) to work?</summary>

1. **The BMC BIOS or SOL configuration.**
2. **The node's motherboard BIOS serial redirection settings.**
3. **The software image's kernel SOL parameters**, set with `softwareimage use default-image; set enablesol yes`.
</details>

<details>
<summary>19. What serial port device name and baud rate does the BCM manual recommend for `SOL` on `x86_64` versus `aarch64` (ARMv8)?</summary>

The manual recommends **`115200` bps** with hardware flow control on. On `x86_64`, use **`ttyS0`** for COM1, or `ttyS1` for COM2. On `aarch64`, use **`ttyAMA0`** for COM1, or `ttyAMA1` for COM2.
</details>

<details>
<summary>20. When should you run `leakdetection disable` on a liquid-cooled node, and what status indicator reminds you that it is disabled?</summary>

Only temporarily, when a faulty leak sensor raises false alarms that would otherwise trigger an unwanted emergency power-off. Keep it disabled until the sensor is replaced. While it is disabled, the node's status line shows **`leak:disabled`**.
</details>

## Sources and review notes

- **BCM 11 Administrator Manual:** chapter 4 (power methods, operations, overviews, monitoring, switch settings), section 3.7 (BMC networks, authentication, `credentialsoverview`, identification, event log, reset, port queries, leak detection), 14.5 (BIOS via Redfish templates and four states; firmware via Redfish with the DGX H100 example; the DOS image and iLO upload skimmed), 14.7 (serial over LAN), 14.11 (hardware information), appendix N (Redfish in BCM).
- **Companion chapters:** Part 7 (Redfish, firmware, BIOS, hardening) for the protocol side; 8.4 for node-installer BMC settings and the BMC cold reset.
- **Run here:** `hardware_lab.py` (45 checks): power method rules, shared ports, scheduling arithmetic, a real custom power script, BMC addressing and inheritance, credential fingerprints, the BIOS four-state flow, the firmware pending-to-activated flow, SOL consistency.
- **My own choices, not the manual's:** the lab's reading that a rack batch starts all its items together; the firmware component state model (it follows the manual's example output, not CMDaemon's code); the hung-node routine (an assembly of the manual's commands, not a manual procedure).
- **Not read or not covered:** the NVIDIA Mission Control Manual's rack power, power shelf and leak chapters; HPE iLO and Dell DRAC specifics beyond the passages above; BIOS template contents; `bios apply` option details; `cm-bios-manage`; the `firmware` command's less common options.
- **Not verified:** everything about real hardware: whether a given DGX needs an AC cycle for each component, output formats, and version differences. The manual's example is for the DGX H100; the GB-series differ.
