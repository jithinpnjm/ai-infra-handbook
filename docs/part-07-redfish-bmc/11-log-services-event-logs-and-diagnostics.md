---
id: "c07-11"
title: "7.11 Log services, event logs and diagnostics"
sidebar_label: "7.11 Log services, event logs and diagnostics"
sidebar_position: 11
description: "How to read what a BMC remembers: log services, event log entries and the IPMI-style SEL, severities and message IDs, full logs and overwrite policy, clock problems, clearing safely, and collecting a diagnostic bundle for support, with a log reader and a 23-check lab"
status: "drafted"
tier: "1b"
level: "I"
lab_venue: "GCP / GKE"
---

# 7.11 Log services, event logs and diagnostics

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted. `code/part07/rf_logs.py` and `logs_lab.py` were **run**: 23 checks pass. The tool was also run on DMTF's example trees. The log contents of my mock are invented, and a "diagnostic bundle" from the mock is a short text file. No real BMC log was read. What real DGX BMCs log, and the exact log paths, are **not verified** |

## Why this matters for AI infrastructure

When a job dies with a CUDA error and the operating system logs show nothing, the cause may be a hardware event that only the BMC saw: a memory error, a power supply drop, a fan failure, an over-temperature trip, a PCIe fault. The BMC keeps its own memory of the machine, and that memory survives the crash and even a power loss of the host. When you ask a vendor for help, they will want a **diagnostic bundle** collected from the BMC. Reading and collecting these logs is a core skill.

## Prerequisites and outcomes

You need chapters 7.2, 7.3, 7.5 and 7.7. After this chapter you can:

- find every log on a Redfish service
- read a log entry and explain its fields
- tell Redfish event entries from IPMI SEL entries
- explain overwrite policies and why a full log can hide the event you need
- spot a BMC clock that makes logs misleading
- clear a log safely and collect a diagnostic bundle
- use logs together with sensors and GPU tools to find a cause

## 1. Where logs live

Logs are kept by **log services**. A log service is a resource of type `LogService`, found under the thing it belongs to:

| Owner | Path pattern | Usually holds |
|---|---|---|
| Manager (BMC) | `Managers/<id>/LogServices/<log>` | BMC events, hardware events, audit of BMC actions |
| System | `Systems/<id>/LogServices/<log>` | events about the computer: boot, memory, processors |
| Chassis | `Chassis/<id>/LogServices/<log>` | events about the box |

Names such as `EventLog`, `SEL`, `Log` or `Dump` are choices of the maker. Always discover them by following the `LogServices` link. In my tool a single function does this:

```bash
python3 rf_logs.py services http://<bmc> <user> <password>
```

On my mock it prints:

```text
Manager  BMC_0        EventLog   type=Event  entries=0/200 policy=WrapsWhenFull
Manager  BMC_0        SEL        type=SEL    entries=0/200 policy=WrapsWhenFull
System   System_0     EventLog   type=Event  entries=0/200 policy=WrapsWhenFull
```

A `LogService` has these useful properties (from the schema):

| Property | Meaning |
|---|---|
| `Entries` | link to the collection of entries |
| `LogEntryType` | what the entries look like: `Event`, `SEL`, `Multiple`, `OEM`, `CXL` |
| `MaxNumberOfRecords` | the capacity |
| `OverWritePolicy` | what happens when full: `WrapsWhenFull` (old entries are overwritten) or `NeverOverWrites` (new entries are discarded) |
| `LogPurposes` | `Diagnostic`, `Operations`, `Security`, `Telemetry`, `ExternalEntity`, `OEM` |
| `DateTime`, `DateTimeLocalOffset` | the log service's clock |
| `ServiceEnabled`, `Status` | on or off, health |
| `SyslogFilters` | rules for which syslog messages are stored |

Its actions: `ClearLog`, `CollectDiagnosticData`, `DownloadRawLog` and `PushDiagnosticData`.

## 2. A log entry

Two kinds are common.

**Event entries** (`EntryType: Event`) follow the Redfish message design from chapter 7.5 and 7.6: a `MessageId` points into a message registry. From my mock after a power-off:

```json
{
  "EntryType": "Event",
  "Severity": "OK",
  "Created": "2027-01-15T08:00:05Z",
  "Message": "PowerState changed from On to Off",
  "MessageId": "ResourceEvent.1.0.ResourceStatusChanged",
  "MessageArgs": [],
  "Links": { "OriginOfCondition": { "@odata.id": "/redfish/v1/Systems/System_0" } }
}
```

**SEL entries** (`EntryType: SEL`) are the old IPMI **System Event Log**: compact records that the BMC translates. The `MessageId` field then holds raw event data, and `SensorType`, `SensorNumber` and `EntryCode` carry the meaning (the schema says `EntryCode` is used if the type is `SEL`). A SEL record in DMTF's example reads *"Temperature threshold exceeded"* with `MessageId: 0x592A28`, a code that you read with the IPMI documentation.

Fields you will use:

| Field | Meaning |
|---|---|
| `Id` | the entry number in this log |
| `EntryType` | `Event`, `SEL`, `Oem` or `CXL` |
| `Severity` | `OK`, `Warning` or `Critical` |
| `Created` | when the BMC wrote the entry |
| `EventTimestamp` | when the event happened (may differ from `Created`) |
| `Message`, `MessageId`, `MessageArgs` | the text, its registry key and arguments |
| `Links.OriginOfCondition` | the resource the event is about, so you can `GET` it |
| `EventGroupId` | entries with the same value share one cause |
| `SensorType`, `SensorNumber`, `EntryCode` | for SEL entries. `SensorType` values include `Temperature`, `Voltage`, `Fan`, `Memory`, `Processor`, `Power Supply / Converter`, `Drive Slot/Bay`, `Watchdog` and many more |
| `Resolved`, `Resolution`, `ResolutionSteps` | whether the cause is fixed and suggested fixes |
| `AdditionalDataURI`, `AdditionalDataSizeBytes`, `DiagnosticDataType` | attached data, for example a diagnostic bundle |

**Collections of log entries come with their members inline.** The spec says the `Members` property of a `LogEntryCollection` is expanded by default (so `Entries`, `Entries?$expand=.` and `Entries?$expand=.($levels=1)` give the same answer). My lab confirms the mock does this. That saves one request per entry. For long logs use paging (`$top`, `$skip`, the `nextLink`).

## 3. The tool: read, filter and group

```bash
python3 rf_logs.py show http://<bmc> <user> <password> --min Warning --since 2026-10-24T00:00:00Z --grep fan
```

It reads every log service, normalises the entries, applies your filters and prints them in time order. Results on DMTF's rack-server example with `--min Critical`:

```text
2012-03-07T14:44:00Z BMC/Log      Critical Event.TempWayTooHot            System May be Melting
2012-03-07T14:44:00Z 437XR1138R2/Log1  Critical 0x592A28   Temperature threshold exceeded
2012-03-07T14:45:00Z 437XR1138R2/Log1  Critical 0x592E28   Temperature threshold exceeded
3 entries
```

and on the blade enclosure example: `Fan 2 crossed Lower Fatal Threshold; fans are no longer redundant` (from the enclosure manager).

The lab shows that related entries can be grouped. Two entries "Fan 3 speed low" and "Fan 3 redundancy lost" carry the same `EventGroupId`, so one problem does not look like two.

### Using a log in an investigation

Take the "mystery crash" from the user's notes (volume 10, scenario 4): a PyTorch job dies with a CUDA illegal memory access, and the OS logs show nothing obvious. The notes' answer is to cross-check the software side with the BMC side:

1. On the host, check GPU memory error counters (for example `nvidia-smi -q -d ECC`).
2. On the BMC, read the event log entries around that time. The notes name `GET /redfish/v1/Managers/BMC/LogServices/EventLog/Entries` and look for memory parity errors, PCIe AER fatal events and processor machine check exceptions.
3. Find the component. A fault on a host DIMM means drain the node and replace the DIMM. A fault on a GPU means run a targeted GPU test to see whether it repeats.

I have not run this on a real DGX. The point is the method: **put the BMC log and the host logs on one timeline**. That only works if both clocks are right (see section 5).

## 4. What the log tells you about itself

A log can mislead if it is full or if its clock is wrong. The tool checks both.

**Overwrite policy.**

| Policy | When full | Risk |
|---|---|---|
| `WrapsWhenFull` | the oldest entries are replaced | the first sign of trouble, which is often the most useful, disappears under later noise |
| `NeverOverWrites` | **new** entries are discarded | the log silently stops recording just when something bad is happening |

My lab shows both. With a 5-entry limit, `WrapsWhenFull` kept the newest five entries (ids kept counting) and with `NeverOverWrites` a new Critical entry was dropped. The tool warns when a `NeverOverWrites` log is 80 percent full or more, and when a wrapping log is 95 percent full. Whichever policy your BMC uses, **forward** important entries to a central place (events, chapter 7.5) so they are not lost.

**Clock.** Log entries carry the BMC's time. If the BMC never had NTP configured, its clock may be hours or years off, and entries will not match your host logs. The tool compares each service's `DateTime` with the clock of the computer running the tool and warns if they differ by more than five minutes. In the DMTF examples this warning fires on every service because the sample dates are from 2012 to 2016. That is the correct behaviour for stale data, and a reminder to check the BMC's NTP setting (`NetworkProtocol`, chapter 7.15) when you bring a node in.

## 5. Clearing a log

`ClearLog` empties the log. Treat it like deleting evidence.

- **Collect first.** Take a diagnostic bundle (next section) or at least copy the entries.
- **Use the ETag guard.** The action has a parameter `LogEntriesETag`. If you send the ETag of the entries collection that you read, the service refuses with `412` when the log changed since, so you do not wipe entries you never saw. My lab proves it: a stale ETag gives 412, the current one gives 204.
- **Check privileges.** A read-only user gets 403.
- The tool's `clear` command is a **dry run unless `--yes`** is given.

## 6. Diagnostic bundles: `CollectDiagnosticData`

A vendor's support team usually wants a bundle: a file with logs and state from the BMC. Redfish defines the action `LogService.CollectDiagnosticData`. Its parameter `DiagnosticDataType` can be `Manager`, `PreOS`, `OS`, `OEM` or `Device`. It can also send the data to a `TargetURI` with a user name and password, or keep it in the BMC.

How it works (spec and schema):

1. `POST` the action. The answer is `202` with a task monitor, because collecting takes time.
2. When the task ends, **its `Location` header is the new `LogEntry`**, and that entry's `AdditionalDataURI` is where you download the data.
3. `GET` the `AdditionalDataURI`. Compare the number of bytes with `AdditionalDataSizeBytes`.

`rf_logs.py collect` does all of that and checks the size:

```bash
python3 rf_logs.py collect http://<bmc> <user> <password> --out bundle.bin
```

On my mock the tool printed `saved 150 bytes to bundle.bin (log entry 3, Manager)`. (The mock's bundle is only a few lines of text.) A deliberately corrupted size field makes the tool stop with exit code 7 and the message `size mismatch`. A real bundle can be many megabytes, so give the request time and do not assume success if the download is cut off.

On NVIDIA DGX the user's notes mention `nvsm dump health`, which "packages all system logs, configuration files and hardware states" for NVIDIA support. That runs on the host operating system and is a different route from the BMC bundle. For an RMA you usually need both. I did not run either.

## 7. The lab

```bash
cd code/part07
python3 logs_lab.py
```

It runs 23 checks:

```text
PASS  3 log services are found by following links: manager EventLog, manager SEL, system EventLog
PASS  a power state change is written to the manager event log (2 entries, members inline)
PASS  each entry has EntryType Event, a MessageId, Severity, Created and the origin resource
PASS  $top=1 pages the log and gives a nextLink
PASS  log service, collection, an Event entry and an SEL entry validate against the official schemas
PASS  filtering at Critical finds the SEL entry, with its sensor type and entry code
PASS  entries with the same EventGroupId can be grouped (same cause)
PASS  WrapsWhenFull keeps the newest 5 entries and drops the oldest (ids keep counting up)
PASS  NeverOverWrites discards new entries when full
PASS  the tool warns about a full NeverOverWrites log
PASS  the tool warns when the BMC clock differs from ours by 2000 s
PASS  ClearLog with a stale LogEntriesETag is refused (412): the log changed since you looked
PASS  a ReadOnly user cannot clear a log (403)
PASS  CollectDiagnosticData is a long action: 202 with a task monitor
PASS  when the task ends, its Location header is the new LogEntry, which has the download address (schema rule)
PASS  the tool detects a size mismatch between the entry and the downloaded data (exit 7)
...
23 passed, 0 failed
```

One real bug the schema check caught while I built this: I had put `OriginOfCondition` at the top of the log entry. The official `LogEntry` schema has it under `Links`. My first version of the mock and the tool both got it wrong, and the validator told me.

## 8. Logs in a fleet

- **Centralise.** Do not rely on each BMC's small log. Subscribe to events (chapter 7.5), or poll and ship entries to a log system, with the BMC name and the original timestamp.
- **Fix clocks** on every BMC with NTP before the machine goes into service.
- **Alert on Critical entries** and on the log-health warnings above.
- **Collect bundles** before any repair that might reset the BMC or erase state.
- **Tie logs to jobs.** The scheduler knows which job ran on a node when an event happened.
- **Keep sample logs** from healthy nodes. Knowing what normal chatter looks like makes the unusual entry stand out.

## 9. Exercises

1. Run `logs_lab.py` and `rf_logs.py services` on the mock. Cause three events (reset the system) and read them with `show`.
2. Serve DMTF's blade example and run `rf_logs.py show --min Warning`. Which manager reported the fan problem and why that one?
3. Set a tiny `MaxNumberOfRecords` and `NeverOverWrites` on the mock (see the lab). Show the warning from the tool.
4. Write down the steps you take to prepare a node for an RMA: which bundles, in which order, and what you record.
5. A log entry has `Created` two hours later than your host's `dmesg` for the same event. Give three possible explanations.
6. Add a `--json` flag to `rf_logs.py show` that prints entries as JSON lines.

## 10. Interview angles

- "A GPU job crashed with no OS errors. Where do you look?" BMC event log and SEL around the crash time, GPU error counters on the host, sensors for heat and power, put on one timeline.
- "What is the SEL?" The IPMI System Event Log, a compact legacy log that Redfish exposes as `EntryType: SEL`.
- "Why can a full log be dangerous?" `NeverOverWrites` drops new events, and wrapping loses old ones.
- "How do you gather evidence before a repair?" A diagnostic bundle through `CollectDiagnosticData`, plus the host-side bundle, before clearing anything.
- "How do you tell if two log entries are the same incident?" `EventGroupId` and `OriginOfCondition`.

## 11. Checkpoint questions (20)

1. Where are log services found?
2. What are the two common `EntryType` values and how do they differ?
3. What do `Severity` values mean?
4. What is `MessageId` and what is it a key to?
5. What is `OriginOfCondition` for? Where is it in the entry?
6. What is `EventGroupId` for?
7. What do `SensorType` and `EntryCode` mean for a SEL entry?
8. Why are `LogEntryCollection` members inline by default?
9. What does `OverWritePolicy: NeverOverWrites` do when the log is full?
10. Why can `WrapsWhenFull` also hide the cause?
11. Why check the BMC clock before reading logs?
12. What does the `LogEntriesETag` parameter of `ClearLog` protect against?
13. Why collect a bundle before clearing?
14. What does `CollectDiagnosticData` return first?
15. Where do you find the download address of the bundle?
16. How do you check that the download is complete?
17. Name three `DiagnosticDataType` values.
18. What is `nvsm dump health` and how does it differ from a BMC bundle?
19. Why centralise BMC logs?
20. How do logs, sensors and GPU tools fit together in an investigation?

## 12. Sources and review notes

- **Redfish Resource and Schema Guide DSP2046 and the official JSON Schemas:** `LogService` v1.9 and later (properties, `OverWritePolicy`, `LogEntryTypes`, `LogPurpose`, the actions, `LogDiagnosticDataTypes`) and `LogEntry` v1.22 (`EntryType`, `SensorType`, `Links`, attachments). I read the property descriptions and the action definitions, including the rule that the finished task's `Location` is the `LogEntry`.
- **Redfish Specification DSP0266 v1.21.0:** expanded resource annotation (`LogEntryCollection` members, 9.13.11 and `$expand`, 7.3.2), tasks and monitors (12.2).
- **DMTF example trees** at commit `fa6d23d9` (rack server, blade enclosure, local storage).
- **NVIDIA-DevOps notes:** volume 10 chapter 1, scenario 4 (memory errors and the BMC event log path) and section 8 (`nvsm dump health`). Volume 20's chapters on GPU driver crashes, Xid errors and DMA/PCIe problems (examples marked illustrative by their authors) are routed to other chapters and not used here.
- **Systems Performance (Gregg), Appendix A (USE method for Linux):** used only for the general idea of checking error counters as a standard step.
- **Run here:** `rf_logs.py` on the mock and on three DMTF trees, `logs_lab.py` (23 checks).
- **Not verified:** the content and paths of real BMC logs, how long real bundles take, bundle contents, and the behaviour of real DGX `EventLog` and SEL. The `ipmitool sel` command is a well-known way to read the SEL but I did not run it.
