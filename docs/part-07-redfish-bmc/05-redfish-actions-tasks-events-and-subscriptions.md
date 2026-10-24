---
id: "c07-05"
title: "7.5 Redfish actions, tasks, events and subscriptions"
sidebar_label: "7.5 Redfish actions, tasks, events and subscriptions"
sidebar_position: 5
description: "How to make a BMC do things and hear back from it: Actions such as Reset and what each ResetType means, long-running work with 202 and task monitors, push events and subscriptions, server-sent events, and a 34-check lab on a mock service"
status: "drafted"
tier: "1b"
level: "A"
lab_venue: "GCP / GKE"
---

# 7.5 Redfish actions, tasks, events and subscriptions

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted. `code/part07/actions_lab.py` ran 34 checks against the teaching mock and **all passed** (three repeated runs gave the same result). The mock is not a real BMC. Real BMCs differ in which `ResetType` values they offer, how long a reset takes, whether they answer `200` or `202`, and what events they send |

## Why this matters for AI infrastructure

Reading data is the easy half. The risky half is **doing things**: restarting a node, updating firmware, cutting power. Those operations take time, can fail halfway, and can be refused. A cluster tool must know how to ask, how to wait, and how to learn the result. The same tool also wants to hear about trouble (a fan failed, a power supply dropped) without asking every machine every second. Redfish has a clear answer for each: **actions**, **tasks** and **events**.

## Prerequisites and outcomes

You need 7.1 to 7.4. After this chapter you can:

- find an action on a resource and call it correctly
- explain each `ResetType` and pick the right one
- handle `200`, `202` and `204` answers from an action
- poll a task monitor, show progress and cancel
- subscribe to events and read the event body
- compare push events, server-sent events and polling

## 1. Actions: things you ask a resource to do

Some operations do not fit "read" or "set a value". Restarting a server is not a value you can store. Redfish calls these **actions**. An action is a `POST` to a special address. The spec says the address looks like `<ResourceUri>/Actions/<QualifiedActionName>`, and each resource tells you its actions in its `Actions` section:

```json
"Actions": {
  "#ComputerSystem.Reset": {
    "target": "/redfish/v1/Systems/System_0/Actions/ComputerSystem.Reset",
    "ResetType@Redfish.AllowableValues": ["On", "ForceOff", "GracefulShutdown", "GracefulRestart", "ForceRestart", "Nmi"]
  }
}
```

- `#ComputerSystem.Reset` is the action's name.
- `target` is where to send the `POST`. **Read it from the resource. Do not build it by hand.**
- `ResetType@Redfish.AllowableValues` lists the values **this** system accepts right now. The spec says this list should contain only values that are both supported and currently valid.

You call it with a JSON body of parameters:

```bash
curl -s -u user:pass -X POST -H "Content-Type: application/json" \
  -d '{"ResetType": "GracefulRestart"}' \
  https://<bmc>/redfish/v1/Systems/<id>/Actions/ComputerSystem.Reset
```

Rules from the spec:

- If a required parameter is missing, the answer is **400**. An unknown parameter value also gets **400** (my mock does this for `ResetType`).
- If the action needs no parameters, the service must accept an empty `{}`.
- A `POST` action is not necessarily safe to repeat. Sending it twice may restart twice.
- If an action would change nothing (for example `On` when the system is already on) the service should answer **200** with the `NoOperation` message. My mock shows this.
- If the service refuses (wrong privilege, bad state) you get 4xx/5xx and an error body.

:::tip PATCH versus the action
I tried `PATCH {"PowerState": "Off"}` on the mock and it answered 400, because `PowerState` is read-only. You can only **read** the power state. To change it you run the `Reset` action. Never look for a writable `PowerState`.
:::

### What each `ResetType` means

From the Redfish Resource Guide (2024.4), in plain words:

| Value | Meaning |
|---|---|
| `On` | turn the system on |
| `ForceOn` | turn on immediately |
| `GracefulShutdown` | ask the OS to shut down cleanly, then power off |
| `GracefulRestart` | ask the OS to shut down cleanly, then start again |
| `ForceOff` | turn off immediately, with no clean shutdown |
| `ForceRestart` | shut down immediately and non-gracefully, then start again |
| `PowerCycle` | behaves like removing power and then restoring it |
| `FullPowerCycle` | behaves like removing the utility power lines and restoring them |
| `PushPowerButton` | act as if someone pressed the physical power button |
| `Nmi` | send a diagnostic interrupt (non-maskable interrupt) that normally halts the system for diagnostics |
| `Pause`, `Resume`, `Suspend` | mostly for virtual machines |

How to choose:

1. **Always try the graceful ones first** (`GracefulRestart`, `GracefulShutdown`). They let the OS flush disks and stop services.
2. **Use `ForceRestart` or `ForceOff` only when the OS is frozen.** They can corrupt files and kill running jobs without warning.
3. **`PowerCycle` and `FullPowerCycle`** are stronger. Use them when a restart does not clear a hardware fault.
4. **`Nmi`** is for debugging a hang. Whether the machine then writes a crash dump depends on how the operating system is set up.

:::note Correction to my notes
The NVIDIA-DevOps notes (volume 10, chapter 1) describe `ForceRestart` as "equivalent to pulling the power plug and plugging it back in". By the Resource Guide's wording that is closer to `PowerCycle`. `ForceRestart` is a non-graceful restart. The notes also say `Nmi` "triggers an OS kernel crash dump". The guide says it generates a diagnostic interrupt, which usually halts the system. Producing a dump is up to the OS. I also did not run any of this on a real DGX.
:::

Before you restart a node in a cluster, drain it in the scheduler (chapter 6.14) so no job loses work.

### Other action features to know

- **`@Redfish.ActionInfo`** points to a separate resource describing the parameters (names, types, allowed values) when the list is too large for the inline form.
- **`@Redfish.OperationApplyTime`** (spec 7.12) lets a request say **when** to apply the operation. Values include `Immediate`, `OnReset`, `AtMaintenanceWindowStart` and `InMaintenanceWindowOnReset`, and the resource says which it supports through `@Redfish.OperationApplyTimeSupport`. For example you can delete a storage volume "on the next reset". Services must run pending operations in the order received. I did not build this in the mock.

## 2. Long jobs: 202 and the task monitor

Some operations take longer than a client wants to wait: a firmware update can take many minutes. The service then answers **202 Accepted** instead of 200. That means "I took your request, but I am not finished."

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Redfish service
    C->>S: POST the action
    S-->>C: 202 Accepted, Location is the task monitor, Retry-After 2, Task body
    loop until done
        C->>S: GET the task monitor
        S-->>C: 202 Accepted, TaskState Running, PercentComplete
        Note over C: wait about Retry-After seconds
    end
    C->>S: GET the task monitor
    S-->>C: 200 OK with the result the action would have returned
    C->>S: GET the Task resource
    S-->>C: TaskState Completed, EndTime
```

The facts, from the spec:

- The **task monitor** is an address the service makes up and you must treat as opaque. It usually looks like `/redfish/v1/TaskService/TaskMonitors/<id>`.
- As long as the job is running, a `GET` of the monitor returns **202**. When it ends, the monitor returns the status and body the original request would have returned, as if it had run immediately.
- The `Location` header gives the monitor. An optional `Retry-After` gives how long to wait. A `GET` on the monitor must return right away without blocking.
- The **Task** resource (under `TaskService`) holds the details: `TaskState`, `TaskStatus`, start and end time, `PercentComplete`, and messages.
- To **cancel**, send `DELETE` to the monitor or the Task. If the service allows it, the `Allow` header on the monitor includes `DELETE`. Afterwards the monitor returns 410 or 404.
- A task that has finished and was cleaned up may return 410 or 404 if you wait too long. So read results soon.
- The spec also says `GET`, `PUT` and `PATCH` should always be synchronous, but your client **must** be ready for either answer to any method.

`TaskState` values from the Resource Guide: `New`, `Starting`, `Pending`, `Running`, `Suspended`, `Interrupted`, `Stopping`, `Cancelling`, `Cancelled`, `Completed`, `Exception`, `Service` (and `Killed`, deprecated). `TaskStatus` says the result: `OK`, `Warning` or `Critical`.

A good polling loop:

```text
start = now
response = POST action
if response.status == 200 or 204: done
if response.status == 202:
    monitor = response.headers["Location"]
    loop:
        wait Retry-After (default 2 seconds)
        r = GET monitor
        if r.status == 202: show PercentComplete, continue
        if 200/201/204: success, read body
        if 4xx/5xx: failure, read error body
        if now - start > limit: give up, report "unknown", do NOT assume success
```

The last line matters. A timeout is not a success and it is not a failure. It is "unknown", and a person or a second check must decide.

### In my lab

Turning on the mock's "slow BMC" mode makes the restart action return 202. The lab then moves a fake clock forward:

```text
PASS  slow action: 202 Accepted with a Location task monitor [12.2]
PASS  polling the monitor while running returns 202 [12.2]
PASS  halfway: PercentComplete is about 50
PASS  when done the monitor returns the original operation's result: 200 + Success [12.2]
PASS  the Task resource now says Completed with EndTime
PASS  cancelling a finished task is refused: 409
PASS  cancelling a running task: 204 [12.2]
PASS  monitor of a cancelled task answers 410 Gone [12.2]
```

## 3. Events: hear about trouble without asking

Polling 1,000 BMCs every few seconds is wasteful and slow. Redfish has an **event service**: the BMC tells you when something happens.

### Push events with a subscription

1. Run a small web server that can receive `POST` requests. This is the **destination**.
2. `POST` a subscription to the event service. The body names your destination and what you want to hear.
3. When something matches, the BMC `POST`s an **Event** to your destination.

```json
POST /redfish/v1/EventService/Subscriptions
{
  "Destination": "https://monitor.example/events",
  "Protocol": "Redfish",
  "EventFormatType": "Event",
  "Context": "gpu-rack-7",
  "RegistryPrefixes": ["ResourceEvent"]
}
```

The answer is **201 Created**, with a `Location` header for the new subscription and an `EventDestination` body. If the request has conflicting or unsupported values the answer is **400**. To stop, `DELETE` the subscription. After that the subscription address answers 404.

Properties you can use to choose events (spec 12.1.5):

| Property | Meaning |
|---|---|
| `RegistryPrefixes` | only messages from these message registries (like `Base`, `ResourceEvent`, `Alert`) |
| `MessageIds` | only these messages, written without version numbers (`Resource.ResourceCreated`) |
| `ExcludeMessageIds`, `ExcludeRegistryPrefixes` | never these |
| `ResourceTypes` | only events about these resource types |
| `OriginResources` and `SubordinateResources` | only events about these resources, and optionally everything below them |
| `Context` | text you choose, sent back with each event so you know which subscription it came from |
| `DeliveryRetryPolicy` | what the service does when delivery keeps failing |

Delivery retry policies (Resource Guide): `RetryForever`, `RetryForeverWithBackoff`, `SuspendRetries`, `TerminateAfterRetries`. The event service also has `DeliveryRetryAttempts` and `DeliveryRetryIntervalSeconds`. My lab checks that a subscription to a dead address is **terminated** after three failed deliveries.

An event body, from the lab:

```json
{
  "@odata.type": "#Event.v1_6_0.Event",
  "Id": "3",
  "Name": "Event Array",
  "Context": "gpu-rack-7",
  "Events": [
    {
      "MemberId": "1",
      "EventId": "3",
      "EventTimestamp": "2026-10-24T09:12:44Z",
      "Severity": "OK",
      "Message": "PowerState changed from On to Off",
      "MessageId": "ResourceEvent.1.0.ResourceStatusChanged",
      "OriginOfCondition": { "@odata.id": "/redfish/v1/Systems/System_0" }
    }
  ]
}
```

- `MessageId` follows the pattern `<Registry>.<major>.<minor>.<Name>`. Standard registries define what each means, its severity and a suggested action.
- `OriginOfCondition` points to the resource the event is about. Go and `GET` it to see the current state.
- Several messages with the same `EventGroupId` come from the same cause. For example, a cable pulled may produce a LAN message, a resource-changed message and a state message.

**Rules to remember** (spec 12.1.2):

- **No history.** You get events only after subscribing. The service does not keep old ones.
- **Subscriptions survive restarts** of the service.
- A pushed payload is at most 1 MiB (metric reports excluded).
- A service must not push events to anyone who has not subscribed.
- The spec marks the older `EventType`-based style (life cycle, alert, status change) as deprecated, in favour of registry prefixes and resource types.

### Server-sent events (SSE)

Instead of running a receiver, the client can open a long `GET` to the address in `ServerSentEventUri` in the event service. The connection stays open and the service sends events down it. Facts:

- The response is `200` with `Content-Type: text/event-stream`.
- Each event has an `id:` line and a `data:` line with the Event JSON, with a blank line between events.
- Opening the stream creates a subscription resource, and closing it removes the resource. The lab checks both.
- A client that loses the connection can send `Last-Event-ID` to resume.
- You can filter the stream with `$filter`, for example `MessageId eq 'ResourceEvent.ResourceStatusChanged'`. The event service lists the filter properties it supports in `SSEFilterPropertiesSupported`.

Choosing:

| Method | Good | Watch out for |
|---|---|---|
| **Push subscription** | scales to many BMCs, your receiver is one place | the BMC must reach your receiver, firewalls, retries, you must keep the receiver up |
| **SSE** | simple, works through one outbound connection from you | one open connection per BMC, you must reconnect |
| **Polling** | simplest and most robust | slow, heavy at scale, you can miss short events |

In real fleets people mix them: events for fast alerts and a slow poll as a safety net. Remember, there is no history, so any events lost during an outage are gone, and a periodic poll catches the state.

## 4. How BCM uses this

The BCM Administrator Manual (appendix N) shows BCM subscribing to BMC events:

- `redfishsubscriptions` (in `cmsh` device mode) lists devices with their hostname, subscription id, whether it is initialized and subscribed, IP, kind (`GB300` for compute trays and `GB200SW` for NVLink switches in the example), port 443 and whether SSL is on.
- `redfishevent -m test1` sends a test message so you can confirm delivery. The book's example output shows a warning event such as `[warning] a07-p01-dgx-02-c05: test1`. Running it several times triggers test events from different devices.
- `redfishpost`, `redfishpatch` and `redfishdelete` let an administrator run the same `POST`, `PATCH` and `DELETE` operations described here, across many devices, filtered by node, category or rack.
- `power on|off|reset` in `cmsh` uses the Redfish API on Redfish BMCs. The book says these commands assume AC power to the BMC is on. It uses the term "AC power cycle" for resetting the BMC itself.

I have not run these commands (no BCM cluster). Part 8 covers BCM.

## 5. The lab

```bash
cd code/part07
python3 actions_lab.py
```

It starts a mock service and a small event receiver, then runs 34 checks in groups:

1. discovering the action from the resource, bad parameters, read-only `PATCH`, privileges, the NoOperation answer
2. the 202 and task-monitor flow with a simulated clock, progress, cancel
3. subscriptions: create, receive, filter, unsubscribe, delivery failure
4. server-sent events with a filter

A real error I found while writing it: the SSE check failed in my first run because my test asked for `ForceOff` when the system was already off, so there was no state change and no event. The lesson is a real one. **Events fire on change, not on commands.** A restart that changes nothing sends nothing.

## 6. Exercises

1. Run `actions_lab.py`. Pick the five checks you think matter most for a restart script and explain why.
2. Using `curl`, start the mock (`python3 redfish_mock.py`) and call `Reset` with `GracefulShutdown`. Then read `PowerState`.
3. Write a Python function `wait_for_task(client, monitor, timeout)` following the polling loop above. Test it against the mock in slow mode (`st.async_reset = True` in code).
4. What should your script do when it calls `Reset` and gets a `504` from a gateway? (Hint: do not assume it failed. Read `PowerState` and the log first.)
5. Design the event path for 500 BMCs: one receiver or several, retry policy, what you store, and the poll fallback.
6. Explain why an event body should lead you to `GET` the origin resource instead of trusting the event alone.

## 7. Interview angles

- "Redfish returned 202. What now?" Follow the `Location` task monitor with `Retry-After`, report progress, handle the final result, set a time limit, and treat a timeout as unknown.
- "How do you restart 100 nodes safely?" Drain first, use the graceful `ResetType`, restart in small batches, wait for each to return, and stop on the first failure.
- "Push events or polling?" Both: events for speed, polling as a safety net, because events have no history.
- "What is the difference between `ForceRestart` and `PowerCycle`?" Non-graceful restart versus removing and restoring power. Use the weakest option that works.

## 8. Checkpoint questions (20)

1. What is a Redfish action?
2. Where do you find the address of an action?
3. What does `ResetType@Redfish.AllowableValues` give you?
4. What status do you get for a missing action parameter?
5. Why can you not change `PowerState` with `PATCH`?
6. What does `GracefulRestart` do that `ForceRestart` does not?
7. When would you use `PowerCycle`?
8. What does a `200` with `NoOperation` mean?
9. What does `202 Accepted` mean?
10. Which headers come with a `202`?
11. What does a `GET` on a task monitor return while the job runs? When it ends?
12. How do you cancel a task?
13. What should a script do on timeout?
14. What are `TaskState` values `Running`, `Exception` and `Cancelled`?
15. How do you create an event subscription and what comes back?
16. What is `Context` for?
17. Why do you get no old events?
18. What happens to a subscription after repeated failed deliveries with `TerminateAfterRetries`?
19. How does SSE differ from a push subscription?
20. Why should event delivery have a polling fallback?

## 9. Sources and review notes

- **Redfish Specification DSP0266 v1.21.0:** `POST` (action) rules and status table (7.11), operation apply time (7.12), eventing, subscription properties and event formats (12.1), asynchronous operations and task monitors (12.2), server-sent events (12.5). I read these clauses.
- **Redfish Resource and Schema Guide DSP2046 (2024.4):** `ComputerSystem` `ResetType` and `PowerState` definitions, `Task` and `TaskState`, `EventDestination` (`DeliveryRetryPolicy`, `SubscriptionType`), `EventService`.
- **BCM 11 Administrator Manual**, appendix N: `redfishsubscriptions`, `redfishevent`, `redfishpost`, `redfishpatch`, `redfishdelete`, and Redfish-based power control.
- **NVIDIA-DevOps notes (volume 10 chapter 1):** the Reset example and `ResetType` list. See the correction in section 1.
- **Run here:** `actions_lab.py` (34 checks).
- **Not verified:** real BMC behaviour (timing, which `ResetType` values exist, event content, event registries). The mock sends one simplified event type. The `@Redfish.OperationApplyTime` and `@Redfish.ActionInfo` features were read in the spec but not built or tested.
