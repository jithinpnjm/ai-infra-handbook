# Voice sample 8: parts part-07-redfish-bmc, part-09-nvidia-systems, part-13-ai-storage, part-18-security, part-20-nebius-sre-interview

## FILE docs/part-07-redfish-bmc/01-bmcs-ipmi-and-out-of-band-management.md

Picture a GPU server that stops answering in the middle of a long job. An eight-GPU server, such as an NVIDIA DGX H100 or HGX node, costs hundreds of thousands of dollars. It draws up to 10.2 kW, and it sits in a dense data center hall that may be thousands of miles from your desk.

---

Without an independent recovery path, every hung kernel or BIOS change would need a technician with a crash cart. That person would walk down the hot aisle and press a physical power button. The Baseboard Management Controller, or BMC, removes that dependency. It is a small, independent computer soldered onto the server motherboard. It runs from auxiliary standby power whenever AC power is connected, and it has its own dedicated out-of-band (OOB) management network. From there it can read thermal sensors, capture hardware fault logs, stream the serial console, flash firmware, and toggle the power-reset lines of the host CPUs.

---

In *Supercomputers for Linux SysAdmins*, chapter 10, Sergey Zhumatiy describes the management controller as *"a small independent server"*. It connects to the main motherboard through low-level hardware buses. These include `I2C`, `SMBus`, `PECI`, `LPC`/`eSPI` and `UART`. Across standard 1U and 2U servers and 8U GPU systems, the BMC provides eight core capabilities.

---

Imagine a junior engineer who proposes updating firmware on 100 GPU servers with a Bash `for` loop. The loop would SSH into each host, download the firmware bundle, and flash the hardware in-band. It looks simple, and it is the design you should reject. This scenario comes from `volume-05/chapter-03-dgx-management-plane.md` and `volume-10/01-bare-metal-and-bmc-lifecycle.md`.

---

## FILE docs/part-07-redfish-bmc/02-redfish-concepts-service-root-resources-collections-odata.md

Read Figure 1 with two arrow styles in mind. Solid arrows show **subordinate containment**, the parent-to-child layout of the URI tree. For example, `Chassis_0` contains `Sensors`. Dashed arrows show **associated cross-links** under the `Links` property. `System_0` links to `Chassis_0`, and `Chassis_0` links back to `System_0`. Those back-links create cycles, so DSP0266 §5.3 calls the Redfish data model a **directed graph, not a strict tree**. Any crawler that follows `@odata.id` references must keep a `visited` set, or it will loop forever.

---

Two of these rows deserve a closer look. `Id` is the final segment of the URI, so it must stay URL-safe. `Name` is only a label, and two siblings may share it. Use `Id` when you build a path and `Name` when you show something to a person.

---

The first is the difference between an empty string and `null`. They mean different things. An empty string, `""`, says the property is supported and healthy, but its value is blank. An `AssetTag` of `""` is normal before an admin assigns one. A `null` says the BMC cannot get or compute the value right now. For example, `"Reading": null` on a host CPU temperature sensor is expected while the host is powered off, or when an `I2C` sensor bus read fails. Never coerce `null` to `0` or `""` in telemetry scripts. Treating `"Reading": null` as `0 °C` would corrupt your thermal data.

---

Notice the two `ComputerSystem` rows in that output. They are the host tray and the GPU baseboard, found by the same crawler that found everything else. The `LogEntry` row is the largest group, with 78 entries, so it is where pagination from Section 5 shows up in practice.

---

## FILE docs/part-07-redfish-bmc/03-the-redfish-protocol-http-methods-headers-status-codes-query-parameter.md

DSP0266 §6.5 solves this "lost update" problem with HTTP entity tags, called `ETag`s. An `ETag` is a version label that the BMC attaches to a resource. Each `GET` returns an `ETag` header and a matching `@odata.etag` property. A value looks like `"fbd530fd09c0"` (a strong ETag) or `W/"fbd530fd09c0"` (a weak ETag). The BMC decides how to build the value, whether by hash, counter, or timestamp. Your client should treat the string as opaque and never try to parse it.

---

The order is not a style choice. Filtering comes first, so it decides which members are left to skip and count. `$select` comes last, so it can only trim what the earlier steps produced. A worked example makes this concrete.

---

A malformed value or the wrong target gets `400 Bad Request`. `$top=abc` is not an integer. Sending `$top=1` or `$skip=1` to a single resource, such as `/redfish/v1/Systems/System_0?$top=1`, targets the wrong kind of resource. Combining `only` with another parameter, as in `?only&$top=1`, is also refused with `400 Bad Request`.

---

The first bug was an error handler that fell through. When `$top` held a non-integer, our first query helper sent a `400 Bad Request` and then returned `None`. The caller read `None` as "no query error" and carried on to write a second `200 OK` on the same socket.

---

## FILE docs/part-07-redfish-bmc/04-redfish-authentication-sessions-and-security.md

Sessions do not expire at a fixed time. They time out when they go idle. While you keep sending requests inside the timeout, the token stays valid. A service can also set an absolute timeout through `AbsoluteSessionTimeout` in the schema guide. To log out, send a `DELETE` to the Session address. An administrator can end other users' sessions the same way. Services must not use HTTP cookies to authenticate requests.

---

The map also has its own logic. Separate objects inside an operation's array mean logical OR. For example, `[{"Privilege": ["ConfigureUsers"]}, {"Privilege": ["ConfigureSelf"]}]` means either `ConfigureUsers` or `ConfigureSelf` is enough. Several names inside the same `"Privilege"` array mean logical AND. So `[{"Privilege": ["ConfigureComponents", "OEMSysAdminPriv"]}]` requires both privileges. The spec covers this in §13.4.3.8.

---

Preventing this takes three habits in every client you write. First, wrap every session login in a `try/finally` block, so the `DELETE` runs even when an exception interrupts the script. Second, reuse one long-lived session across several reads to the same BMC, instead of logging in once per metric. Third, give your scraper its own dedicated `ReadOnly` account. An administrator can then inspect `/redfish/v1/SessionService/Sessions`, see which `UserName` owns the orphaned sessions, and end them one at a time with `DELETE`. Active maintenance sessions keep running.

---

If your Day-0 discovery pipeline assumes that a successful 201 Created from `/redfish/v1/SessionService/Sessions` means the node is ready for inventory and firmware checks, it fails on the very next step. As soon as the script sends `GET /redfish/v1/Systems`, the BMC returns 403 Forbidden with the `PasswordChangeRequired` message from the Base Message Registry.

---

## FILE docs/part-07-redfish-bmc/05-redfish-actions-tasks-events-and-subscriptions.md

A fan can fail, or a power supply can drop out, and the tool should learn about it as it happens. Redfish has a concept for each job: **actions** for asking, **tasks** for waiting, and **events** for hearing about trouble.

---

1. Start with the graceful options, `GracefulRestart` or `GracefulShutdown`. They let the OS flush disks and stop services.
2. Use `ForceRestart` or `ForceOff` only when the OS is frozen. They can corrupt files and kill running jobs without warning.
3. `PowerCycle` and `FullPowerCycle` are stronger. Reach for them when a restart does not clear a hardware fault.
4. `Nmi` is for debugging a hang. Whether the machine then writes a crash dump depends on how the operating system is set up.

---

In real fleets, people mix the methods: events for fast alerts, and a slow poll as a safety net. Keep in mind that there is no history. Any event lost during an outage is gone, but a periodic poll still catches the state.

---

Scaling from one test rack to a thousand-node AI factory breaks the simple polling approach. Say you poll forty sensors and seventy-five log entries on every BMC every five seconds. Your monitoring cluster then generates tens of thousands of HTTPS requests per second. Those requests hit slow embedded ARM processors over a `1 GbE` out-of-band network. Slow the interval to five minutes to protect the BMCs, and you may take up to five minutes to notice that a rack PDU circuit tripped or a cooling fan failed.

---

## FILE docs/part-07-redfish-bmc/06-the-redfish-schema-reading-csdl-json-schema-and-the-resource-guide.md

Why keep both a versioned and an unversioned file? The spec's answer is that references from other resources use the unversioned definition, so nothing depends on one particular version. The unversioned file has no property details. It holds the list of versions, the allowed URIs (such as `/redfish/v1/Systems/{ComputerSystemId}`) and the capabilities, meaning whether you can create, update or delete. The versioned file holds the real properties and actions for that version.

---

The `mockups` folder is a free library of realistic Redfish trees. It covers rack servers, liquid-cooled servers, PDUs, power shelves, cooling units, storage, CXL, telemetry and more. You can serve any of them with the mock and practise your scripts against it.

---

The same idea applies to Attribute Registries for BIOS and boot configuration, which chapter 7.14 uses. A dual-socket Intel Xeon server, an AMD EPYC server and an NVIDIA Grace ARM server each have their own UEFI setup options. No fixed `Bios` schema could list every possible BIOS attribute. So the `Bios` resource carries a free-form `Attributes` dictionary and an `AttributeRegistry` pointer, such as `"BiosAttributeRegistry.v1_0_0"`. Your tool fetches that Attribute Registry from the BMC. It then learns the exact data type, allowed enum values, read-only status and menu hierarchy of every BIOS setting on that motherboard. All of this happens before it sends a single `PATCH` request.

---

1. Start with the command line, because it is the quickest way to see a schema. Run `python3 code/part07/schema_tools.py explain Chassis.v1_23_0`. Find three read-only properties and three read-write properties, then find the one required property, `Id`. Finally, check the resource capabilities. They should read `insertable=False updatable=True deletable=True`.
2. Next, you will look at one property in detail. Run `python3 code/part07/schema_tools.py explain ComputerSystem.v1_17_0 --prop Boot`, then run it again with `--prop PowerState`. Read the JSON Schema definitions for `BootSourceOverrideTarget` and `PowerState`. Work out why `PowerState` has `"readonly": true`.
3. Now test the validator with a payload you break on purpose. Run `python3 code/part07/schema_lab.py` and confirm it prints `11 passed, 0 failed`. Copy `Systems/437XR1138R2/index.json` from the `public-rackmount1` mockup to `/tmp/bad_sys.json`. Change `"PowerState"` to `"Maybe"`, then run `python3 code/part07/schema_tools.py check /tmp/bad_sys.json`. Read the exact validation error it reports.
4. Look up a MessageId in the registry. Open the latest `Base.1.*.json` file in `$REDFISH_PUBLICATIONS/registries/` and find the entry for `PropertyValueNotInList`. Write down its `Message` template with the `%1` and `%2` placeholders, its `NumberOfArgs`, its `Severity` and its `Resolution`.
5. Crawl a DMTF mockup tree. In one terminal, start `python3 code/part07/redfish_mock.py --mockup $REDFISH_PUBLICATIONS/mockups/public-liquid-cooled-server --port 8443`. In a second terminal, run `python3 code/part07/schema_tools.py crawl http://127.0.0.1:8443 admin adminpass`. Confirm that all `241` resources validate cleanly against the official DMTF JSON Schemas.
6. Write a small helper. Using `schema_tools.load()`, write a 15-line Python function. It takes a versioned `@odata.type` string, such as `"#ComputerSystem.v1_17_0.ComputerSystem"`, and returns the sorted list of top-level property names whose `"readonly"` value is `False`.

---

## FILE docs/part-07-redfish-bmc/07-systems-chassis-and-managers-the-core-resource-model.md

Next comes state. `PowerState` can be `On`, `Off`, `PoweringOn`, `PoweringOff` or `Paused`. `Status` holds `State`, `Health` (`OK`, `Warning` or `Critical`) and `HealthRollup`. `HealthRollup` is the worst health of the resource and everything below it. That means a bad chassis fan can make the system show `Warning` even when the CPU is fine. `LastResetTime` tells you when the system last restarted, and `BootProgress` gives the last boot state.

---

Boot control lives in `Boot`. This is where the one-time or continuous boot override sits. `BootSourceOverrideEnabled` can be `Disabled`, `Once` or `Continuous`. `BootSourceOverrideTarget` names where to boot from, with values such as `None`, `Pxe`, `Hdd`, `Cd`, `Usb`, `BiosSetup`, `Diags`, `UefiShell`, `UefiTarget`, `UefiHttp`, `RemoteDrive`, `UefiBootNext`, `Recovery` and a few more. `UefiHttp` is the HTTP network boot from chapter 6.22. `BootSourceOverrideMode` is either `Legacy` or `UEFI`. Provisioning tools use these three fields to say "boot from the network once". Chapter 7.14 uses them.

---

`Manager.Reset` restarts the BMC. The schema says that if the manager provides the Redfish service, it must send the answer before resetting, to avoid client timeouts. `Manager.ResetToDefaults` takes `ResetAll`, `PreserveNetworkAndUsers` or `PreserveNetwork`, so a factory reset can keep the network and the accounts. `ForceFailover` and `ModifyRedundancySet` apply to redundant managers.

---

Look at the counts. There are five managers, five chassis and four systems. One enclosure manager looks after the box, and each blade has its own BMC. This is why "one server equals one BMC" is a habit you need to unlearn.

---

## FILE docs/part-07-redfish-bmc/08-power-thermal-sensors-and-environment.md

A GPU alarm fires at 3 a.m. The alert says "hot", but a number alone does not tell you much. You need to know what was measured, in which unit, and where on the machine. A `Sensor` answers all three questions in one resource. The table below lists the properties you will use most.

---

Because the unit and the context travel with the value, one program can read every sensor. It does not need a separate list for each vendor. You find sensors under `Chassis/<id>/Sensors`. Some BMCs also place sensors under other resources. In a fleet tool, treat the chassis list as the main route, and the metric links of components as an extra source.

---

Fan redundancy tells you how serious a failed fan is. Take DMTF's example, where each fan group has `MinNeededInGroup: 1` out of two fans. If one fan fails, one fan is still left, so the group still meets its minimum. The failure becomes a repair ticket, not an emergency. Losing both fans would be a different story.

---

Read the block as a short story. The server is drawing 374 W, and the cap is set to 500 W. The BMC allows any cap between 150 W and 1000 W, so 500 W is inside the range. To change the cap, you `PATCH` the control's `SetPoint`, and you use the usual ETag care from chapter 7.3. The NVIDIA notes say power capping on DGX H100 and H200 is done through Redfish. I could not check how.

---

## FILE docs/part-07-redfish-bmc/09-storage-network-adapters-and-pcie-devices.md

Here is the arithmetic. Gen5 gives 32 GT/s on each of 16 lanes, which is about 64 GB/s. Gen3 gives 8 GT/s on each of 8 lanes, which is about 8 GB/s. The degraded link keeps only about one-eighth of the original bandwidth. This can happen with a bad cable or riser, dust, a loose card, a BIOS setting, or power problems.

---

Use the lab across the fleet. Run the tool against every BMC after racking and after each maintenance window. A GPU node with one degraded link should stay out of the scheduler until that link is fixed. For depth, pair the tool with the host-side checks in Part 10, such as NVLink, `nvidia-smi` and DCGM. Make a clean run the condition for putting any node back into service.

---

Redfish does not show how fast data actually moves. A link can run at full width and still be slow, because of congestion or a software setting. The speed and width it reports are the values the BMC reads. Some BMCs cannot see every device, since they only see what is wired to them or what the vendor mapped. A device missing from the list is therefore not proof that the device is absent.

---

The second silent problem in AI fabrics is a high-speed port that links up, but at a fraction of its rated speed or lane width. You will find these ports under `NetworkAdapter/Ports`. Modern 400 Gbps and 800 Gbps InfiniBand and Ethernet links are built from parallel lanes. Each lane is a SerDes circuit, which converts data to and from a serial signal. A typical link uses 4 lanes of 100 Gbps PAM4 signaling, or 8 lanes of 100 Gbps.

---

## FILE docs/part-07-redfish-bmc/10-firmware-inventory-and-the-updateservice.md

Firmware is software that lives on a chip inside a part, such as a GPU or a network card. The user's notes list seven groups that an AI cluster has to keep consistent. The table below shows what each group controls and why you should care.

---

Both methods answer with `202` and a task monitor, which chapter 7.5 covers. The task's `Messages` tell you how the update went. They come from the **Update message registry**, and the stage messages below follow the image from the first transfer to the wait for activation.

---

The notes make five points, and you should read each one before you run anything. First, `show_version -p` compares installed versions with a package. Second, `update_fw -s <file>.json` limits the update to the targets in that file. Third, stop GPU activity first, because `nvidia-smi` can block a VBIOS update. Fourth, add no extra load, such as jobs, diagnostics or monitoring, while the update runs. Last, downgrades follow a `ForceUpdate` procedure.

---

One bug showed up on my first run, and it matters for you because real BMCs behave the same way. The update took longer than the simulated session timeout, so the client got a 401 halfway through. I then added automatic **session renewal** to my Redfish client. When it gets a 401 while holding a token, it logs in again once and repeats the request. Real BMCs time sessions out too, and a long update is exactly when that happens.

---

## FILE docs/part-07-redfish-bmc/11-log-services-event-logs-and-diagnostics.md

Before you start, work through chapters 7.2, 7.3, 7.5 and 7.7. This chapter is about reading what the BMC remembers. When you finish, you can find every log on a Redfish service and read the fields of a log entry. You will know how Redfish event entries differ from IPMI SEL entries. You can also explain overwrite policies, and see why a full log can hide the event you need.

---

In the DMTF examples, this warning fires on every service, because the sample dates run from 2012 to 2016. That is the right behaviour for stale data. It is also a reminder to check the BMC's NTP setting, which lives in `NetworkProtocol` (chapter 7.15).

---

Now suppose a GPU job crashes on that node at `14:22:05 UTC` on October 28. The BMC's `SEL` records the fatal PCIe error, but with a timestamp from three years ago. An engineer who filters with `--since 2026-10-28T14:00:00Z` misses the hardware fault completely. That engineer then concludes the BMC log was clean.

---

1. Capture the readable BMC event logs. Run `rf_logs.py show`, and save the raw JSON from `/Managers/{id}/LogServices/SEL/Entries` and `EventLog/Entries`. Your team then has an immediate text summary of the fault timestamps, `MessageId` codes and `OriginOfCondition` links.
2. Trigger the out-of-band BMC diagnostic bundle with `LogService.CollectDiagnosticData`. Run `python3 code/part07/rf_logs.py collect https://<bmc> <user> <password> --out <node>-bmc-bundle.bin`. Checks 14 and 15 of `logs_lab.py` verify this step. The command posts a body with `DiagnosticDataType` set to `Manager` or `OEM`. It polls the `202 Accepted` task monitor until the task finishes, then follows the `LogEntry` `Location` header and downloads the binary archive from `AdditionalDataURI`. Last, it checks that the downloaded byte count matches `AdditionalDataSizeBytes`, and exits with `exit 7` on a mismatch.
3. Capture the in-band host bundle, if SSH to the host OS still works. Run `sudo nvsm dump health` on DGX systems, or `sudo nvidia-bug-report.sh`. Either one captures the in-band kernel ring buffer, PCIe AER registers, NVLink error counters and DCGM state.
4. Clear the BMC log last, and only after the repair. Clear the `SEL` and `EventLog` only when the physical repair is finished and both bundles are archived in your ticket system. Pass the ETag of the `Entries` collection in `LogEntriesETag`, so a new post-repair fault is never wiped by mistake. A stale ETag gets `412 Precondition Failed`.

---

## FILE docs/part-07-redfish-bmc/12-automating-redfish-with-python-ansible-and-go.md

Clicking through a web page works for one server. With 1,000 servers you need code, and code that talks to BMCs has to be careful. A bad retry loop can lock accounts. An unbounded loop can overload the management switches. A script that dies on the first failed host leaves half a fleet changed and the other half untouched. This chapter shows the same few operations in three languages, then the rules that keep any of them safe at scale.

---

The module help lists more commands. Besides the ones above, you will find `GetFanInventory`, `GetPsuInventory`, `GetBiosAttributes`, `GetBootOrder` and others. `redfish_command` also covers power, with `PowerOn`, `PowerForceOff` and `PowerReboot`. It covers boot override with `SetOneTimeBoot` and `EnableContinuousBootOverride`, and firmware with `SimpleUpdate` and `MultipartHTTPPushUpdate`. I tested only the commands in the table.

---

A test against one happy-path mock server only proves that your JSON field names are spelled right. It says nothing about failure isolation. That is why `code/part07/fleet_lab.py` starts fifteen separate HTTPS mock servers at once and injects six failure modes:

---

Running `python3 code/part07/fleet_lab.py` in CI takes less than five seconds on a laptop. It gives you mathematical confidence that a single broken BMC in Rack 12 will never stall a cluster-wide operation or lock out your administrative credentials. Run it before any new script touches real hardware.

---

## FILE docs/part-07-redfish-bmc/13-redfish-on-nvidia-dgx-and-hgx-bmc-gpu-baseboard-and-management.md

Two more facts belong to that second point. Four-GPU Redstone boards often wire their GPUs point-to-point over NVLink without NVSwitch chips, and you cannot upgrade them to 8 GPUs later. Power delivery matters too. Current equals power divided by voltage, so $I = P / V$. Feeding 8 GPUs at 700 W each means 5.6 kW or more. At `12V`, that would need more than 460 A, and the copper would lose a large amount of power as $I^2 R$ heat. Stepping the distribution bus up from `12V` to the `48–54V` class cuts the current roughly $4\times$. The on-board VRMs then step the voltage down to about `~1 V` at the GPU die.

---

Use both views together. The BMC sees fans, power supplies and a host that is down. NVSM and DCGM see GPU errors, NVLink counters and clocks. When you investigate a fault (chapters 7.8, 7.9 and 7.11), line the two up on one timeline so you can see which event came first.

---

Suppose you need automation for a DGX that you rarely get to touch. The safest approach is to **record** its Redfish tree once and replay it from then on. The tool `rf_record.py` crawls a service using `GET` only. It saves each resource as `index.json` in a folder that follows the DMTF mockup layout. With `--redact`, it also replaces serial numbers, UUIDs, MAC and IP addresses with placeholders.

---

I tested the round trip on my mock. The recording held 153 resources, and I replayed it through `--mockup`. A crawl of the replay found the same set of resources as the original. The crawler counted 154 URIs, including the live session. In `--mockup` mode the data is read-only, so a recording lets you test inventory, health, drift and parsing code, but not actions.

---

## FILE docs/part-07-redfish-bmc/14-fleet-scale-hardware-management-and-node-lifecycle-automation.md

1. Describe the target state in files under version control: a firmware baseline, a BIOS target, an acceptance profile and an account policy.
2. Measure the real state the same way on every node, using inventory, hardware, sensors and logs.
3. Compare and report drift automatically and often.
4. Change things in small, verified, repeatable steps, with a human decision before anything risky.

---

On my mock, the real `plan` reported six differences, two of which were already right. After `apply --yes --reset`, the last line read `LIVE and verified`. A second `plan` then showed `0 to change`. Without `--yes`, `apply` only prints what it would send. The tool changes only the attributes that differ, so you can run it again and again. Engineers call this property idempotent. Run `plan` before every `apply`, and send the change only when the plan shows what you expect.

---

Here is the trap. A `Continuous` network boot left in place makes the node reinstall itself at every restart. Always use `Once` for provisioning, and check afterwards that the override reads `Disabled`. For diagnosing why a network boot fails, use the D-T-B-I chain from chapter 6.22. The letters stand for DHCP, Transfer, Boot-mode and Image.

---

A node that is racked but not yet ready sits in an awkward middle state. Part of its work is done, part is not, and someone has to decide where to resume. `code/part07/node_lifecycle.py` handles this by taking one node from "racked" to "ready" in six steps. The diagram shows the order and the places where a run stops.

---

## FILE docs/part-07-redfish-bmc/15-bmc-security-hardening-and-attestation.md

The BMC is the most privileged computer in the rack. It can power the server on and off, mount a virtual disk, open a console, rewrite firmware and read hardware state. It works below the operating system, where your normal security tools cannot see it.

---

The tool does not read BMC-specific security features. It skips SSH key policy, LDAP or Active Directory integration, and role mapping, where the schema has `RemoteRoleMapping`. It also skips multi-factor authentication settings and the `SecurityPolicy` resource. That resource holds the TLS and SPDM policy, including allowed versions, algorithms, and trusted and revoked certificates, as shown in DMTF's example. A mature audit adds these checks, using the resources your BMC really has.

---

Firmware is the small software inside each part of the server: the GPU, the NIC, the BIOS and the BMC. If an attacker replaces it with a malicious copy, that copy survives an operating system reinstall. The Security volume's chapter on hardware and firmware trust explains the idea for beginners. Four defences follow from it.

---

What this means for you is that setting `SecureBootEnable` to true is not enough. The change applies at the next boot, just as a BIOS setting does in chapter 7.14. Secure Boot protects you only when a platform key is enrolled, which is User Mode. So a checker must read `SecureBootCurrentBoot`, not only `SecureBootEnable`. My audit does exactly that.

---

## FILE docs/part-09-nvidia-systems/01-dgx-system-families-and-what-they-are-for.md

Not every cluster runs multi-node frontier training. In enterprise data centers and edge sites with standard air-cooled racks, three PCIe accelerators dominate inference and multimodal pipelines. Choosing the wrong card among them can stall modern transformer deployments on missing precision formats or PCIe bus saturation.

---

Imagine buying eight Formula One engines and bolting them into a backyard kit car. Individually, each engine is a masterpiece. Together, the frame twists, the radiator boils over in two minutes, and the transmission shears off. In AI infrastructure, assembling bare components in a generic chassis without full-stack validation is known as the Whitebox Fallacy.

---

When a frontier Mixture-of-Experts or trillion-parameter model outgrows an 8-GPU server, splitting Tensor Parallelism or all-to-all expert routing across servers hits an immediate wall. Inside an 8-GPU node like the DGX H100 or DGX B200, the eight GPUs communicate at NVLink speeds. Adding a ninth GPU in a second server drops communication to the speed of a network card, creating an eighteen-fold bandwidth cliff that stalls multi-node Tensor Parallelism and Mixture-of-Experts routing.

---

The DGX GB200 NVL72 and DGX GB300 NVL72 eliminate that 8-GPU wall by disaggregating eighteen compute trays and nine NVLink switch trays across a passive blind-mate rear copper backplane. All 72 GPUs share full NVLink 5 bandwidth in a single NVLink domain without the power draw and transceiver failure rates of 72-GPU optical cabling. Chapter 9.5 covers the complete NVL72 compute tray, switch tray, power shelf, and crossbar architecture.

---

## FILE docs/part-09-nvidia-systems/02-inside-a-dgx-h100-and-h200-system.md

Each H100 or H200 SXM5 GPU exposes 18 fourth-generation NVLink sub-links. Every individual sub-link runs at 50 GB/s bidirectional, which equals roughly 25 GB/s in each direction. Bonding 18 sub-links gives each GPU 900 GB/s of bidirectional bandwidth. That is roughly seven times the 128 GB/s bidirectional rate of a 16-lane PCIe Gen5 slot.

---

The DGX H100 and DGX H200 solve this by sharing the exact same 8U mechanical chassis, 10.2 kW power budget, and dual Xeon 8480C host tray. Both systems also share the same 700W per-GPU thermal envelope, 900 GB/s NVSwitch fabric, and Tensor Core math engines. What changes between them is the High Bandwidth Memory stack on each SXM5 package. The H200 replaces 80 GB of HBM3 with 141 GB of faster HBM3e inside the same thermal footprint.

---

A result around 43 percent sits cleanly inside the 40 to 60 percent target band for well-tuned large-model training clusters. If Model FLOPs Utilization drops to 20 percent, the DGX node is starving on data loading. It may also be hitting memory bandwidth limits with tiny microbatches, or suffering from a PCIe or NUMA network misconfiguration.

---

If an operator runs a standard operating system reboot or a board-level DC power reset in `cmsh`, the new GPU-tray firmware does not activate. The GPU Tray Satellite BMC, the seven ERoT security controllers, the tray FPGA, and the eight PCIe retimers remain powered by the standby rails of the six power supplies. Those standby rails stay live whenever AC cords are plugged in.

---

## FILE docs/part-09-nvidia-systems/03-hgx-platforms-and-oem-integration.md

Think of the DGX versus HGX strategy like an aircraft engine manufacturer that also sells a flagship corporate jet. Buying a DGX is buying the complete turnkey jet directly from the engine maker. Buying an HGX-based server is like an airframe manufacturer buying the pre-assembled twin-engine wing assembly. The airframe builder then integrates its own fuselage, cockpit avionics, and maintenance crew around it.

---

When an NVLink error halts a training job on an OEM server, replacing a $30,000 SXM GPU module will waste two days if the fault sits inside a soldered NVSwitch chip. Operators need to know which components on the HGX tray can be swapped in the rack. They must also know which faults require replacing the entire baseboard.

---

An `Xid 79` error means the host CPU lost PCIe link framing with GPU 4. On an OEM server, that signal path crosses the OEM motherboard, OEM PCIe riser card, high-speed internal interconnect cable, HGX PCIe Gen5 retimer, and SXM5 mezzanine socket. A slightly loose PCIe riser cable vibrated by high-RPM chassis fans produces the exact same `Xid 79` error as a dead GPU.

---

Notice the distinction in Platform B. Omitting `nvidia-smi topo -m` is an evidence gap marked `Missing` that reduces confidence until proved. In contrast, sharing the storage and compute network or supplying only four compute NICs is a verified mandatory requirement failure.

---

## FILE docs/part-09-nvidia-systems/04-grace-cpu-gh200-and-gb200-superchips.md

When a model or dataset outgrows GPU memory on a traditional x86 server, training and inference speeds collapse. Platform engineers and ML researchers feel this slowdown immediately when a job fits in host DDR5 RAM but runs ten times slower than expected. The culprit is the narrow PCIe bus separating the Intel Xeon or AMD EPYC processor from the GPU.

---

Instead of licensing x86, NVIDIA built Grace around the Armv9 architecture. Each socket integrates 72 high-performance Arm Neoverse V2 cores linked by a high-bandwidth on-die mesh called the Scalable Coherency Fabric. All 72 cores feed data loaders, tokenizers, and network rings without legacy x86 decode overhead.

---

A GPU is only as fast as the data it receives. The design goal for Grace is that the CPU should never be the bottleneck when it shovels data to the GPUs. Grace can stream data from storage. It can also run on-the-fly transforms such as tokenization or data augmentation, then feed the results to the GPUs over NVLink-C2C. If part of the workload suits a CPU better, the Grace cores can handle it and leave the results where the GPUs can read them at once.

---

The two chips complement each other. The CPU covers the work GPUs do poorly, such as random memory access and control-heavy code. The GPUs handle the number crunching that a CPU cannot keep up with. The low-latency link also lets them trade tasks cheaply. Launching a GPU kernel from the CPU is much faster here, because the command does not cross a slow PCIe bus. It is similar to calling a fast local function instead of a slow remote one.

---

## FILE docs/part-09-nvidia-systems/05-gb200-and-gb300-nvl72-rack-scale-systems.md

The NVIDIA GB200 NVL72 and DGX GB300 NVL72 solve that problem by changing the fundamental unit of computing. The rack, rather than the individual server, is now the computer. NVIDIA disaggregates the Grace CPUs and Blackwell GPUs across 18 compute trays. It links them through 9 NVLink switch trays over a passive rear copper backplane. That backplane delivers 130 TB/s of aggregate NVLink 5 bandwidth so the entire liquid-cooled rack operates as a single NVLink domain. On that same MoE benchmark, moving onto an NVL72 rack multiplies per-GPU throughput by more than thirty times and cuts first-token latency to 50 milliseconds.

---

Therefore, every tray in an NVL72 rack separates front-aisle serviceability from rear-panel blind mating. All optical or copper network cables and NVMe drives are serviced from the front cold or hot aisle, while liquid cooling, DC power, and NVLink 5 connections blind-mate automatically at the rear.

---

Inside the rack, power is distributed to each 1U compute node, where AC is converted to DC for the local electronics. Each node holds two Grace Blackwell Superchips, which together draw on the order of 6 kW. Eighteen nodes draw about 110 kW. The NVSwitch trays, network switches, air cooling, and water cooling pumps add about 20 kW, for a total of 130 kW.

---

Multi-Instance GPU (MIG) goes one level deeper. It splits a single physical GPU into smaller GPUs, partitioned in hardware. A Blackwell GPU with 180 GB of usable memory can be cut into smaller pieces that each run a small inference job at the same time. Each Blackwell GPU supports up to seven fully isolated MIG instances, each with dedicated memory and SMs. MIG sizes are fixed by product generation.

---

## FILE docs/part-09-nvidia-systems/06-dgx-superpod-concepts-scalable-units-fabrics-and-tiers.md

Cutting corners on switch counts, rack space, or cable runs during initial deployment leads to expensive outages when the cluster expands. A partial build that shrinks the switch layer forces a full cluster re-cabling event later, while optical patch panels introduce signal reflections that drop high-speed InfiniBand links.

---

A DGX SuperPOD solves this by deploying two physically and logically separate storage systems. System 1 is High-Performance Storage, or HPS, which is a resilient, POSIX-compliant parallel file system from a certified DGX Storage Program partner such as WEKA, VAST, Lustre/DDN, or IBM Storage Scale / GPFS. Compute trays access HPS over 400 Gbps lossless RoCEv2 from each tray's dedicated BlueField-3 storage port. HPS requires native RoCEv2 RDMA, GPUDirect Storage, and explicit certification for Grace-based `aarch64` systems. It also requires transparent read and write caching across local system RAM and local E1.S or U.2 NVMe flash, along with non-disruptive upgrades.

---

Depending on whether your AI factory runs compute-dominated text LLMs or I/O-intensive multimodal pipelines, `superpod-gb300-ra` specifies two High-Performance Storage throughput tiers. In the table below, linear scaling per Scalable Unit is my inference generalizing the 1-SU and 4-SU rows of the reference architecture table.

---

As the financial breakdown below demonstrates, hardware amortization and cluster utilization dominate electricity in token economics. On a 40-GPU H100 inference cluster, electricity accounts for less than a tenth of the total cost per million tokens at full utilization, and total unit cost more than doubles when utilization drops to 40%. Keeping GPUs busy via Mission Control, Run:ai bin-packing, and fast checkpoint recovery is worth far more than any electricity discount.

---

## FILE docs/part-09-nvidia-systems/07-dgx-b200-superpod-data-center-design-power-cooling-cabling-and-layout.md

For example, on a traditional dual-corded enterprise server, plugging half the power supplies into PDU A and half into PDU B increases uptime. On a DGX B200, that exact same dual interleaved wiring is a serious mistake that is not recommended by NVIDIA. Because a DGX B200 requires at least five of its six internal PSUs energized to operate, losing either PDU in an interleaved rack drops three PSUs on every server and crashes the entire rack. Similarly, spacing racks farther apart to dilute a dense heat plume can push InfiniBand cable runs past the physical reach of copper or optical cables. Mastering the balance across Power, Cooling, and Space while aligning facility, IT, network, and application teams is mandatory before a single crate arrives on the loading dock.

---

In the table above, a single asterisk denotes the power factor assumption, and a double asterisk denotes a two-circuit power provisioning scheme. Look closely at the Stranded Capacity column. If your facility installs two 415V 32A circuits with fully rated breakers, you can still only power two DGX B200 nodes in that cabinet. Three nodes would exceed half-circuit symmetry across the two feeds, leaving 15.1 kW of stranded capacity per rack. Matching your breaker amperage and derating to the two-node or four-node demand minimizes stranded facility power.

---

Now examine the 14.3 kW DGX B200. A DGX B200 also has six internal Power Supply Units, but five of the six PSUs must be energized for the system to operate. That architecture provides N+1 internal PSU redundancy, so the node can survive the loss of only one internal PSU. If more than one PSU is de-energized, leaving four or fewer supplies active, the DGX B200 shuts down immediately regardless of upstream power redundancies.

---

Because each DGX B200 pulls over two thousand cubic feet per minute of supply air through its heatsinks at sea level, a two-node or four-node rack moves a massive air volume. Both the temperature and humidity envelope and the particulate cleanliness of that air stream must be strictly controlled.

---

## FILE docs/part-09-nvidia-systems/08-gb300-superpod-reference-architecture.md

Scaling a traditional 64-port switch fabric past two thousand GPUs forces architects to add a third tier of core switches. That extra core tier increases optical cable cost, latency, and power consumption. Network engineers and distributed training users feel this penalty when collective operations cross extra switch hops and job completion times stretch out. Raising the switch port radix allows the GB300 SuperPOD to scale to sixteen Scalable Units in a simple two-layer leaf-spine fat-tree without needing a third core tier.

---

Combining high-speed storage reads with bursty cluster management traffic on a poorly sized Ethernet network causes checkpoint stalls and unreachable management nodes. Storage administrators and security engineers feel this impact when a multi-rack checkpoint write saturates oversubscribed switch uplinks or when unauthenticated building controllers gain direct reachability to server BMCs. Separating host ports, sizing storage leaves for non-blocking throughput, and enforcing strict border routing solves all three problems.

---

1. **Out-of-Band Network.** The OOB network connects all compute-tray BMCs, BlueField BMCs, NVSwitch COMe and BMC ports, storage and network gear, and rack PDUs onto 48-port 1 GbE copper SN2201 switches. In the GB300 SuperPOD, each SU's OOB switches roll up into the aggregation layer as a dedicated VXLAN terminated on a pair of OOB aggregation spine switches. This design creates a physically independent IPMI, Redfish, and fabric-management plane.
2. **Customer Edge Uplink.** The customer edge handover requires at least two 100 GbE links with DR1 single-mode optical transceivers to handle high-speed dataset ingestion and corporate access. It uses a dedicated VTEP for uplink and hands over routes to the customer edge via external BGP peering. The border session announces routes to and from In-Band, Out-of-Band, and the Building Management System.
3. **BMS security zone rule.** The Building Management System provides data-center-scale power and cooling telemetry to Mission Control. It is required to flow through the customer edge uplink interfaces as part of the untrusted zone.
4. **Two options for OOB customer uplink.** In the default Dedicated OOB Uplink design, the last pair of SN2201 OOB switches acts as the OOB edge ToR switches. That pair provides a dedicated physical uplink to the customer's OOB management network. In the alternative In-Band Spine Route Leaking design, the customer chooses not to provision a dedicated OOB link. Instead, the OOB switches connect to the SN5600D In-Band spine network, and routes to the OOB interfaces are leaked toward the customer edge over the eBGP uplink.

---

Operating thousands of liquid-cooled GPUs manually means a single degraded tray or stuck rank can halt a multi-node training job for hours until an on-call engineer intervenes. Site reliability engineers and ML teams lose valuable compute hours when hardware telemetry, fabric alerts, and job schedulers live in disconnected silos. Automating fault isolation and placing orchestration services on the right Kubernetes clusters eliminates manual triage.

---

## FILE docs/part-09-nvidia-systems/09-compute-storage-in-band-and-out-of-band-networks-in-a-superpod.md

Wiring all eight compute NICs of a multi-GPU server into a single Top-of-Rack switch like a traditional web server creates a single point of failure and wastes intra-node NVLink locality. When that local switch reboots or fails, the entire server drops out of the training job. Understanding how GPUs inside a node cooperate with GPUs across nodes explains why AI factories wire NICs by rail instead of by rack.

---

When cluster provisioning, user home directories, and external container registries share a single interface with high-rate RDMA storage, a spike in user logins or container downloads can disrupt storage latency. Cluster administrators and end users need a dedicated management highway that handles boots, schedulers, and external border routing without touching the lossless storage lane.

---

Every rack in a DGX SuperPOD contains NVIDIA SN2201 48-port 1 GbE RJ45 copper switches that connect the management ports of every hardware component:
1. **DGX Compute Tray BMCs.** Each tray provides a 1 GbE RJ45 port for Redfish and IPMI management.
2. **BlueField-3 DPU BMCs.** Dedicated ports provide independent out-of-band management for the DPU cards.
3. **NVLink Switch Tray management interfaces.** Each switch tray connects both its single RJ45 BMC module port and its two RJ45 COMe ports running NVOS, which are used by NMX-M and BCM firmware updates.
4. **DGX Power Shelf BMCs and smart Rack PDUs.** Each of the eight power shelves per GB300 rack connects its front 1 GbE RJ45 BMC port and rear RJ45 power-brake management ports alongside smart rack PDUs.
5. **Fabric switch and storage management ports.** The OOB switches also connect InfiniBand Q3400-RD or QM9700 switches, Ethernet SN5600D switches, management servers for BCM, UFM, and Mission Control, and partner storage controller BMCs.

---

To avoid a sprawling flat Layer-2 broadcast domain across eight to 128 racks, each Scalable Unit's SN2201 OOB switches roll up as a dedicated VXLAN. That VXLAN terminates on a pair of OOB Aggregation Spine switches. As detailed in Chapter 9.8, Section 4.3, the OOB fabric hands over to the customer's corporate OOB network in one of two ways. The default handover uses the last pair of SN2201 switches as dedicated OOB edge ToR uplinks, while the alternative leaks routes through the SN5600D In-Band spine layer across the eBGP border VTEP.

---

## FILE docs/part-09-nvidia-systems/10-basepod-and-smaller-deployments.md

Second, you must partition expensive GPUs safely across multiple users and jobs. Administrators need clear rules for choosing Multi-Instance GPU hardware isolation versus Multi-Process Service spatial sharing or simple time-slicing. Using a software sharing mode across untrusted tenants exposes shared physical memory. One faulty kernel can then crash every neighbor on the device.

---

A DGX BasePOD of two to sixteen nodes is like operating a regional airport inside existing enterprise hangars. It introduces a single control tower running Base Command Manager with Slurm or Kubernetes. It also uses a single runway layer of leaf-only switches and a shared fuel depot of centralized flash storage.

---

A DGX SuperPOD of 32 or more nodes is like building an international hub airport from bare ground. It requires dedicated utility substations, liquid-cooling distribution units, and multi-tier leaf-spine air-traffic control with UFM and NMX-M. It also needs automated recovery software because hardware faults occur daily at thousand-GPU scale.

---

Treating two to sixteen nodes as the practical envelope of a spine-less BasePOD or leaf-only pod before transitioning to a multi-tier SuperPOD in `select_deployment_archetype` is my inference. It combines the two-to-eight node BasePOD onboarding range in the interview guide with the eight-to-sixteen node leaf-only pod architecture in Volume 21.

---

## FILE docs/part-09-nvidia-systems/11-power-delivery-thermal-design-and-liquid-cooling.md

Tier 2 consists of smart rack power distribution units. These metered units monitor per-phase inlets and locking per-receptacle outlets. They export SNMP and Redfish telemetry such as `PowerWatts`, `LineInputVoltage`, and `CurrentAmps` into Prometheus and provide remote outlet switching for full AC power cycles.

---

Even when a rack has plenty of electrical power, insufficient airflow or reversed switch fans will quickly shut down training jobs. If cold supply air cannot absorb the heat generated by the servers and front-panel optical transceivers, component temperatures climb past their thermal slowdown thresholds.

---

When cooling equipment with air, engineers must calculate how many cubic feet per minute of cold air must pass through the servers. That airflow must carry away the heat load for a target air temperature rise between the front intake and rear exhaust. The standard sensible-heat airflow formula implemented in `calculate_sensible_heat_airflow_cfm` relates heat load in watts to airflow volume and temperature rise.

---

If a facility team assumes that a liquid-cooled NVL72 rack dumps zero heat into the room air, the data hall will quickly overheat. The DGX GB300 SuperPOD Reference Architecture describes the DGX GB300 NVL72 rack as a hybrid cooling solution because cold plates do not cover every tiny component on the board.

---

## FILE docs/part-09-nvidia-systems/12-software-stack-and-management-in-an-ai-factory.md

An AI factory filled with thousands of liquid-cooled GPUs and fast InfiniBand switches is inert silicon until the software stack binds it into one coherent machine. If a researcher launches a standard single-process Python script on a fifty-million-dollar cluster, the job runs on one CPU core. The rest of the factory sits idle. Worse, if one node in a multi-node job boots with an older kernel driver or a mismatched PCIe device order, the whole run stalls. The same hang happens when a plain Kubernetes job places all pods except one, leaving the cluster stuck until a communication timeout kills the job thirty minutes later.

---

1. Cluster provisioning, firmware, and fabric management run through NVIDIA Mission Control, Base Command Manager, UFM Enterprise, and NMX-M. Together, they keep every compute tray, NVLink switch tray, and InfiniBand switch on an identical golden image and firmware matrix with automated node draining and self-healing.
2. Host kernel driver and containerized CUDA runtime alignment matches the host OS `nvidia.ko` driver branch to the user-space libraries. Those user-space libraries include the CUDA toolkit, cuDNN, and NCCL bundled inside pre-validated NVIDIA NGC containers.
3. Distributed framework and memory sharding layers include PyTorch DDP, DeepSpeed ZeRO, Megatron-Core, and DLPack. They shard model weights, gradients, and Adam optimizer states across worker ranks launched by `torchrun`.
4. Gang-scheduled workload orchestration runs through Slurm, Kubernetes operators, Kueue, Volcano, or NVIDIA Run:ai. It guarantees that all ranks of a multi-node job are placed and started at the exact same moment.
5. SLO-driven observability and incident response stacks built on DCGM, Prometheus, and Grafana scrape true hardware pipeline activity. They page on-call engineers before thermal slowdown or stragglers breach service commitments.

---

1. NVIDIA Base Command Manager is the bare-metal foundation built around CMDaemon and `cmsh`. It provisions compute nodes from immutable golden software images under `/cm/images/<image>` and tracks physical rack and chassis slot coordinates. It also flashes compute-tray and switch-tray firmware via `cm-nvfwupd` version 2.1.2 and executes autonomous recovery by draining unhealthy nodes and requeuing interrupted jobs, as covered in Chapters 8.5 and 8.16.
2. NVIDIA Unified Fabric Manager Enterprise is the appliance that manages the scale-out Compute InfiniBand Fabric on Quantum-2 NDR or Quantum-X800 Q3400-RD XDR switches. It configures Subnet Manager partitions, Adaptive Routing, SHARPv3 trees, SHIELD self-healing, and predictive cable or transceiver failure analytics.
3. NVIDIA Network Manager eXperience manages the scale-up Multi-Node NVLink switch trays running NVOS. It provides real-time NVLink telemetry and partition control across the 72-GPU rack domain.
4. NVIDIA Mission Control is the unified five-layer operations umbrella built on top of BCM, UFM, NMX-M, and the facility Building Management System. It delivers automated failure detection, self-recovery, workload migration, unified infrastructure and application diagnostics, and in-memory checkpointing.
5. Slurm and NVIDIA Run:ai provide the two workload scheduling paradigms. Slurm handles batch multi-node training. NVIDIA Run:ai provides cloud-native Kubernetes GPU orchestration across the user-space and administrative Kubernetes clusters described in Chapter 9.8 Section 6.1.
6. NVIDIA AI Enterprise and NGC provide the commercial enterprise support boundary and pre-tested NGC framework containers such as `nvcr.io/nvidia/pytorch:*`. They also include NeMo and Megatron-Core for 3D-parallel training alongside NVIDIA NIM microservices for production inference.

---

When you launch a 64-GPU training job across 8 nodes with 8 GPUs per node, you do not SSH into 8 servers and start 64 Python processes by hand. You also do not use the deprecated `torch.distributed.launch` utility. Instead, you use `torchrun` with the `c10d` rendezvous backend.

---

## FILE docs/part-09-nvidia-systems/13-sizing-and-capacity-planning-exercises.md

When executives ask what it actually costs to serve a million tokens or expand a GPU fleet over three years, rough hardware sticker prices give the wrong answer. A defensible TCO model must amortize staggered server purchases across active GPU-years and account for fixed depreciation and staffing costs when diurnal traffic drops below peak.

---

Why does the cost per million tokens jump from $0.70 to $1.74 when average diurnal traffic drops to 40% of peak? Hardware amortization and FTE salaries are fixed daily costs that dominate electricity. Because fixed costs do not shrink when traffic dips overnight, a 2.5x drop in average utilization drives the real cost per million tokens up by 2.5x.

---

When a startup grows its user traffic by 15% a month and its training runs by 20% a month, a simple spreadsheet forecast quickly outruns the physical electrical breakers of the data hall. Because enterprise GPU orders take three to nine months to arrive, architects must pair lead-time reorder triggers with hard facility power ceilings.

---

This chapter's self-checking Python model in `code/part09/capacity_planning.py` and lab script in `code/part09/capacity_planning_lab.py` implement five verification checks.
- The Effective Capacity and Cost per Million Tokens Calculator verifies the inference fleet economics at full load and diurnal average load.
- The FinOps Zombie Reaper Bot Evaluator and MIG Reclamation Check verify pod eviction thresholds and logical GPU slicing across the staging node pool.
- The First-Fit Decreasing GPU Job Bin-Packer and Spot versus On-Demand Savings Calculator verify node packing and annual cloud savings.
- The Multi-Year Fleet TCO and GPU-Year Amortizer verifies the staged refresh and the large AI factory unit economics.
- The Seasonal and Multi-Year Demand Forecaster detects the facility power wall and compares exponential growth against the saturating logistic S-curve.

---

## FILE docs/part-09-nvidia-systems/14-cloud-gpu-platforms-dgx-cloud-coreweave-nebius-and-gcp-a3-and-a4.md

Building an on-premises AI factory takes months of facility construction and multi-megawatt utility power contracts. Even teams that own physical SuperPODs regularly need elastic burst capacity for urgent training deadlines. As a result, infrastructure engineers spend much of their time deploying and operating workloads across cloud GPU platforms.

---

This chapter shows how three major cloud GPU platform archetypes expose bare-metal hardware performance. You will examine NVIDIA DGX Cloud, GPU-native neoclouds like CoreWeave and Nebius AI Cloud, and Google Cloud GPU machine families. Along the way, you will learn how PCIe passthrough, BCM Topograph topology discovery, and multi-NIC RDMA fabrics keep cloud clusters running at line rate.

---

1. **Host maintenance termination:** Compute Engine VMs with attached GPUs cannot live-migrate during physical host maintenance events. You must set `on_host_maintenance = "TERMINATE"` and rely on your scheduler and checkpoints to restart interrupted jobs.
2. **Compact collocation placement:** Attach a `google_compute_resource_policy` with `collocation = "COLLOCATED"` to multi-node training pools. This policy places VMs on adjacent physical switches and satisfies the GCP requirement for BCM Topograph.
3. **Capacity acquisition modes:** Use `google_compute_reservation` with `SPECIFIC_RESERVATION` affinity for guaranteed continuous capacity. For queued batch jobs on GKE, integrate Dynamic Workload Scheduler with Kueue `ProvisioningRequest` in Flex-Start or Calendar mode so all nodes of a job allocate atomically at once.
4. **GKE node pool upgrade guardrail:** Default GKE surge upgrades try to boot an extra GPU node before draining an existing one. When your quota or reservation is completely full, the upgrade hangs forever. Always set `max_surge = 0` and `max_unavailable = 1` with `auto_upgrade = false` so GKE drains and upgrades nodes in place during maintenance windows.
5. **Single driver manager rule:** Let GKE install the NVIDIA driver and set `driver.enabled=false` in the NVIDIA GPU Operator, or disable the GKE installer and let the GPU Operator manage `nvidia.ko`. Never enable both driver managers on the same node pool.

---

1. Run `python3 -B code/part09/cloud_gpu_platforms_lab.py`. Pick the Topograph checks for AWS, OCI, and GCP and write the specific permission or placement setting that must be present for each cloud.
2. Write the two-step plan to upgrade a BCM 11.34 cloud cluster from `topograph` to `topograph4`. State what you check afterwards and what failure occurs if you skip one step.
3. Sketch the SR-IOV data path of a ConnectX Virtual Function into a guest VM. Mark the Physical Function, the Virtual Functions, the IOMMU, and what a legacy `virtio` path would add.
4. A Nebius training job runs at under 5 GB/s bus bandwidth. List the three checks you would run and the Terraform change that fixes the most likely root cause.
5. Choose a GCP machine family for a 7B inference service, a 70B training run on H100, a 70B training run on B200, and a rack-scale NVL72 run. Name the inter-node network transport for each choice.
6. Write the GKE node pool upgrade settings for a pool that has zero spare GPUs in its reservation, and explain each parameter.

---

## FILE docs/part-13-ai-storage/01-the-ai-data-path-from-storage-to-gpu.md

A GPU that sits idle waiting on a data loader or a stalled checkpoint costs the same hourly rate. So does a GPU waiting on a broken collective. Still, storage is routinely sized by two numbers from a vendor datasheet: total usable terabytes and peak sequential bandwidth.

---

Every one of those eight boundaries has a per-operation latency and an aggregate bandwidth ceiling, so any of them can become the slow link. This chapter maps the five AI storage workload phases across the four-tier storage hierarchy. It contrasts the traditional POSIX CPU bounce-buffer path with GPUDirect Storage direct DMA. You will also work through the bandwidth scaling math from one GPU to a full rack, and learn which commands isolate a storage bottleneck.

---

As you read the table, you will see that each tier trades capacity for speed. Tier 0 is the fastest and smallest, and Tier 3 is the largest and slowest. The table lists what each tier is built from and what it is used for.

---

1. **Benchmarking AI storage with 4 KB random OLTP profiles or cached files smaller than host RAM.** Suppose you run `fio` with a 10 GB test file on a node with 256 to 2,000 GB of RAM, and you leave out `--direct=1`. The result measures DDR5 page cache bandwidth, which tops 50 GB per second. It does not measure storage throughput. Always set `--size` larger than host RAM, or pass `--direct=1` with 1 MB to 8 MB block sizes that match dataset reads and checkpoint writes.
2. **Leaving `/dev/shm` at the 64 MiB container default.** Multi-worker PyTorch data loader pipelines with `num_workers=8` and `prefetch_factor=4` allocate tens of gigabytes of shared memory in `/dev/shm`. On eight-GPU nodes, mount a memory-backed `emptyDir` with `sizeLimit: 400Gi` at `/dev/shm`.
3. **Assuming GPUDirect Storage is active without checking `/proc/driver/nvidia-fs/stats`.** The default in `/etc/cufile.json` is `"allow_compat_mode": true`. A misconfigured mount or an unsupported FUSE filesystem then falls back to CPU bounce-buffer copies without a warning. Your job keeps running, only slower, and nothing raises an error.
4. **Treating local RAID 0 NVMe scratch as durable storage.** Node-local NVMe has no cross-node replication. If a compute node fails, any checkpoint staged only on local NVMe is lost until it is flushed to shared parallel storage or object storage.
5. **Using `num_workers=0` in production or forgetting `persistent_workers=True`.** Setting `num_workers=0` is a useful temporary diagnostic, because it isolates pure Python transform time. In production, though, it serializes file reads with GPU execution. Forgetting `persistent_workers=True` makes worker processes respawn and re-initialize file handles at the start of every epoch.

---

## FILE docs/part-13-ai-storage/02-local-nvme-and-data-staging.md

Caching the dataset on local NVMe changes every epoch after the first. Once the data lives on `/raid`, the data loader reads it back at 3.5 GB per second sustained. That is about 1.75 GB per second for each GPU, comfortably above the 120 MB per second each GPU needs. Epoch time drops from 245 seconds to 200 seconds. That saves 45 seconds per epoch, an 18 percent speedup. Over a ten-epoch run, inline caching saves 405 seconds in total, which cuts run time by about 16.5 percent.

---

The second bug is silent staleness. Suppose an upstream pipeline updates a shard on shared storage. A node's `/raid` cache still holds last week's copy under the same filename. Training then quietly mixes old and new data across nodes, and no error is raised. The fix is to store a SHA-256 hash and byte size for every cached file in a `manifest.json`. Then check that hash before you trust a cache hit.

---

Modern Linux sends NVMe I/O through a multi-queue block layer. It maps one submission queue per CPU core directly onto the NVMe hardware queues. The older design funneled every request through one lock-contended queue, which is how legacy SATA drives worked.

---

1. Compare the DGX H100 and H200 two-tier drive layout with a DGX GB200 and GB300 NVL72 compute tray. Work out the usable scratch capacity per node or tray, and across an eighteen-tray rack. Explain why `/raid` uses RAID 0 while the OS tier uses RAID 1. Next, compute the full stripe width, `sunit`, and `swidth` for the eight-drive DGX H100 array and the four-drive GB200 array. Finally, give the percentage of drives that a single 64 KB read activates, and the percentage that a 4 MB read activates.
2. Work through a 500 GB dataset of two million files that trains on a node with 2 TB of local NVMe. Cold Lustre epochs take 245 seconds, and warm NVMe epochs take 200 seconds. Under inline cache fill on the first epoch, calculate the total wall-clock time for ten epochs with and without local NVMe. Include the seconds saved and the net percentage speedup. Then take explicit pre-staging at 2.0 GB per second. Compute the copy time and the exact break-even epoch count. Finally, find the net time gained or lost on a three-epoch run and on a six-epoch run.
3. A distributed job writes a 500 GB checkpoint. Shared Lustre sustains 1.2 GB per second, local NVMe sustains 3.5 GB per second, and the asynchronous handoff acknowledges in one second. Compute the synchronous write stall time directly to Lustre, the local NVMe write duration, and the critical-path speedup from asynchronous staging. Then find the minimum safe interval in seconds between consecutive checkpoints, so the background flush finishes before the next checkpoint fires.
4. Suppose `fio` on `/dev/md0` measures 3.5 GB per second of sequential read. Yet the PyTorch training loop achieves only 150 MB per second, and the GPUs sit at 65 percent utilization. Inspection shows the blk-mq scheduler set to `bfq`, a queue depth of 128, read-ahead at 128 KB, `/raid` mounted with `relatime`, and workers on the wrong NUMA node. List all five misconfigurations. Write the Linux command that fixes each one for sequential shard streaming. Then explain how `read_ahead_kb` should differ for random `O_DIRECT` reads. Finally, state the `gdsio` improvement when you switch from CPU mode to GPUDirect Storage.
5. Each of the eight U.2 drives in a DGX H100 `/raid` array holds 3.84 TB and is rated at 1.0 DWPD over five years. Compute the lifetime TBW rating for one drive and for the eight-drive array. Find the effective daily NAND writes, effective DWPD, and lifespan for 2.5 TB per day of host writes at a WAF of 1.2. Then repeat that calculation for 15.0 TB per day of checkpoint traffic striped across all eight drives. Finally, state the alert thresholds for `percentage_used`, `available_spare`, `temperature`, and `media_errors`.
6. A DGX H100 `/raid` array has 30,720 GB of usable space and enforces an 85 percent maximum safe fill ceiling. Compute the maximum safe allocatable scratch capacity in gigabytes. Explain why a new 16,000 GB job fails admission when a killed 12,000 GB job leaves an orphan behind. Then show how an orphan-sweep step in Prolog plus a cleanup step in Epilog resolves that admission. Calculate the fill percentage during and after the second job runs.

---

## FILE docs/part-13-ai-storage/03-gpudirect-storage-architecture.md

GPUDirect Storage removes the host DRAM bounce buffer. It is part of the NVIDIA Magnum IO stack, alongside GPUDirect RDMA. The user-space cuFile library works with the nvidia-fs.ko Linux kernel driver. Together they program the local NVMe drive or RDMA storage NIC to move blocks directly into and out of GPU BAR1 memory across a shared PCIe switch.

---

On paper, eliminating the CPU bounce buffer cuts copy latency in half and boosts sustained throughput by 20 to 30 percent. In production, those gains appear only when five conditions hold at the same time. Miss one, and the gain can vanish.

---

The cuda-checkpoint tool is different. It works alongside CRIU, which stands for Checkpoint and Restore in Userspace, to pause and migrate whole running CUDA processes. It calls `cuCheckpointProcessLock`, `cuCheckpointProcessCheckpoint`, `cuCheckpointProcessRestore`, and `cuCheckpointProcessUnlock`. During a process suspend, the CUDA driver drains in-flight GPU work and copies the GPU memory image into host DRAM, so CRIU can snapshot the process. It does not DMA directly from GPU HBM to disk through GDS.

---

1. Work out the model-weight fetch. A 100 MB model shard takes 100 microseconds of raw storage read latency. Compare the CPU-bounce path at 3,000 MB per second with the GDS direct DMA path at 6,000 MB per second. Calculate the copy or DMA time, the total fetch time, and the copy speedup factor. Then average the five Lab 03 CPU-bounce trials against a 960 MB per second GDS read rate, and decide whether the gain clears the 20 percent deployment threshold.
2. Trace the cuFile lifecycle and path resolution. Use `validate_cufile_lifecycle()` and `resolve_gds_execution_path()` in `code/part13/gpudirect_storage_arch.py` to find the execution path in five cluster scenarios. For each one, say whether `/proc/driver/nvidia-fs/stats` increments and whether `__memcpy_avx2` runs. The scenarios are a healthy WekaFS PIX setup, a Lustre PHB setup, a standard `torch.load` call, a FUSE mount with compatibility mode enabled, and a node missing nvidia-fs.ko with compatibility mode disabled.
3. Do the alignment math. A worker calls `cuFileRead` with an unaligned file offset, transfer size, and GPU buffer address. Show why all three coordinates fail the 4 KiB check. Then calculate the rounded-down start offset and the rounded-up read size that cover the byte range. Finally, compute the realigned offset and size for a 4,096-byte offset when a Lustre OST enforces 8 KiB alignment.
4. Compare gdsio modes. Compare gdsio mode `-x 2` with mode `-x 0` on a 10 GiB read test. Calculate the percentage throughput gain, the latency reduction, and the drop in host CPU utilization. Then compute the CPU I/O efficiency, in GB per second per 1 percent of CPU, before and after you enable GDS.
5. Audit a configuration file. Audit a `/etc/cufile.json` for a 1 MiB training workload, where compatibility mode, poll mode, and unaligned POSIX fallback are all enabled. Convert `max_device_pinned_mem_size_kb` to GiB, name all three configuration defects, and write the hardened settings.
6. Size a Blackwell pipeline and the 3FS cluster. A Blackwell B200 node reads a 4.0 GB batch compressed 2.5x with LZ4 over a 50 GB per second GDS link. It unpacks the batch with the 800 GB per second Hardware Decompression Engine. Compute the uncompressed read time, the compressed read time, the hardware unpack time, the combined serial time, the effective throughput, and the speedup factor. Then calculate the total drives, the raw capacity, the combined read throughput, and the speedup over Ceph for DeepSeek's 68-node 3FS cluster.

---

## FILE docs/part-13-ai-storage/04-lustre-for-ai.md

The second failure comes from default striping. Lustre gives new directories a stripe count of one. A multi-hundred-gigabyte checkpoint written into an untuned directory therefore serializes the whole dump onto a single OST. That bottleneck freezes training for over ten minutes, when the same dump could finish in seconds across all targets. The reverse problem exists too. When dozens of ranks write unaligned byte ranges into one shared file, the Lustre Distributed Lock Manager thrashes extent locks and cuts throughput by fourfold.

---

Wide striping adds metadata and lock overhead for small files. Creating a file, statting it to find its size, or unlinking it with $C$ stripes means managing $C$ child OST objects plus the MDT inode. So the stripe layout and the metadata layout have to be designed together. Progressive stripe layouts and distributed metadata go hand in hand.

---

Lustre Networking hides the underlying fabric behind pluggable drivers, called Lustre Network Drivers. The kernel TCP driver `ksocklnd` uses TCP port 988. Keep that port open in host and datacenter firewalls for management fallback. TCP becomes CPU-bound at 400 Gbps line rates, so production AI data planes use RDMA instead. The native RDMA Verbs driver `ko2iblnd` runs over both InfiniBand and RoCEv2 Ethernet. Each protocol name and number forms its own isolated LNet subnet. A client on `@o2ib0` talks directly only to servers on `@o2ib0`, unless LNet routers bridge the subnets.

---

1. **PFL + DoM Object & Byte Distribution (`evaluate_pfl_dom_file`):**
   Take a directory on a 24-OST Lustre cluster with the composite layout `lfs setstripe -E 1M -L mdt -E 64M -c 1 -S 1M -E 4G -c 4 -S 4M -E -1 -c -1 -S 4M`. Evaluate three files: a 260 KiB JSON manifest, a 512 MiB WebDataset shard, and a 10 GiB checkpoint. For each file, work out how many bytes sit on the MDT through DoM, how many bytes sit on OSTs, and how many distinct OSTs hold data.
2. **Metadata Bottleneck Diagnosis and Dataset Sharding (`evaluate_lctl_metadata_stats` & `model_dne_metadata_scaling`):**
   At epoch start across 128 GPU nodes, `lctl get_param llite.lustre-1a5c.stats` runs over a 60-second window and records the saturated metrics in the inputs block. First, compute the per-second open rate, the `getattr` rate, and the average open latency in milliseconds. Compare them with the healthy thresholds. Second, suppose the dataset is repackaged as the inputs block describes. Calculate the reduction factor in `open` calls per epoch, and the total open time across 4 MDTs.
3. **DNE Phase 1 vs Phase 2 Single-Directory Trap (`model_dne_metadata_scaling`):**
   A Lustre cluster has 4 MDTs, each rated for 50,000 metadata operations per second. A vision job opens 200,000 files that sit in one directory, `/lustre/imagenet/train`. Work out the active MDT count, the aggregate metadata IOPS capacity, and the total open time under DNE Phase 1 with `lfs mkdir -i 0`. Then do the same for DNE Phase 2 with `lfs setdirstripe -c 4`.
4. **Client RPC Bandwidth-Delay Product (`calculate_client_rpc_bdp`):**
   A GPU client with a 400 Gbps RDMA NIC reads a file striped across 8 NVMe OSTs. The storage round-trip time on this congested path is 4,000 microseconds. First, use the untuned defaults to work out the per-OST RPC size, the in-flight bytes, the per-OST BDP limit, and the aggregate bandwidth across the 8 OSTs. Second, apply the tuned `max_rpcs_in_flight` and `max_pages_per_rpc` values from the parameter block, and recalculate.
5. **Checkpoint Striping & LDLM Lock Contention (`model_checkpoint_write_strategy`):**
   A 64-rank training job writes a 500 GB checkpoint. Compare three layouts: a single-OST write, an unaligned N-to-1 shared-file write across 12 NVMe OSTs, and a sharded N-to-N write across 24 OSTs. For each one, work out the effective write bandwidth and the total checkpoint stall time. Then calculate how long a 5.6 TB checkpoint takes on a 4-SU SuperPOD Enhanced tier.
6. **OST Skew Remediation, OSS RAM Sizing, and `gdsio` Verification (`audit_lnet_multirail_and_osts` & `compare_gdsio_paths`):**
   An OSS serves 6 OSTs connected to 120 Lustre clients. Use the book's sizing formulas to work out the baseline RAM per OST and the recommended total OSS RAM. Then calculate the fill skew when OST 0 is at 98% and OST 1 through OST 5 are at 60%. Write the `lfs find` and `lfs migrate` pipeline that rebalances OST 0. Last, compute the percentage throughput gain and latency reduction between `gdsio` modes `-x 2` and `-x 0`.

---

## FILE docs/part-13-ai-storage/05-beegfs-weka-vast-and-object-storage.md

The first option is BeeGFS, an open-ecosystem parallel filesystem. It splits its work into management, metadata, storage targets and kernel clients, and each piece runs as a standard Linux service. That makes it far simpler to install and run than Lustre. The trade-off is that you still have to configure directory stripe patterns yourself. Repackaging small files keeps the metadata servers from saturating above 100 GPUs.

---

For durability, WekaFS skips hardware RAID cards and 3x replication. Triple replication wastes two-thirds of raw NVMe capacity. Instead, WekaFS stripes data across failure domains with cluster-wide $N + K$ erasure coding. Here $N$ counts the data chunks and $K$ counts the parity chunks, and together they never exceed the number of storage nodes.

---

Consider what happens on a shared-nothing storage cluster when many clients write at once. Each server owns specific drives and metadata shards, so a write that spans nodes forces those servers to exchange lock and cache-coherency messages across the network. At multi-terabyte-per-second scale, that east-west coordination and the host OS page caches become the main bottlenecks.

---

As you read the table, treat it as a before-and-after pair. The first row is the bounce-buffer path, and the second row is the direct path. The throughput rises from 8.0 GB/s to 9.6 GB/s, which is the 20 percent gain, and latency drops from 1.25 ms to 1.00 ms.

---

## FILE docs/part-13-ai-storage/06-data-loading-small-files-and-metadata.md

Picture reading ten thousand single pages, each one from a different book scattered across a huge library. Every page means walking to the front desk for its call number. Then you walk to a shelf, read one page, and return the book before you can ask for the next. Most of your time goes to walking, not reading. If someone packs those ten thousand pages into one binder ahead of time, you need one lookup and then read straight through.

---

Repacking millions of files into WebDataset tar shards solves the storage side. The CPU can still become the limit. In computer vision, video, and multimodal training, CPU image decoding and augmentation can saturate every host core. In one representative object-detection pipeline that reads images and video, `top` shows host CPU use pinned at 800 percent, which is eight full cores. The GPU still shows periodic starvation gaps.

---

The location of a gap tells you the cause. Gaps at the start of every step point to DataLoader starvation. Gaps during the backward `AllReduce` point to network bottlenecks. If kernels run with no gaps but still run slowly, use Nsight Compute (`ncu`) to inspect SM utilization and memory stalls. For example, an NCCL kernel at 60 percent SM utilization, with high memory stalls over PCIe, jumps to 90 percent SM busy once it is routed over NVLink.

---

The block below holds the inputs and the expected results for all six exercises. Work each exercise by hand, then compare your answer with the target in the block. If your number differs, you will find the mistake faster by checking one step at a time.

---

## FILE docs/part-13-ai-storage/07-checkpoint-architecture-and-recovery.md

1. Calculate the exact byte footprint of a model's active training state, and compare it with the persistent mixed-precision AdamW checkpoint state across foundation model scales.
2. Instrument the three synchronous checkpoint phases, find straggler ranks with `dist.all_gather`, and compute optimal checkpoint intervals with Young's approximation and Daly's correction.
3. Design a two-stage asynchronous checkpoint pipeline that moves data from GPU HBM to pinned host DRAM, then to local NVMe and shared storage, with OOM guards and atomic directory publication.
4. Reshard a checkpoint across changing GPU world sizes with `torch.distributed.checkpoint`, and compare framework checkpoints with transparent driver-level snapshots taken through `cuda-checkpoint` and CRIU.

---

Platform engineers need to keep two memory pictures apart. One is the active, per-step training memory that lives in GPU HBM. The other is the persistent checkpoint state written to disk. Active training holds gradients during the backward pass. Checkpoints are saved at the step boundary instead, after the optimizer has updated the weights and cleared the gradients.

---

The third rule is tiered checkpoint retention. Without cleanup, a thousand checkpoints would consume half a petabyte. So an automated hook runs after every validated commit. It keeps a rolling window of the last five checkpoints for crash recovery, plus a periodic milestone every hundred epochs or steps for downstream evaluation.

---

Checkpoint problems rarely announce themselves clearly. The job either crashes with a cryptic error, or it runs on with a quietly wrong model. The table pairs each failure with the evidence to collect and the fix that has worked in production.

---

## FILE docs/part-13-ai-storage/08-capacity-performance-and-cost-planning.md

Example B shows why pruning matters. A hundred jobs that each keep twenty rolling checkpoints would need 1,000 TB, so the older copies have to move to S3 or be pruned. Before you sign off on a capacity number, add the thirty percent buffer and check the total against your usable subtotal.

---

Not every team needs the same storage speed. NVIDIA certifies partner parallel filesystems, such as DDN EXAScaler, WEKA, VAST Data, IBM Storage Scale, NetApp, and Dell, against two High-Performance Storage tiers. Each tier is defined per Scalable Unit and matched to a type of workload.

---

For the hardware, provision a twelve-node Lustre cluster. It has eight OST storage nodes, two MDS metadata nodes, one backup MDS, and one MGS management node. Using twelve-terabyte enterprise NVMe SSDs per OST provides 96 TB raw and 80 TB usable capacity.

---

The next group measures the numbers you sized earlier. Run the `fio` jobs to check read and write bandwidth, the `gdsio` pair to compare GPUDirect Storage with a CPU bounce buffer, and `strace` to count file opens. Compare the output with the figures you worked out in sections 1 and 2.

---

## FILE docs/part-13-ai-storage/09-storage-troubleshooting.md

A slow storage path is hard to diagnose during an outage if you never measured a healthy one. Think of the golden baseline as a photograph of the node on a good day. Before you launch production workloads, capture a reproducible five-minute baseline and save it as `healthy.txt`. It covers five domains: network and PCIe topology, filesystem mounts and target health, raw network versus storage bandwidth, local NVMe versus shared storage workload profiles, and host memory state.

---

When your application reads a file, the request travels a long road. It starts at the remote storage media, crosses the network fabric, passes through the client kernel filesystem and host DRAM, and finally crosses PCIe or NVLink-C2C into GPU HBM. If you know the normal latency and throughput at each stage, a broken hop stands out right away.

---

At Gate 3, you profile the job with `python -m cProfile -s cumtime train.py`, which is marked `untested here`. It shows 120,000 calls to `Image.open` taking 45.2 seconds. It also shows `augmentation.apply` taking 12.1 seconds, which totals 57.3 seconds of CPU work.

---

2. **Tell a communication-bound job from a compute-bound one.**
   - **(a)** Use the AllReduce baseline below to explain mathematically why changing the micro-batch size does not change the gradient AllReduce payload bytes.
   - **(b)** Use the halving and doubling measurements below to calculate Run B's new AllReduce share of total iteration time at double the batch size. Then classify Run A and Run B as communication-bound or compute-bound.

---

## FILE docs/part-18-security/01-threat-modeling-for-ai-infrastructure.md

STRIDE is the standard threat-modeling method, described in *Engineering AI Systems* Chapter 9. It names six threat types: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege. For AI infrastructure, each type gets an AI-specific version, as the table shows.

---

Follow one request through your platform. It arrives from the internet, passes through a load balancer, calls an internal service, loads a model image, and reads a dataset. Each step is a place where someone could act. Grouping those places gives you four attack surfaces, and each one needs its own controls.

---

Production Kubernetes, chapter 7, walks through an attacker who gets root on the API server node and then reads Secrets from etcd. The chapter then argues that an RBAC mistake or a compromised application is the more likely way a secret leaks. Use the same reasoning when you rank the threats above.

---

Track a few signals that show whether the threat model is still doing its job. Each one has an alert, so a stale model triggers a message rather than waiting to be noticed. The thresholds in the table are examples to adjust.

---

## FILE docs/part-18-security/02-hardware-and-firmware-trust.md

Chapter 18.1 listed the threats to your GPU platform. This chapter covers the controls that close the gaps at the hardware and firmware layer. A GPU cluster is a stack of hardware, firmware, drivers, and workloads, and any layer in that stack can be attacked. Your job is to confirm that the hardware is trusted before a workload runs, and then to keep checking.

---

Imagine a node that boots a modified bootloader. The machine starts, the operating system loads, and nobody notices the change until someone uses it. Secure boot is the control that catches this, because it checks every stage before that stage is allowed to run.

---

Firmware changes deserve tighter access than ordinary cluster changes. A single shared account that can both read and rewrite firmware records makes every change hard to trace. Split the rights into reader, writer, and admin roles, as the table shows.

---

The chapter treats 30 seconds as the example limit for any one answer. If an answer takes longer than that, the firmware trust is not yet ready to run as a production service. The lab is **untested** against a live GKE cluster.

---

## FILE docs/part-18-security/03-containers-and-the-software-supply-chain.md

Syft is the Anchore tool that reads a container image and writes its SBOM. It can write CycloneDX or SPDX, and this chapter uses CycloneDX. Generate the SBOM at build time, from the same image reference you pushed, so the inventory matches what runs.

---

Picture a build that installs a package named `myorg-common-lib`. Your company publishes that package on a private index. An attacker publishes a package with the same name on the public index. If the build looks at the public index too, it may pick up the attacker's copy. The build does not warn you, and the malicious code runs inside your build.

---

Before containers, teams deployed a binary, a compressed archive, or raw source code onto a server. They then made sure the server had the right dependencies and configuration. A container image packs those pieces into one artifact. It holds the application, the execution environment, and the dependencies together.

---

Static scanning is one layer of defense in depth. An image can download malicious content after it is deployed. A running container can also be hijacked. Runtime scanning addresses those risks. A simple form scans the filesystem of running containers on a schedule. A stronger form limits the actions and behaviors a container can perform, so you do not chase each new CVE. Look at Falco and the Aqua Security suite, and plan time to study runtime scanning on its own.

---

## FILE docs/part-18-security/04-kubernetes-access-control-and-pod-security.md

The access controls mark the boundary between tenants. A workload that can read another tenant's data has crossed that boundary. As the platform owner, you should enforce the boundary by default, so that crossing it needs an explicit, approved grant. When an auditor asks who can read a secret, the answer should come from these controls, not from memory.

---

1. **The platform team owns the access controls.** It writes the RBAC roles, sets the Pod Security Standards, and manages the secrets. When a control drifts, the platform team is the one that has to fix it.
2. **Tenants expect their data to stay private.** The platform team must enforce that privacy by default. It cannot rely on each team to configure it correctly.
3. **Secrets need the same care.** API keys, database passwords, and model signing keys are all secrets. You have to store them safely, rotate them, and keep a record of their use.

---

1. Write least-privilege Roles and RoleBindings for each namespace.
2. Use Workload Identity to link Kubernetes ServiceAccounts to cloud IAM roles.
3. Set Pod Security Standards to "restricted" and refuse privileged pods.
4. Write NetworkPolicies that deny by default and allow only what each workload needs.
5. Manage secrets with Vault or External Secrets Operator, and rotate them automatically.
6. Run these controls on GKE, with ongoing checks, secret rotation, and incident response.

---

The first Ingress is denied, because its host does not match the regex. The second Ingress is admitted, because its host matches. Test a policy like this with one passing object and one failing object before you rely on it.

---

## FILE docs/part-18-security/05-gpu-sharing-security-dma-iommu-and-sr-iov.md

Chapter 18.4 checked who can reach the cluster. This chapter checks what a workload can reach once it is running on a GPU. A GPU reads system memory directly through DMA, which stands for Direct Memory Access. When two tenants share a GPU, that direct access is the path you have to contain.

---

On modern hardware, the IOMMU is enabled by default, so the real work is watching it. You verify it on every node, monitor its translations, and respond when faults appear. A page fault is a signal to investigate, not noise to ignore.

---

NVIDIA applies the same idea to GPUs through vGPU. Each tenant gets a virtual GPU that its workload sees as a separate device. The partitions are created once, at boot, and the GPU device plugin then hands them to workloads.

---

1. **Add an IOMMU enforcement alert.** Write an alert that fires whenever a node's IOMMU is disabled, so the gap never goes unnoticed. *Solution sketch:* a Prometheus exporter for the IOMMU state, plus an alert that fires when the state is not "enabled".
2. **Add a MIG partition enforcement alert.** Write an alert that fires when a MIG partition is not enforced. *Solution sketch:* a Prometheus exporter for the MIG state, plus an alert that fires when the state is not "enforced".
3. **Add a GPU memory anomaly alert.** Write an alert that fires when GPU memory access looks anomalous. *Solution sketch:* a Prometheus exporter for GPU memory, plus an alert that fires when the pattern is anomalous.
4. **Add a per-workload GPU sharing mode policy.** Decide which workloads use time-slicing, MIG, or SR-IOV, and write the rule down. *Solution sketch:* a policy document, plus a Kubernetes admission controller that enforces it.
5. **Add a GPU sharing security dashboard.** Build a Grafana dashboard that shows the IOMMU state, the MIG partitions, the SR-IOV VFs, and the GPU memory metrics. *Solution sketch:* a Grafana dashboard with those panels and their data sources.
6. **Add a GPU memory scraping incident response runbook.** Write the steps for responding to a GPU memory scraping attack, along with the escalation contacts. *Solution sketch:* a Markdown runbook with the response steps and the contacts.

---

## FILE docs/part-18-security/06-bluefield-doca-and-confidential-computing.md

This chapter covers the design that gives that proof. A BlueField DPU (Data Processing Unit) runs security work on its own processor, away from the host CPU. A confidential VM encrypts the workload's memory and registers. An attestation chain lets a remote verifier check that the stack started the way you approved.

---

Imagine a cloud host where the operator has root access. Normally that operator can read the memory of any VM on the machine. A confidential VM (CVM) closes that gap by encrypting its memory and registers with a key that only the VM holds.

---

The remote verifier is the service that decides whether the chain is valid. It runs off the cluster and holds the public keys for the TPM, the DPU, and the CVM. Keeping it separate means a compromised node cannot vouch for itself.

---

Work through this lab in order. It checks each layer of the high-assurance stack on GKE: the BlueField DPU, the DOCA services, the confidential VM, the attestation chain, and GPU CC. The lab is **untested** in this repository, so treat its commands as a plan to run, not a record of a working run.

---

## FILE docs/part-18-security/07-data-and-model-protection-audit-and-compliance.md

Data also moves. A request from a client to the model API, or from one service to another, can be read by anyone on the network path. Encryption in transit wraps that traffic in TLS, which keeps the contents private and stops an attacker who tries to sit in the middle.

---

The security team, the regulator, and the post-mortem team all query the audit log. Production Kubernetes, chapter 9, advises restricting who can read these logs, because not everyone should see them. Start with a narrow query, such as one user's recent events.

---

A regulator may ask one question: which data trained the model that decided on this customer? Lineage answers it by linking data, models, and customers in a chain. The chain has three links. Data feeds the model, the model serves the customer, and every step writes to the audit log. Lineage proves the chain itself. The audit log proves nobody changed the record.

---

Each exercise asks you to add one alert. Build it, then break the control on purpose in a test environment to confirm the alert fires. If the alert stays silent when the control is broken, fix the alert before you trust it.

---

## FILE docs/part-20-nebius-sre-interview/01-the-nebius-loop-and-how-to-use-this-volume.md

The recruiter email arrives and says only "we would like to talk". You have a job posting, a handful of anonymous reports and a volume of 30 chapters. You need to know which stage each chapter serves, so you do not spend a week on the wrong one.

---

What to do with it: prepare for the Amsterdam version, because it is the most detailed and the hardest. Expect some rounds to be easier than you prepared for. Do not read the easy reports as a reason to skip system design.

---

In a console round the same seven steps become: state the symptom, say what you will check first and why, run one command, say what the output means, and name your next hypothesis. In a design round step 3 is where you state your assumptions and numbers. In an incident round step 3 is where you say what you will do to protect users before you know the cause. Chapter 8 has the coding version with timing, and chapter 26 has the incident version.

---

First read [20.38 Token Factory inference engineering](38-token-factory-inference-engineering-everything-nebius-has-published.md). It collects everything public about the inference platform and is the chapter closest to your role. Then read [20.30 the architecture map](30-nebius-ai-factory-to-token-factory-architecture.md), which shows where Token Factory sits on top of AI Cloud, and [20.32 model lifecycle, serving and economics](32-token-factory-model-lifecycle-serving-and-economics.md).

---

## FILE docs/part-20-nebius-sre-interview/02-the-role-in-one-page-the-job-posting-line-by-line.md

R3 mixes two ideas that are often confused. Autoscaling decides how many replicas you run. GPU efficiency asks whether those replicas do useful work. For inference, the usual trap is scaling on a signal that looks fine when the system is drowning. Nebius has not published its autoscaling signals, so the interviewer will probe your reasoning and not your recall. [gap]

---

R4 is about modules and the shape of failure. A resilient cluster module sets defaults such as spread across zones and safe upgrade settings, so every new cluster starts safe. R5 is about the path of a request. Retries hide a transient failure from a user, and the same retries can multiply load in a partial outage. The vendor case study in section 6 mentions exactly that problem. [vendor]

---

The interviewer says: "You have not run vLLM in production. Why should we consider you?" Q5 is desirable, so you have room. Answer in three parts. State the truth: "I have not run it in production." Show the nearest evidence: "I have run GPU workloads on Kubernetes and I read its metrics on a test server." State the plan: "I read the metrics design and I know the three places a request waits, which are the waiting queue, the running batch and the KV cache." Chapter 20.18 teaches those three places. That answer uses a gap as proof of how you learn.

---

The first mistake is rating every skill 4 or 5. The tracker will then have nothing to rank and you will have no study plan. The second is quoting the posting back to the interviewer. Say what you did, not what the line says. The third is claiming knowledge of how Token Factory works inside. Public facts are fine and everything else is a reasoned design.

---

## FILE docs/part-20-nebius-sre-interview/03-triage-method-for-a-sick-linux-box.md

First, the load average counts demand, not only CPU demand. Since 1993 Linux has included tasks in the uninterruptible state, shown as state D, so threads stuck on disk count too. The book says the load is current usage plus queued work. A load of 20 on a 64-CPU machine is headroom. A load of 128 on the same machine means one thread running and one waiting per CPU, on average, if the load is all CPU.

---

The book defines the three. Utilisation is the percent of time the resource was busy, or for memory the share of capacity used. Saturation is extra work the resource cannot service, usually waiting in a queue. Errors are counts of error events. The method iterates over resources, not tools. You write the full list of questions first and only then look for tools, and unanswered questions become known-unknowns.

---

Step 4 is the book's estimate. With 85 on 48 CPUs the book says threads were waiting about 77 percent of the time, from 85 divided by 48 minus 1. It says removing the waiting should speed things up about four times. That is the book's rough arithmetic and not a measurement. The book says that magnitude corresponded to the observed three to four times latency difference.

---

The `vmstat` `bo` column showed about 490000 and `wa` about 43. This is busy with a small queue and a sub-millisecond `await`, which is the reading of Scenario 2, and not saturation. Important correction: the 2048 MB write finishes in about four seconds. `triage_first60.sh` runs its tools one after another, so by the time it reached `iostat` the burst was over and `iostat.txt` showed an idle disk. Only `vmstat.txt`, the third tool, caught it. Run `iostat` by hand beside a short burst.

---

## FILE docs/part-20-nebius-sre-interview/04-files-descriptors-syscalls-and-permissions.md

Systems Performance gives the method in its USE appendix. Per-process utilisation is `echo /proc/PID/fd/* | wc -w` against `ulimit -n`. System-wide it is `file-nr` against `file-max`. The book says saturation may not make sense here. Errors are `strace` seeing `EMFILE`, or the `opensnoop -x` tool.

---

A disk alert fires at 95 percent. You run `du` and the numbers add up to far less. Or a create fails with `No space left on device` while `df -h` shows half the disk free. Both puzzles exist because a filesystem has two resources, not one.

---

The other puzzle is the deleted file that still holds space. A process opened a log file, and then someone or a rotation tool ran `rm`. The name is gone, so `ls` and `du` cannot see it, but the process still holds a descriptor. The proc_pid_exe manual says an unlinked path is shown with ` (deleted)` appended, and the lsof manual says `+L1` selects open files that were unlinked.

---

Reasoning. `Operation not permitted` is `EPERM`, a different error from `EACCES`. With root and normal modes, think of inode flags. `ls -l` does not show them and `lsattr` does. The script needs root or passwordless sudo and a filesystem such as ext4 or XFS. It sets the flag on one temp file, shows the refusals and `lsattr`, and clears the flag on exit. Real output as root with `--cap-add LINUX_IMMUTABLE`: the append, `chmod` and both `rm` calls printed `Operation not permitted`, `lsattr` printed `----i---------e-------`, and after `chattr -i` the write worked. Correction found by running it: root in a default container does not have `CAP_LINUX_IMMUTABLE`, so `chattr +i` itself failed with `Operation not permitted` and the script exited with status 77. This confirms the capability rule in section 6. It also worked on a tmpfs.

---

## FILE docs/part-20-nebius-sre-interview/05-cpu-memory-disk-and-the-scheduler.md

Read it in four steps. First look at the constraint to learn the scope. Second look at `oom_memcg` to learn which cgroup, which maps to a pod through its path. Third compare the victim's `anon-rss` to the limit. Fourth look at the table for who else was large. The kernel source picks the victim by a score. It starts from resident pages plus swap entries plus page tables, then shifts it by `oom_score_adj` scaled to the total memory. A task whose `oom_score_adj` equals the minimum value is skipped and cannot be chosen.

---

The model is on the GPU, so why is host memory the problem? Because everything around the GPU runs on the host. Weights are read from disk through the page cache. Worker processes hold a Python runtime. Data is staged in buffers before copying to the GPU. A GPU inference pod can be killed by the host memory limit while its GPUs are nearly empty.

---

Real output with a 512 MiB file: `Cached` went from 2249340 kB to 2773628 kB, `MemFree` from 3240588 to 2698228 kB, `MemAvailable` from 4934840 to 4921872 kB, and `Dirty` from 2448 to 364880 kB. After the delete, `Cached` returned to 2249340 kB and `MemFree` to 3253872 kB. The helper moved from `81.4% available` to `81.2%` and back to `81.6%`. On the book's numbers it reads 8.4 percent free and 60.9 percent available.

---

Explicitly labelled inferences.
- That pinned memory behaves like anonymous memory in a limit calculation. The books say it cannot be swapped, and the budget treats it as unreclaimable.
- That an OOM kill is one cause of silently shrinking worker pools in a serving fleet.
- That kill-and-replace suits an inference fleet better than swap, as long as the router notices.
- All numbers in the host-memory budget are hypothetical inputs.

---

## FILE docs/part-20-nebius-sre-interview/06-network-debugging-from-socket-to-switch.md

This chapter serves the Linux console round, and it also feeds the 30-minute production-incident round. Nebius states that technical interviews include "practical tasks in the Linux console", "coding, troubleshooting, debugging" and knowledge of "service management, Linux/Unix, networks". The job posting asks for debugging "from kernel to application layer". One candidate reported a Linux server troubleshooting round of one hour on the command line. Nebius has not published which network faults it uses, so this chapter teaches the method and the common faults.

---

The listen man page adds a twist that matters for scenario 1. When the queue of pending connections is full, "the client may receive an error with an indication of ECONNREFUSED". Or the request "may be ignored so that a later reattempt at connection succeeds". So a full queue can look like either a refusal or a timeout, depending on the kernel and its settings.

---

I ran the reader on a real `tcpdump -nn` capture taken on loopback during the accept queue demo. It printed `retransmits: []`, because those were SYN retries and the reader looks for repeated data segments. It listed the three SYNs that never got an answer under `unanswered SYN`. The data retransmit case was tested only on fixture text. The MTU math script prints the sizes to test: 1,450 gives a TCP payload of 1,410 and a ping payload of 1,422.

---

Books, read in the local corpus on 2026-11-09:
- Systems Performance, 2nd edition, Chapter 10 Network: TCP states and timers, TIME_WAIT and port exhaustion, connection backlog queues, ss, nstat, tcpdump, tcpretrans, sysctl examples, MTU and ICMP discussion.
- How Linux Works, 3rd edition, Chapter 9 Understanding Your Network and Its Configuration: ping sizes, resolver files, search line, systemd-resolved, ports and netstat.
- Computer Networking Problems and Solutions, Chapter 24 Troubleshooting (half split) and Chapter 5 Higher Layer Data Transports (Path MTU Discovery, ICMP).
- Networking and Kubernetes, Chapter 2 Linux Networking (Conntrack), Chapter 4 Kubernetes Networking Introduction (CoreDNS, Autopath, DNS limits), Chapter 5 (endpoints, kube-proxy).

---

## FILE docs/part-20-nebius-sre-interview/07-the-console-round-text-tools-systemd-and-everyday-operations.md

The same chapter warns that `-g` needs a build of `journalctl` with a particular library, so some distributions lack it. It also notes that you need root, or membership of the `adm` or `systemd-journal` group, to read everything. `tail -f` does not work, because the journal is not a plain text file.

---

`tar` is safest with `-C`, which changes directory first so the archive holds relative paths. The round trip I ran produced `src/`, `src/a.txt`, `src/sub dir/` and `src/sub dir/b.txt`, and `diff -r` said the restored tree equals the original. `rsync` takes a trailing-slash rule: `src/` means the contents, `src` means the directory itself. The dry run with `--itemize-changes` printed `>f+++++++ c.txt` on the Mac and `>f+++++++++ c.txt` with rsync 3.2.7. Both read "a new file would be sent", and only the count of plus signs differs. Always dry-run before a copy that can delete or overwrite.

---

Send TERM and wait for the grace period. Check whether it is a zombie by looking at the state column. If so, deal with the parent. If it is stuck in uninterruptible sleep, KILL does not help, so name the wait and go to chapter 20.5. Otherwise send KILL and note you skipped cleanup. In a container, say PID 1 only receives signals it has a handler for. Expect the follow-up "what exit code do you see": 143 or 137.

---

1. Generate the fixtures. Expected result: nine files in `code/part20/c07_fixtures/`, a repeat run gives byte-identical files.
   `python3 code/part20/c07_make_fixtures.py`
2. Run all twelve solutions and compare with the outputs above. I ran them all on macOS and on Ubuntu with gawk and mawk and the outputs matched.
   `for f in code/part20/c07_t0*.sh code/part20/c07_t1[0-2]*.sh; do echo "== $f"; bash $f; done`
   Task 9 needs a path argument, so create the tree first with `--tree`.
3. Run the tests. Expected result: 17 passed. I ran it on the Mac and on Ubuntu. It needs rsync installed.
   `python3 -m pytest -q code/part20/test_c07_solutions.py`
4. Run the three demos: `c07_signals_demo.sh`, `c07_robust_demo.sh` and `c07_transfer_demo.sh`. The first prints the exit codes 0, 137 and 143, and a zombie row. On Linux the zombie row ends in `sleep`, not `<defunct>`.
5. Time yourself. Cover the solutions, open each task statement, and solve it in four minutes. Then extend each pipeline with a cross-check by a second method.
6. On a Linux host, repeat tasks 7 and 8 with the live commands `ps -eo pid,ppid,stat,comm` and `df -P`, and confirm the same pipelines work on real output. I ran both in the container and they did. Task 6 with `journalctl -u` was not run. It needs systemd as PID 1 and the container has none.

---

## FILE docs/part-20-nebius-sre-interview/08-the-coding-round-what-to-expect-and-how-to-perform.md

Thinking aloud is a skill with a shape. Use short, structured sentences with a fixed vocabulary. "My first idea is a double loop, which is quadratic. The repeated work is looking up a complement, so a dictionary should make that constant time. I will check with the example." That takes ten seconds and it gives the interviewer three things to react to.

---

A secondary source says some rounds use a plain editor and do not let you run the code. Assume the worst. In that case, the main danger is not the algorithm. It is a typo, an off-by-one error, or a variable that was never defined. The defence is writing in a style that is easy to read back.

---

Code. The `compress` function earlier. Test by hand. Trace `"aaa"`: `run_char` is `a`, `run_len` becomes 3, the loop ends, the last run is appended, giving `"a3"`, which is shorter than `"aaa"`, so it returns `"a3"`. Trace `"aa"`: the packed form is `"a2"`, which has length 2, not shorter than 2, so it returns `"aa"`. That check is why the comparison is `<` and not `<=`. The unit tests cover these cases and pass.

---

1. Change into the repository root and run the Python tests: `cd code/part20 && python3 -m pytest -q test_c08_*.py`. Expected result: 30 passed. I ran this and saw 30 passed.
2. Run the Go tests: `cd code/part20/c08_go && go vet ./... && go test ./...`. Expected result: `ok  c08toolkit`. I ran this and it passed.
3. Open a Python shell in `code/part20` and run `import c08_stdlib_tour as t; t.statistics_demo()`. Expected result: `(22, 3, 2.5, [1.5, 3.0, 52.0])`. I ran this.
4. Break a function on purpose. In a scratch copy, change `<` to `<=` in `compress`, then run `python3 -m pytest -q test_c08_edge_cases.py`. Expected result: at least one failure on `"aa"`. I did not run this exact mutation, so treat the result as the expected shape. The point is to see the harness catch a boundary bug.
5. Timed drill, which you do alone. Pick one problem from the practice set in c20-11, set a 25-minute timer, open a plain text editor with no autocomplete, and talk aloud while you work. Then run the harness. Count the bugs it finds that you did not find by hand. That count is your real score.

---

## FILE docs/part-20-nebius-sre-interview/09-algorithm-patterns-for-sre-flavoured-problems.md

The cost is O(n) time and memory proportional to the number of distinct paths, not lines. That second part is where the SRE angle lives. If you key by raw URL and the URL contains a user id, the dictionary grows without bound. Chapter 20.15 covers the same problem as metric cardinality. The helper `collapse_ids` in the strings section shows the usual fix.

---

You want requests with the same session to land on the same replica, so its cache is warm. Taking the hash modulo the number of replicas works until you add one replica, and then almost every key moves. Distributed AI Systems, chapter 9, applies consistent hashing of the user id to give the same user the same model variant. This is the generic mechanism. Nebius has not published its router algorithm.

---

The test compares the component count against a brute-force merge of sets on random edge lists. The `failing_clusters` function is the SRE form: only links between two failing nodes count, so a healthy switch does not join clusters. In the interview, ask whether a shared healthy switch should connect them.

---

The examples are the SRE forms. `min_replicas` finds the fewest replicas that cover peak traffic when per-replica capacity falls as replicas are added, so you cannot just divide. The test compares it to a linear scan. `min_timeout_ms` returns the smallest integer timeout that lets a target fraction finish. `min_window_hours` is the classic split-array problem, framed as the shortest maintenance window that lets a fixed job order run on a given number of nodes. The test compares it to brute force on 100 random inputs. `float_search` uses a fixed number of iterations because a real-valued loop that tests equality may never end.

---

## FILE docs/part-20-nebius-sre-interview/10-complexity-latency-numbers-and-measuring-your-own-code.md

Name worst case against average case too. Fluent Python, chapter 3, explains that a dict or set derives an index from the key's hash. Chapter 2 says Python's sort is Timsort, which adapts to how ordered the data is, so sorted input sorts faster.

---

The first is Jeff Dean's keynote slides "Designs, Lessons and Advice from Building Large Distributed Systems", given at LADIS 2009. The file's creation date is October 2009. Its slide "Numbers Everyone Should Know" is the table below. The second is an undated Dean slide set, "Software Engineering Advice from Building Large-Scale Distributed Systems", with older values for a few rows. The third is Peter Norvig's page "Teach Yourself Programming in Ten Years", which lists a similar table without the datacenter round trip. I fetched all three on 2026-11-09.

---

The older Stanford slides list mutex lock/unlock at 100 ns and reading 1 MB from disk at 30,000,000 ns. Norvig's table gives a disk seek of 8,000,000 ns. The digits move between versions and the orders of magnitude do not.

---

Fetched 2026-11-09: docs.python.org time-complexity page, the Python 3.12 collections page, the Tail at Scale paper (OCR of the PDF). Claims checked: 9. Confirmed: 8 (list, set, dict and deque costs, the 63 percent fan-out figure, hedging after the 95th percentile adding about 5 percent load, the string `+=` quadratic note, the 0.9999 quantile arithmetic, the Dean latency table from earlier fetches). Corrected: 1 (the tail-latency defences were unsourced and now follow the paper's list). Removed: 0. Still unverified: 3. They are that Nebius asks for the latency numbers, that cache explains the locality gap, and datacenter round-trip time on current cloud hardware. The Stanford-named slide date is still my inference.

---

## FILE docs/part-20-nebius-sre-interview/11-coding-practice-set-40-problems-with-tested-solutions.md

You are forty minutes into the coding round. The interviewer has read you a problem about log lines, you have restated it, and the editor is empty. This chapter is the practice set for that moment. Chapter 20.8 covers what to expect and the toolkit, chapter 20.9 teaches the patterns, and chapter 20.10 gives complexity and latency numbers. Here you only practise.

---

Brute force gives you a fallback and, later, an oracle. The tests here use the same idea: where it is cheap, each solution is checked against a slow, obviously correct version on thousands of random small inputs. **Write the slow version first, in your head or on paper.**

---

The interviewer says: "Compress runs of equal letters, but only if it helps." You restate, ask about digits, and agree on lowercase input. A brute force is obvious, so you go straight to one pass. The solution keeps the current character and its length and flushes when the character changes.

---

The pattern catalogue for these problems is chapter 20.9. The Python toolkit and what to expect in the round are chapter 20.8. Complexity and latency numbers, and how to test aloud, are chapter 20.10. The SLO and burn-rate meaning behind P1 is chapter 20.19, and request retry behaviour behind M13 is chapter 20.21. Telemetry at high volume, and the series cardinality that P3 ignores at small scale, is chapter 20.15. Rollout safety behind P4 is chapter 20.14. The log-parsing flavour of E3 and M6 also appears in the Linux console round, chapters 20.3 and 20.7.

---

## FILE docs/part-20-nebius-sre-interview/12-estimation-toolkit-for-inference-capacity.md

A user pastes a long document and your endpoint starts rejecting requests, yet the weights fit with room to spare. The room was not spare. It was reserved for the KV cache, and the cache grows with every token of every live request.

---

During generation, each layer keeps a key vector and a value vector for every token seen so far. Without that store, the model would recompute them at every step. The book Hands-On LLM Serving and Optimization, Chapter 5, gives the per-token formula in its multi-head form. Replace the head count with the number of key-value heads, because models with grouped-query attention store only those.

---

The book works the L40S: 362 TFLOPS divided by 864 GB/s gives a ridge near 419 operations per byte. Its Table 5-10 then shows that decode with one row per request has an intensity of about 1 whatever the sequence length. Prefill, which processes the whole prompt as many rows, climbs from 62 at 64 tokens to 1,365 at 4,096 tokens. The book's conclusion is that prefill can be compute-bound while decode is always bandwidth-bound at batch size one.

---

The answer is nine H100s, about $29,565 per month, which is 9 GPUs times $4.50 times 730 hours. The $4.50 is the Nebius on-demand list price fetched on 2026-11-09, so replace it with your own contract rate. State that it assumes 40 percent prefill efficiency and 5 GB of overhead, and that a benchmark replaces both. You can reproduce it with the command in the lab.

---

## FILE docs/part-20-nebius-sre-interview/13-design-a-multi-tenant-llm-inference-api.md

The job posting adds three lines that this design touches directly. It asks for request routing and retry logic so transient failures do not reach users. It asks for Kubernetes autoscaling tuned for GPU efficiency. It asks for alert design and SLOs for high-throughput APIs. So the interviewer wants a design where reliability is a feature of the architecture, not an afterthought.

---

One realistic question, in the interviewer's voice: "Design the API behind a service like Token Factory. Many customers call it with an OpenAI-style request. Some want shared capacity, some want a dedicated endpoint. You have 45 minutes. Where do you start?"

---

Keep the surface small. Nebius says the API is OpenAI-compatible, so the data path is a streaming chat or completion call. Add a separate control API for managing endpoints, which the public facts say lifecycle operations belong to. Say the split now, because everything later hangs on it.

---

Set a per-stream write timeout and a maximum duration. Stop generation when the client disconnects, because generating for nobody wastes GPU. Bound every queue. Distributed AI Systems, Chapter 9, describes a bounded request queue that rejects at once with a 503 rather than letting requests time out after a long wait. Fast rejection gives the client a clear signal to retry or go elsewhere.

---

## FILE docs/part-20-nebius-sre-interview/14-design-dedicated-endpoints-and-safe-model-rollout.md

Public facts, from the plan's research section, tagged vendor and docs. Token Factory offers serverless and dedicated endpoints with an OpenAI-compatible API and the full vLLM parameter set. The control plane, which handles create, update, enable, disable and delete, is separate from the region-specific data plane. On a dedicated endpoint you pick the GPU type from L40, H100, H200 or B200, the GPUs per replica, the minimum and maximum replicas, and the region in the EU or US. The chat-app case study reports a 99.9 percent SLA on dedicated endpoints and a need for X+1 redundancy.

---

Strong automatic signals are the canary producing zero tokens, the error rate above a hard ceiling, a pod restarting or failing readiness repeatedly, and a quality score below the floor on the live eval probe. Weaker signals are latency ratios and finish_reason shifts, which need a baseline and enough traffic, so they should hold first and page a person if they persist. Chapter 20.19 covers SLO burn alerts that can serve as a fleet-wide backstop.

---

Rollback itself must be boring. It is the same update action pointing at the previous version id, which still exists in the weights hub and is still cached on nodes if you keep it. Time to rollback is the sum of a router weight change, which is seconds, and a pod replacement, which is a cold start. So keep the old replicas alive until the new version has carried peak traffic, as chapter 20.13 recommends. That makes rollback a weight change and not a reload.

---

The cache point is worth saying out loud. A reasonable design keys the prefix cache and cache-aware routing by model version, so no hit crosses a version boundary. That is my reasoning, and it follows from the fact that different weights produce different KV values.

---

## FILE docs/part-20-nebius-sre-interview/15-design-an-observability-pipeline-for-very-high-volume.md

An alert fires and a new engineer opens Grafana. The pipeline has succeeded if that engineer gets from "TTFT is high" to "model X on pool Y is queueing" in two minutes. It has failed if the answer sits in data that was sampled away, or the query times out because the store is overloaded.

---

The three signals have different costs. A metric costs by series count, a log by bytes and a trace by spans retained. Systems Performance, Chapter 4, makes the same split. Counters are always on and nearly free. Profiling and tracing cost CPU and storage, so you sample them. That is the shape of the whole design.

---

The memory limiter processor is the control point for the collector. It checks memory at an interval, with a recommended 1 second. When memory crosses the soft limit, which is the limit minus a spike allowance of 20 percent by default, it refuses data by returning errors upstream. Those errors are retryable, so senders can retry or slow down. When it crosses the hard limit it also forces garbage collection. The README says to place it first in the pipeline so backpressure reaches the receivers. The batch processor then groups data. Its `send_batch_size` defaults to 8192 and its `timeout` to 200 ms.

---

Start with the good design. The gateway counter has model 20, code 8 and route 5, which gives 800 combinations, times 12 gateway pods, giving 9,600 series. Now add tenant with 1,000 values and assume 10 percent of combinations occur. That is 800 times 1,000 times 0.1, which is 80,000 combinations, times 12 pods, giving 960,000. The histogram has 14 buckets plus three series, so 17 per combination. With model 20 and route 5, tenant 1,000 and fill 0.1, that is 10,000 combinations, times 17, times 12 pods, giving 2,040,000. Total about 3 million.

---

## FILE docs/part-20-nebius-sre-interview/16-design-gpu-fleet-health-and-capacity.md

DCGM ships an active check, `dcgmi diag`, with four run levels. The documentation gives the durations below. The Diagnostic plugin multiplies large matrices while watching for Xids, temperature violations and memory errors, so it cannot share the GPU with customer work.

---

When the limiter says no, the node is not forgotten. It stays suspect and appears in a held list for a human. The design principle is that automation may act freely on small, rare, well-understood events. It must hand over to a person when the scale of the event surprises it.

---

1. From the repo root run `python3 -m pytest -q code/part20/test_c16_fleet_health.py code/part20/test_c16_spare_pool.py`. Expected and observed: 19 passed.
2. Run `cd code/part20 && python3 c16_spare_pool.py`. Observed: spares of 2, 3 and 7 for the three repair times in the table above.
3. Run `python3 c16_sim_storm.py` in the same directory. Observed: the eight lines shown in section 7. Change `trip_flags` to 10 and see whether the hourly rate alone still protects you.
4. Run `promtool check rules c16_gpu_health_rules.yml` and then `promtool test rules c16_gpu_health_rules_test.yml`. Observed: 15 rules found and the test passes.
5. On a GPU node with DCGM, run `dcgmi diag -r 1 -j`. Not run. Expected shape: JSON with a result per test and exit code 0 when all pass.
6. On a cluster, run `kubectl drain <node> --ignore-daemonsets --timeout=300s`. Not run. Expected shape: pods evicted one by one, and a message about a disruption budget if one blocks.

---

Not verified: `dcgmi diag` and `kubectl drain` were not run, there is no GPU or cluster here. What vLLM's HTTP server does between SIGTERM and exit was not traced. I confirmed only the `shutdown_timeout` setting and its help text. Whether Nebius uses any of this is unknown. The prompt "detect a failing GPU before the customer does" comes from a secondary source and is unverified as a real question.

---

## FILE docs/part-20-nebius-sre-interview/17-system-design-drill-sheet-twelve-prompts.md

The interviewer says "design a system for me" and starts a clock. This chapter serves the system design round. Nebius states that the round covers designing "a whole or partial distributed system" to meet load and availability targets, preferably with specific technologies, estimating performance and compute, and discussing storage and processing trade-offs [official, careers/interviews/sre]. It also says any language and any technology is allowed, and that you should think aloud and ask for hints.

---

A secondary source lists five prompts: GPU job scheduling, model inference serving, training data storage for thousands of GPUs, detecting a failing GPU before the customer does, and an SRE variant [report]. Prompts 1 to 5 below are those five. Prompts 6 to 12 are my own additions, chosen because they fit the Token Factory SRE posting. Nebius has not published its internal designs. Everything under "Graders look for" is my reasoning about what a strong answer contains.

---

1. "Let me restate the problem in one sentence. Is that right?"
2. "Who are the users, and what does one request or job look like?"
3. "What is the scale: peak load, data size, number of tenants?"
4. "What is the target: latency, availability, durability?"
5. "What is out of scope, and may I assume it?"
6. "Here are my assumptions. Please correct any that look wrong."
7. "I will estimate first, then draw the data path, then talk about failure. I will watch the clock."

---

In prompt 2 the interviewer says "the model is now 70 billion parameters." Do not restart. Recompute weights at 2 bytes: 140 GB, which no longer fits one 80 GB GPU. Say tensor parallelism across at least 2 GPUs, with less KV room per GPU. Then re-derive requests per GPU with the formulas of [20.12](./12-estimation-toolkit-for-inference-capacity.md). Show that only the inputs changed and the method did not.

---

## FILE docs/part-20-nebius-sre-interview/18-how-llm-serving-fails.md

A request enters the engine and sits in the waiting queue. The scheduler moves it into the running batch when there is room. While it runs, its keys and values occupy the KV cache, which is GPU memory reserved for per-token attention state. Nearly every serving failure is one of these three places filling up, stalling or lying about itself.

---

The mechanism. Every running request needs KV space that grows with each token. When space runs out, vLLM preempts a request, frees its cache and recomputes it later. The vLLM optimisation page says V1 defaults to recompute mode, since recomputation is cheaper than swapping in that architecture. Recomputation burns GPU time and puts the victim back at the front of the queue, which hurts both its latency and everyone else's.

---

Confirm. Compare `vllm:request_prompt_tokens` p99 against p50. A tail that is eight or more times the median is a warning sign. In the classifier this ratio is a starting value I chose, not a vendor number. Also check that preemption is flat, which rules out section 3.

---

Fix later. Separate prefill and decode pools, as the Nebius case study did [vendor], and add per-tenant context-length limits. AI Systems Performance Engineering, chapter 16, lists "decode-node hotspot or head-of-line blocking" and recommends inspecting router logs and enabling speculative decoding paths. Treat the speculative-decoding suggestion with care, for reasons in section 11.

---

## FILE docs/part-20-nebius-sre-interview/19-slis-slos-and-alerts-for-token-apis.md

Picture a normal web API. A request arrives, the server works, one response comes back with a status code. Availability is the share of non-error status codes and latency is one number per request. A token API does not behave like that.

---

The budget is 43.2 minutes. Twelve minutes is 12 divided by 43.2, which is 0.278, so 27.8% of the month. If instead 25% of requests fail for 20 minutes, the equivalent outage is 0.25 times 20, which is 5 minutes, or 11.6%. The first alert to fire is the fast availability burn. The error ratio is 100% and the threshold is 1.44%, so it fires in about 52 seconds and clears a few minutes after the rollback.

---

The reasoning is that a ratio over almost no traffic is noise. If tenant b is a dedicated customer with a contract, give it a different rule, such as an absolute count of failures in an hour. The trade-off is another rule to maintain.

---

4. Break a threshold on purpose. Change `rate1h > 0.0144` to `rate1h > 0.0200` in `slo_burn_alerts_availability.yaml` and rerun the availability test. I did this. The test named "two percent errors pages fast and medium" failed with `got:[]`, because 2% is not strictly above 2%. Restore the file afterwards.

---

## FILE docs/part-20-nebius-sre-interview/20-autoscaling-gpu-inference.md

CPU is worse. Production Kubernetes, Chapter 13, warns against scaling on a metric that does not change in proportion to load, and it gives CPU spikes at startup as an example. An LLM engine's CPU does the tokenisation and the HTTP work. It does not track how many sequences the GPU holds. LLMs in Production adds that the CPU and memory must be large enough, or the service throttles before the GPU metric ever moves.

---

Three more points from that page matter for GPU work. It advises a CPU node group of at least two nodes, or an autoscaling one, so that CoreDNS and the networking add-on can run there and the GPU group can scale down. It lists a known issue. With the NVIDIA GPU Operator and Network Operator installed, autoscaling on a GPU group can create more nodes than needed. The page attributes it to an upstream autoscaler bug and suggests a new node group on the GPU-adapted boot image. I have read the page and have not reproduced the issue.

---

At the first sync the ratio is 22 divided by 11, which is 2.0. The desired count is ceil of 4 times 2, which is 8. The default scale-up policies allow 100 percent or 4 pods per 15 seconds, so going from 4 to 8 is allowed. At the second sync the four new replicas are not ready. The 88 requests are spread over 8 pods for the calculation, the average is 11, and the ratio is 1.0. Nothing changes. After the replicas load weights and join, the 88 requests spread over 8 pods. If traffic then falls and the recommendation drops to 5, the 900-second window keeps the count at 8 until the highest recommendation inside the window is lower. The answer: 8 replicas, no runaway, and a slow descent.

---

Expected shape, which I ran: the static fleet violates the 5 second queue SLO for 91 percent of requests. The queue and in-flight policies violate it for about 51 percent. The utilisation policy violates it for 0 percent and uses 12.6 GPU-hours against about 7 for the others.

---

## FILE docs/part-20-nebius-sre-interview/21-request-routing-retries-and-overload-control.md

The exponential schedule doubles the ceiling each time: ceiling for retry n is the smaller of the cap and base times 2 to the power n minus 1. Full jitter then sleeps a random time between 0 and the ceiling. Its mean is half the ceiling, so the total wait is also halved. With base 0.1 s and cap 5 s, the four ceilings are 0.1, 0.2, 0.4 and 0.8 seconds, total 1.5. The full-jitter means are 0.05, 0.1, 0.2 and 0.4, total 0.75.

---

Envoy circuit breakers cap connections, pending requests, requests and active retries per cluster. The docs call the defaults modest and give 1024 connections per cluster as an example. Istio's connection pool defaults for pending requests, requests and retries are all 4294967295, which is effectively no limit. Check what your mesh actually enforces.

---

Routing to the replica that already holds a request's prompt prefix skips the prefill and cuts time to first token. Routing to the least loaded replica keeps queues even. They pull in opposite directions, and reliability decides the winner under stress.

---

A whole region loses capacity. The tempting answer is to send its traffic elsewhere. For a tenant whose prompts must stay in the EU, the elsewhere may be illegal. A fallback that breaks the promise is worse than an outage.

---

## FILE docs/part-20-nebius-sre-interview/22-operating-vllm-triton-ray-and-tensorrt-llm.md

TensorRT-LLM is NVIDIA's library for NVIDIA GPUs. Its v1.2.1 overview says it is architected on PyTorch, with a Python LLM API and a `trtllm-serve` command that starts an OpenAI-compatible server. It lists in-flight batching, paged KV cache with block reuse, chunked prefill, speculative decoding, FP8 and FP4 quantisation, and disaggregated serving, which it marks Beta. The book says it suits teams that have standardised on NVIDIA hardware and want the best efficiency.

---

SGLang is a peer to vLLM. The book lists RadixAttention for prefix reuse, structured output, speculative decoding and four parallelism modes, and says it targets a broader range of hardware than TensorRT-LLM. Its README describes it as optimised for agentic workloads and large-scale serving.

---

`max_num_seqs` caps how many requests run in one step. The class default is 128, but its docstring says real values are set when the engine config is created, so read the start-up log for the value in force. A high cap with a small cache means admitting work you cannot hold. The vLLM optimisation guide lists lowering it as one of the fixes for preemption.

---

Step 1. Read the start-up log for "GPU KV cache size". With the section 3 inputs, the cache holds about 389,100 tokens. Step 2. Divide by `max-num-seqs`. The average request can be only about 3,040 tokens before 128 running requests fill the cache. Step 3. Compare with traffic. If the afternoon average prompt plus output is 4,000 tokens, the cache cannot hold the batch, so vLLM preempts and recomputes.

---

## FILE docs/part-20-nebius-sre-interview/23-kubernetes-failure-drills-for-gpu-platforms.md

A GPU is not built in. A vendor device plugin advertises it. The Kubernetes scheduling-GPUs page says an administrator installs drivers and the vendor plugin, and then the cluster exposes a resource such as `nvidia.com/gpu`. If the plugin is not running on a node, that node advertises zero and every GPU pod stays Pending.

---

GPUs go in `limits`. The same page says you can give a limit without a request, because the limit becomes the request. You can give both only if they are equal. You cannot give a request alone. There is no overcommit.

---

Say: "Pending means the scheduler has not placed it, so I read the scheduler's reason in the pod events." Then run `kubectl describe pod` and read the FailedScheduling line. State the three outcomes. Insufficient `nvidia.com/gpu` means no node has a free GPU in its Allocatable. Untolerated taint means the pod needs a toleration. A selector mismatch means labels. Follow up: if Allocatable is zero on a node that has GPUs, the device plugin is the suspect. If a ResourceQuota is hit, the pod never exists, because the API server returns 403 and the ReplicaSet records the failure.

---

I ran steps 1 to 5 on macOS with Python 3.12 and kubeconform from `~/go/bin`. I ran steps 1 to 4 again in a disposable Linux container, `ubuntu:24.04` on kernel `6.18.37-0-virt` with Python 3.12.3 and the repository mounted read-only. The results were the same on both. I did not run kubeconform on Linux. Step 6 is not run, because there is no cluster, and Docker alone cannot stand one up without privileged mode.

---

## FILE docs/part-20-nebius-sre-interview/24-terraform-for-resilient-gpu-clusters.md

The job posting lists "Terraform modules that build resilience into new clusters" and "Terraform/IaC" as required. Resilience here means three things. The cluster survives failures of its parts. The code survives mistakes by its own engineers. The state, which is Terraform's memory of what exists, survives accidents too.

---

The nebius-solutions-library `k8s-inference` README is a real example. It has two Terraform stages. The `cloud` stage holds one state for clusters, pools, filesystems, static IPs, identities, registry, buckets and the managed database. The `platform` stage holds one state per cluster for Helm releases, manifests, tenants and API keys. The tfvars file has a `protect_data` setting at the top level. The README also describes one cluster per GPU region plus a CPU control cluster. That layout is the library's choice, not a Nebius standard.

---

Production Kubernetes, chapter 2, adds the cluster-level view. Smaller clusters mean a smaller blast radius, and the book says to federate regionally and then globally. It also treats clusters as replaceable herd animals. That idea carries over directly. If a cluster is cheap to rebuild from code, a bad cluster is a rebuild, not an emergency.

---

Next, `prevent_destroy`. The lifecycle docs say it makes Terraform reject any plan that would destroy the object. They also give three caveats that interviewers love. It does not help if you delete the resource block from the code. It can make some changes impossible. And it blocks `terraform destroy`. Here is the real output when I removed the `gpu` pool from the variables while this module still had `prevent_destroy`. The state was hand-written for the demo, so treat it as a demonstration of the mechanism, not a Nebius run.

---

## FILE docs/part-20-nebius-sre-interview/25-promql-grafana-and-tracing-traps.md

A counter only goes up, except when a process restarts and it falls back to zero. Dashboards that subtract two counter values break at that moment. The Prometheus docs say `rate` adjusts automatically for breaks in monotonicity, such as counter resets after target restarts.

---

An alert without a `for` clause becomes active on the first evaluation, as the docs say. One noisy sample pages a person. A `for` clause holds the alert in the pending state until it has been active for the whole duration.

---

Alertmanager's docs describe three tools. Grouping puts alerts of similar nature into one notification. Inhibition suppresses certain alerts when others are already firing. Silences mute alerts for a time. A routing tree in the config file sets the grouping, the timing and the receivers.

---

1. Check the rules. `promtool check rules code/part20/c25_trap_rules.yaml` should print `SUCCESS: 11 rules found`.
2. Run the exercise tests. `promtool test rules code/part20/c25_exercises_test.yaml` should print `SUCCESS`. Change one expected value and see the diff it prints.
3. Run the alert tests. `promtool test rules code/part20/c25_trap_rules_test.yaml` should print `SUCCESS`.
4. Check the Alertmanager config. `amtool check-config code/part20/c25_alertmanager.yml` should list 2 inhibit rules and 2 receivers. Run `code/part20/c25_route_check.sh` and expect three `ok` lines.
4b. Run the real Alertmanager. Start `prom/alertmanager` in Docker with the config, pointing both webhooks at a small receiver on the host. Post three alerts for one model and cluster, one for another model, and one `VllmTargetsMissing`. I ran this. Two ticket alerts for model m1 arrived as one notification listing both. A page alert for model m2 reached the pager, and the ticket alert for the same model was inhibited. In cluster c2, `QueueDeep` with severity page was inhibited while `VllmTargetsMissing` was firing. The API listed the inhibited alerts as suppressed. The timing values were not measured to the second.
5. Lint the good and bad rules. `python3 code/part20/c25_promql_lint.py code/part20/c25_trap_rules.yaml` reports 0 findings. The same command on `c25_bad_rules.yaml` reports 5 warnings and exits 0. Add `--strict` and it exits 1.
6. Run the pytest suite. `python3 -m pytest code/part20/test_c25_promql_lint.py` should report 38 passed.
7. Break an offset on purpose. Write `rate(gateway_requests_total[5m]) offset 1h` into a rule file and run `promtool check rules`. Expect the parse error quoted in idea 11. I ran this.
8. Break a join on purpose. Use two vLLM series for one pod and one `kube_pod_info` series, then query without `group_left`. I ran this and `promtool` printed the many-to-one error quoted in idea 7.

---

## FILE docs/part-20-nebius-sre-interview/26-the-stress-interview-production-incident-role-play.md

Every drill has a destructive trap, such as restarting every replica at once, defragmenting a live etcd member, sending EU traffic to a US region, or editing live config that GitOps will overwrite. Before you run anything risky, say what it does, how to undo it, and how far the damage can spread. If you cannot say how to undo it, ask for a second pair of eyes.

---

Later in the same run I filled the disk for real. A 60 MB write into the 50 MB tmpfs failed with `head: error writing 'standard output': No space left on device`. Then `df` showed 100 percent and `du` showed 50M. `df -i` showed 757,587 inodes with 2 used, so space and inodes are separate limits. The `df` and `du` gap, the `(deleted)` row and the `/proc` truncation are now real Linux output. The kubelet eviction behaviour was not tested, since there is no cluster.

---

Observed on the Mac and again on Linux with OpenSSL 3.0.13: a `notAfter` date one day ahead, then `Certificate will expire` with exit status 1, because the certificate expires inside the 86,400 seconds you asked about. With `-checkend 0` it printed `Certificate will not expire` and exit status 0.

---

Fact-check pass on 2026-11-09. Six claims were checked and all are confirmed: the `kubectl rollout undo` and `rollout status` commands on the Kubernetes Deployments page, the startup probe arithmetic on the probes page, the four incident roles and declare-early conditions in Managing Incidents, the 64 attempts and 60 retries per minute in Addressing Cascading Failures, the etcd fsync figure and defragmentation warning in the etcd documentation, and the eviction defaults used in chapter 20.23. The router registration and every incident number are invented and cannot be checked.

---

## FILE docs/part-20-nebius-sre-interview/27-post-mortems-on-call-and-incident-leadership.md

This chapter serves two stages of the loop. It sharpens the production-incident stress round, covered in 20.26, and it prepares the behavioural questions that follow your project deep dive. The job posting asks you to "detect, isolate and remediate incidents quickly using automation and runbooks, then lead post-mortems to prevent recurrence". It also asks you to "work with software engineers to make reliability a built-in feature". Each phrase maps to a section below.

---

The Google SRE book chapter Being On-Call gives figures. On-call should take no more than 25 percent of an SRE's time, with at least 50 percent for engineering. The maximum is two incidents per 12-hour shift, because handling one incident, including root cause and follow-up, averages about 6 hours. A single-site team needs 8 engineers for a rotation, or 6 per site with two sites. The workbook defines pager load as paging incidents per shift and adds that an incident may involve more than one page. It says a 21-day trailing average is useful for spotting trends.

---

To keep load down, the same chapter says to align paging alerts with symptoms that threaten SLOs, make every paging alert actionable, group related alerts so one incident does not generate many pages, and tune toward one alert per incident. The workbook recommends limiting shifts to 12 hours and says a 12-hour overnight shift beats 24 hours or more. It says out-of-hours work should be compensated. One of its case studies praises psychological safety: even when engineers escalated, they were still regarded as competent.

---

1. **"Tell me about an incident you led."** Impact: "About a quarter of requests were slow for forty minutes." Role: commander and operator, or commander only. Decisions: mitigate with traffic weight first, delay root cause, communicate every 15 minutes. Result: minutes to mitigate and resolve. Change: one gate, one alert, with a number. Expect "what would you do differently?" and answer with something concrete.
2. **"Tell me about a time you made a mistake in production."** Own it in the first sentence. Give the impact, how you noticed, how you reverted. Then say what the system lacked that let one person cause it, and what you added. Never blame a colleague. Expect "was anyone blamed?"
3. **"Tell me about a post-mortem you wrote or led."** Name the structure: summary, impact, timeline, cause and trigger, lessons, actions. Give one action with owner, date and measure. Say how you ran the review so people spoke freely. Expect "what happened to the action items?" and have a closure rate ready.
4. **"How do you decide an incident's severity?"** Customer impact first, then SLO risk, then the response time each level carries. Say levels can be raised, and that you declare early. Mention the three signs from Managing Incidents. Expect a scenario to classify.
5. **"Tell me about a time you reduced toil or on-call load."** State the baseline: pages per shift or hours a month. Say how you measured it, what you automated, and the new number. Include one thing you chose not to automate and why. Expect "how did you know it was worth it?" and give the break-even arithmetic.
6. **"Tell me about a time you pushed back on a release for reliability."** Use the budget. Give the SLO, the minutes consumed, the options you offered. Say you looked for a way to ship safely, such as a flag or a smaller canary. Expect "what if the VP overrides you?" and say you would record the risk and escalate through the agreed policy.
7. **"Tell me about a time an incident was handed over, or you took over one."** Describe the briefing and the explicit "You're now the incident commander" line. Say what you wrote in the state document. Say what you checked on taking over: current mitigation, open hypotheses, who holds each role. Expect "what if the handover is unclear?"
8. **"Tell me about a time you worked with developers to make a service more reliable."** Pick a concrete change: a readiness check that tests generation, a retry budget, a load-shedding path. Show how you made it their problem too, with data. State the measurable result and how the developers owned it afterwards. Expect "what did they resist?"

---

## FILE docs/part-20-nebius-sre-interview/28-the-project-deep-dive-and-the-final-round.md

Writing the project down is how you find out what you do not know. The dossier has nine parts. Context, role and team, constraints, numbers, architecture, decisions, failures, what you would change, and metrics of success. Each part answers a question an interviewer will ask, and the order is the order a good story is told.

---

For why SRE, the honest shape is a story about what you like. You like owning the number that says whether users are happy, and you like turning a repeated page into automation. The job posting asks for incident detection, isolation and remediation with automation and runbooks, and for post-mortems. Link one of those to a thing you have done: [YOUR AUTOMATION EXAMPLE].

---

Speak in this order. One sentence on why it existed. One on your role and the team size. The shape of the system in three components. The two biggest decisions. The result with one before-and-after number. Finish with "the part I would like to go deeper on is" and name the most interesting decision. Expect a follow-up on whichever part you mention last, so end on your strongest. State [YOUR NUMBER] for scale and [YOUR NUMBER] for the result.

---

The checker itself is below. It is the file `code/part20/c28_dossier_check.py`. It reads the dossier, strips HTML comments while keeping line numbers, splits it into sections and blocks, and applies the rules. The unfilled-marker pattern, the claim-word pattern and the minimum counts sit at the top so you can adjust them.

---

## FILE docs/part-20-nebius-sre-interview/29-the-8-week-plan-the-final-week-and-the-cheat-sheet.md

A realistic question in the interviewer's voice, from the final round: "We have an hour. Tell me how you prepared for this interview, and what you found hardest." The honest answer is a plan, with dates, that you actually followed. Chapter 20.1 (`c20-01`) explains the loop itself, and this chapter schedules the study.

---

Hours per week is a parameter. The generator at the end of this chapter takes it. The split inside each week is a rule I chose: about 40% reading and lab work, 30% drills and coding practice, 30% speaking aloud and mock rounds. Nothing in the official page sets this split. If you have 6 hours a week, keep the ratio and cut breadth, not the speaking.

---

The most common failure in a loop like this is not missing knowledge. It is being unable to say what you know under a clock, with a person watching. So the mock protocol trains the output, not the input. Run one mock for each round type from week 3, then one every week in the last three.

---

The schedule generator uses only the standard library. It picks the plan from the days left and clips the plan to the days you have. Hours per block equal weekly hours times the days in the block over seven, scaled by a load factor that tapers the last block. The code block below equals the file.

---

## FILE docs/part-20-nebius-sre-interview/30-nebius-ai-factory-to-token-factory-architecture.md

Storage choices follow recovery needs. Network SSD tolerates up to two concurrent hardware failures. Non-replicated disks have no redundancy. Local SSD is erased when the VM stops or is deleted. A shared filesystem can attach to many VMs at once.

---

The control plane has one base URL, `https://api.tokenfactory.nebius.com`. The data plane URL depends on the endpoint region. The control and data plane page maps `eu-north1` to the same hostname as the control plane, `eu-west1` to `api.tokenfactory.eu-west1.nebius.com`, and `us-central1` to `api.tokenfactory.us-central1.nebius.com`. The deploy guide's own example creates an `eu-north1` endpoint but shows a `us-central1` inference URL, so match the URL to the region you actually chose.

---

The create-endpoint OpenAPI schema also has an optional `reservation_policy` object. Its `policy` field takes AUTO, FORBID or STRICT, and `reservation_ids` is an optional list. The capacity guide does not explain which reservations qualify or what guarantee follows. Confirm that with Nebius before you assume anything. Canarying and draining an endpoint rollout are your own design choices [inference], unless a current page documents them.

---

Metrics are collected where inference runs and ultimately stored in `eu-north`. The Prometheus and Grafana integration page uses a static API key issued in the Token Factory UI. Its path includes your project ID, and it recommends a scrape interval of no less than 15 seconds. A residency review should treat metrics location separately from endpoint region. The page also says the dashboards are for debugging and performance analysis, not billing reconciliation.

---

## FILE docs/part-20-nebius-sre-interview/31-nebius-ai-cloud-foundation-gpu-fabric-and-platform-choices.md

An interviewer says: "A customer wants to train a model, host a fine-tuned version and serve an agent in Europe. Build it on Nebius." You have a whiteboard and ten minutes. You need to know which layer you can pick, which layer Nebius runs for you, and which facts you must check live before you promise anything.

---

Topology matters because the network has layers. The topology page describes a fabric with a root switch, PODs under it joined by core switches, and scalable units inside PODs joined by leaf switches. Crossing a higher layer costs more [official]. Slurm and Volcano can read a topology file so the scheduler places distributed jobs on nearby nodes. Nebius reports NCCL AllReduce tests with "performance gains of up to 20%, depending on cluster size" and gives no test setup [vendor]. Treat that as a reason to benchmark your own job, not as a promise.

---

Object Storage has three classes. Standard is the default. Intelligent moves objects to a cheaper Cold tier after 30 days without access, and moving does not change performance. Enhanced Throughput has no speed throttle, a higher storage price, and free operations and egress. Standard and Intelligent are capped at 20 GBps per tenant per region [official, storage classes page]. The page lists weights, datasets and checkpoints as Enhanced Throughput use cases.

---

1. Pick one workload: multi-node training, online serving, or an agent. Write latency, throughput, residency and recovery targets. **Expected:** every item has a number or is marked unknown.
2. Open the VM types page. Choose a platform, preset and region, and a fallback. **Expected:** you can say which facts need a live project check.
3. Open the GPU clusters page. Decide if InfiniBand is justified. **Expected:** a yes or no with a reason tied to collectives.
4. Assign each dataset, weight file, checkpoint and image to a storage type from section 6. **Expected:** no unique checkpoint exists only on local SSD.
5. Pick an orchestrator from section 7 and list who owns drivers, scaling, keys and regional recovery. **Expected:** a one-line owner per item.
6. Write one failure and one cost check from section 8. **Expected:** each has a signal, a first action and an owner.

---

## FILE docs/part-20-nebius-sre-interview/32-token-factory-model-lifecycle-serving-and-economics.md

A customer writes to support: "Our fine-tuned model worked in the test. In production we see 404 for ten minutes after every restart, the bill is higher than the token count suggests, and legal asks where prompts are processed." Each part of that message is a question about the product contract. This chapter serves the system design round and the project deep dive. It also feeds the incident round, because most customer incidents on a managed inference product start with a misread contract.

---

The table follows the Dedicated Endpoints overview page [official]. One cell needs care. The overview says capacity is "reserved for your organization". The capacity page says self-service endpoints use an on-demand shared pool, that the capacity is "not a long-term reservation", and that minimum replicas are guaranteed only while the endpoint is active [official]. The second page is more precise. Read "reserved" as "held while active".

---

Scope is where privacy enters. On Serverless the cache is shared within a model, across organisations, projects and API keys. A hit does not reveal who sent the earlier request. On Dedicated Endpoints each customer has an isolated cache. Traffic that arrives through OpenRouter is served as ordinary Serverless traffic, so it shares the same cache [official]. The page says plainly: do not use caching as an access control boundary, and `prompt_cache_key` only helps route to the server that holds the cache [official]. Note the contrast with vLLM, whose prefix cache can mix a cache salt into the block hash to isolate tenants [vLLM v0.32.0 docs]. Nebius does not describe such a salt for Serverless [gap].

---

Custom weights on Dedicated Endpoints are beta and available on request through support. The create schema has `custom_weights_id` [official]. Public Serverless supports base models only [official]. So the loop from logs to fine-tune to dedicated endpoint exists, but each step has an eligibility check. A model missing from the list is a support request with the Hugging Face link and traffic details [official].

---

## FILE docs/part-20-nebius-sre-interview/33-ai-factory-solution-architecture-ha-and-recovery.md

A team may prototype on Public Serverless, run production on a Dedicated Endpoint, and fine-tune on Soperator. Another may build a Kubernetes fleet. Do not force every workload into one product. Ask for an exit path too. If the application calls a gateway you own, you can move the model behind it later without changing the public contract. **Choose a service for the operating burden it removes, not for the GPUs it lists.**

---

Start with the Managed Kubernetes service level [official]. The target is 99.90%. Unavailability means no customer access to the control plane, from inside or outside the platform, for at least five minutes. The credit is 10% of the service fee if uptime falls below 99.90% down to 95.00%, and 25% below 95.00%. The page excludes events beyond Nebius control, control planes that are not the highly available kind, defined as an etcd cluster size of three, outages caused by your firewall or routing rules, disabled clusters caused by an add-on you installed, changed pre-installed add-ons, and end-of-life Kubernetes versions. Nebius gives at least 30 days notice before a version reaches end of life, and after that date the service level no longer applies to the cluster.

---

The operations guide in the same repository gives HA facts you can reuse [official, repository]. Request-path components run two replicas spread over two system nodes: Envoy, LiteLLM, the API, Kueue and Knative Serving. Several reconcile-only components run a single replica on purpose, because an outage delays changes and not traffic. The fleet database is a Managed PostgreSQL cluster with one host by default, and setting two hosts adds a replica with the service's failover. A CronJob recovers stopped spot nodes every two minutes.

---

The customer wants an agent that searches internal data and calls tools with an open model. Prompts may not leave the EU. Reasoning: Public Serverless is out because its region is Global. A Dedicated Endpoint in an EU region is a DPA-backed commitment. Turn ZDR on at the organisation, accepting that speculative decoding is off. Put your gateway, retrieval and evaluation outside the endpoint. For failure, name a second EU region endpoint as the alternate, and check that the template exists there. The answer: Dedicated in an EU region, ZDR, own gateway, written reserved capacity, warm alternate in a second EU region, tested monthly. Record every open item, including the unpublished failover meaning in the "99.9% fail-over" sales line.

---

## FILE docs/part-20-nebius-sre-interview/34-nebius-hardware-data-centers-and-the-gpu-fleet.md

Nebius has not published whether a customer VM on an NVL72 maps to one tray, to several, or to single GPUs. A reasonable design is to assume the tray is the smallest unit that can be repaired and the rack the smallest unit that shares NVLink and cooling [inference].

---

The B200 data centre reference shows how wiring decides blast radius [book, handbook chapter 9.7]. A DGX B200 has six power supplies and needs five energised. Wire three cords to each of two feeds, and losing one feed leaves three of six supplies, so every node in the rack crashes. Wire all six cords of each node to one feed, and losing a feed takes out half the nodes. Use six discrete sources with one cord each, and losing any one source leaves five of six, so no node stops. The book calls the interleaved two-feed model a serious mistake for this reason. The model's `nodes_lost_on_single_feed_failure` function encodes the three cases.

---

The drain rule behind it is the one from chapter [20.16](./16-design-gpu-fleet-health-and-capacity.md) section 7. Automation may act on small, rare events and must hand over to a human when many nodes ask at once. Your layout adds a second limit. Never drain two nodes that hold replicas of the same service in the same domain at once, unless a spare covers the pair [inference].

---

Step time on a training job rises by a third. No node is unhealthy. Check per-rail link state and the leaf in the reference layout. One leaf serves 72 trays, each now at three of four NICs, so 75 percent of scale-out bandwidth. The model's `rail_bandwidth_fraction(4, 1)` returns 0.75. The fix is to route the job away from that leaf or restore it. The point is that capacity fell without a node fault, so a node-health dashboard shows green.

---

## FILE docs/part-20-nebius-sre-interview/35-the-nebius-api-surface-grpc-cli-sdks-iam-and-terraform.md

This catches people. The README says `Update` replaces fields rather than patching them [source-code]. Protobuf drops default values on the wire, so an empty value is indistinguishable from "not sent". The server therefore changes a field only if the request carries a non-default value or the field is named in the `X-ResetMask` header. The mask is not Google's field mask. A resource `{a: {b:1, c:2}}` updated with an empty request and mask `a.b` becomes `{a: null}`, which is surprising.

---

The SDKs manage the header for you. The CLI exposes two modes [official]. Command-line parameters give a patch by default. A file or standard input gives a full update by default, and the docs warn it resets omitted parameters it recognises. `--clear-mask` clears one field in patch mode. For automation this means a script that reads a resource, edits one field and writes it back is correct, and a script that sends only the field it cares about to a full-update path can silently clear the rest. The operation records essential request headers such as `x-resetmask`, so a repeated request is processed the same way [source-code].

---

Now the trap. The docs define `RESOURCE_EXHAUSTED` as quotas exhausted, mapped to HTTP 429 [official]. The SDK also retries that code by default. So a pure quota failure is retried by default unless the server sets `retry_type`. I did not find how the services set `retry_type` for `QuotaFailure`. So my guard in `c35_client_guard.py` refuses to retry `QuotaFailure` and `NotEnoughResources` no matter the code. That is `[inference]`, and a deliberate choice.

---

I measured the budget idea with the guard. One hundred calls that always fail, five attempts each, produce 500 attempts without a budget. With a 10 percent budget and 3 retries in reserve they produce 112 attempts, which is 1.12 per call. I ran that, and it is a simulation, not a Nebius measurement.

---

## FILE docs/part-20-nebius-sre-interview/36-managed-kubernetes-and-soperator-how-nebius-runs-kubernetes-and-slurm.md

With GPU settings on, the node boots an image with the NVIDIA driver and Container Toolkit. The preset `cuda12.8` carries driver series 570.x and `cuda13.0` carries 580.x [official, GPU setup page]. Turn GPU settings off only to install the GPU Operator yourself, for example for MIG, and then the driver lifecycle is yours. For InfiniBand you create a GPU cluster in a fabric and give its id to the node group. The Soperator Terraform recipe rejects a GPU preset without a fabric or cluster id and taints GPU workers `nvidia.com/gpu` with `NO_SCHEDULE` [source-code, `gpu_fabric_validation.tf`].

---

Notice the shape. A GPU fault does not live-migrate anything. The node is cordoned, the job must finish or die, and the VM is stopped and started to land on healthy hardware. Checkpointing is the recovery story for training and replica count is the story for inference.

---

The cluster autoscaler adds nodes for unschedulable pods and removes underused ones, inside each node group's minimum and maximum. A GPU node group that scales to zero needs a CPU node group of at least two nodes so CoreDNS and Cilium have somewhere to run [official, autoscaling page]. Scale-up can still fail on quota, physical capacity or a full reservation, and the autoscaler will not page you about it.

---

`code/part20/c36_node_lifecycle.py` models section 9 minute by minute, with 12 tests. It encodes the first-match reason classifier, no replacement under a running job, a shared budget on nodes in flight, a rate limit on unhealthy reports, oldest-failure-first order, stale-drain cleanup and the NotReady timeout. Budget and report limit are parameters, because Nebius has not published its numbers [inference]. The demo drains five of six nodes with a budget of 2 and 2 reports per 20 minutes. I ran it.

---

## FILE docs/part-20-nebius-sre-interview/37-observability-status-and-operations-on-nebius.md

The first is endpoint state. The Dedicated Endpoint page `[official]` separates lifecycle from readiness. Lifecycle is deployment state: Starting, Updating, Running, Warning, Stopping, Stopped. Readiness is traffic-serving capability: Not ready, Partially ready, Ready. The page says to use readiness to decide whether to send traffic. It also says to contact support if Warning or Partially ready lasts more than three hours. The page uses "Warning" in one place and "Error" in a table, and does not say they are the same.

---

Dedicated Endpoints carry no formal SLA unless a contract covers them `[official]`. I found no Token Factory SLA page. The universal SLA, effective 2026-11-02, pays compensation as a credit against future bills, not cash. You claim through the console within 14 days of the end of the reporting period. Emergency works and planned node maintenance are excluded up to 8 hours per period. Exceeding quotas is excluded. The Compute SLA defines VM unavailability as a missing GPU, NVLink, fabric link, boot disk or external network, and excludes slower bandwidth without loss of connectivity `[official]`.

---

The VM monitoring docs `[official]` list GPU metrics with DCGM names such as `DCGM_FI_DEV_GPU_UTIL` and `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS` (the pre-4.9.0 spelling; dcgm-exporter 4.9.0 renamed the utilisation field to `DCGM_FI_DEV_GPU_UTIL_RATIO`, see 17.4, and I could not confirm a new name for the throttle bitmask), a throttle bitmask where 72 means overheating plus slowdown, and InfiniBand counters for link downs and port errors. They do not mention XID errors. A Nebius blog `[vendor]` describes passive and active GPU health checks and automatic node draining for Soperator and Managed Kubernetes clusters. Nothing says a Token Factory dedicated endpoint exposes any of this, so assume it does not. On your own vLLM fleet, as in [20.33](./33-ai-factory-solution-architecture-ha-and-recovery.md), you scrape these yourself.

---

Nebius has not published its internal telemetry design for Token Factory. What follows is `[inference]` drawn from the public failure modes above and from [20.15](./15-design-an-observability-pipeline-for-very-high-volume.md). Job postings I read for the Compute Node and NetSRE teams name no monitoring product.

---

## FILE docs/part-20-nebius-sre-interview/38-token-factory-inference-engineering-everything-nebius-has-published.md

A Dedicated Endpoint is an isolated deployment. You pick region, GPU type, GPUs per replica and min and max replicas [official]. Capacity comes from an on-demand shared pool. Only the minimum replicas are held, and only while the endpoint is active. There is no formal SLA unless a contract says so [official]. The legal guide adds a hard fact for failure design: dedicated endpoints use no multi-region routing, load balancing or automatic failover to another region [official].

---

Over-limit requests may be processed at lower priority when spare capacity exists, flagged by `x-ratelimit-over-limit: yes` [official]. And the request field `service_tier` takes `auto`, `default`, `over-limit`, `flex` and `no-limit` [official]. `default` returns 429 at the limit. `flex` does not consume rate-limit credits, runs at lower priority and can still return 429. So the admission layer has at least two priority classes and spare-capacity borrowing. How the scheduler enforces priority inside an engine is not published.

---

Fine-tuned weights deploy only through Dedicated Endpoints, and the custom weights path is beta on request [official]. A LoRA adapter on a mixture-of-experts model must be merged into the exact base weights first [official]. That means a merged checkpoint is a new full-size artifact, with its own load time and its own validation, not a small adapter swap. How multi-LoRA serving works, if it exists, is not published.

---

A WEKA-style tier shows 93 versus 40 percent hit rate. Uncached tokens per request were 4,400 versus 33,900, a ratio of 7.7. Requests served in eight hours were 55,694 versus 23,015, which is about 6,960 versus 2,880 per hour. Both numbers come from one replay of agentic coding sessions on one node [vendor], so do not carry them to a chat workload. The SRE question is operational: what does the tier cost in failure modes. Ask what happens when it is slow, when a node holding blocks dies, and whether a miss falls back to recompute within the latency budget.

---

