---
id: "c20-16"
title: "20.16 Design: GPU fleet health and capacity"
sidebar_label: "20.16 Design: GPU fleet health"
sidebar_position: 16
description: "A system design for finding a failing GPU before the customer does: health signals and the Xid catalog, passive and active checks, the node lifecycle from cordon to return, blast-radius limits on automation, spare pool sizing with arithmetic, silent capacity loss, draining inference traffic, a fleet capacity SLO and the vendor RMA flow, with a tested state machine, drain limiter, spare-pool calculator and a promtool-checked rule file."
status: "drafted"
tier: "1"
level: "I"
lab_venue: "Laptop / Docker"
---

# 20.16 Design: GPU fleet health and capacity

## What the interviewer is testing

The question is about GPUs, the graphics processing units that run AI models, and the interviewer wants to hear a plan rather than a product name. The interviewer says: "Design a system that detects a failing GPU before the customer does, using health checks, telemetry and automatic hardware replacement." This is the system design round. One public source reports this as a Nebius prompt, but it is a secondary source and I could not verify it as an actual question. The posting lists "incident detect/isolate/remediate with automation and runbooks" and "self-healing systems". It also asks for knowledge of "how distributed back-ends fail".

A single clever alert is the easy part, and many candidates stop there. The harder part is a loop: notice a problem, decide what it means, remove the node from service, repair it, prove it works, and only then return it. You must also show that the loop cannot hurt you. An automation that drains the fleet because one bad driver fired a false alarm is worse than no automation at all, and the interviewer is listening for that second half.

Nebius has not published its health system, so everything below about its design is my reasoning, and I label it as such. What is public is the failure that motivates the question. The Nebius chat-app case study says restarted workers sometimes did not rejoin the pool, so capacity shrank silently. It also says the team used X+1 redundancy, which means one spare unit beyond what the load needs. Both ideas run through this chapter. Keep the case study in mind as you read, because it explains why the design cares about nodes that are missing without anyone noticing.

In a real round the follow-up often arrives while you are still drawing, and it is usually a question about limits. For example: "Your automation just cordoned four nodes in ten minutes. Should it cordon a fifth?" The strong answer is a number, a reason and a human. Give the number that limits the automation, the reason that number exists, and the person who gets called when the limit is hit.

## The core ideas

### 1. A failing GPU shows up in three places before the customer notices

![Three columns for hardware counters, physical state and workload comparison, with the workload check catching quiet throttling.](./img/p3-2016-three-places.svg)

*Figure 20.16.1. Comparing a replica to the fleet median catches the slowdown that no counter reports.*

Picture a replica serving a model on eight GPUs, the processors that do the arithmetic for the model. One GPU starts to overheat and slows down. Every token step waits for the slowest GPU, so the whole replica gets slower. A token is a short piece of text the model writes, one after another. The customer sees a worse time to first token, which is the wait before the first word of the answer appears, long before anything crashes. The failure is real, but no error appears anywhere, and that is exactly why it is hard to catch.

So where should a design look? You can catch that failure in three places. The hardware reports its own errors, which are Xid messages, ECC counters, PCIe replays and NVLink errors. Xid is NVIDIA's numbered code for GPU faults. ECC means error-correcting memory, and its counters tell you when memory had to fix a bit. PCIe is the bus that connects the GPU to the host machine, and NVLink is the fast link between GPUs. The physical state shows stress, which means temperature, power and clock throttling. Throttling is when the GPU slows itself down to protect its hardware. The workload shows the effect, which means tokens per second per GPU compared with its peers. A good design watches all three, because each one misses failures that the others catch.

The third place is the one most designs skip, and it catches the quiet failures. Think of a runner who slows down without limping. A throttled GPU raises no Xid, so the error log stays clean. The check that finds it is a comparison. Compare each replica to the fleet median for the same model and GPU type. The median is the middle value when you line up all the replicas by speed. A replica that is 30 percent slower for an hour is suspect even when every hardware counter is quiet. That comparison is my own suggestion and the 30 percent is a placeholder, not a vendor figure.

**Watch the hardware, the physical state and the workload, because each one hides failures from the others.**

### 2. The signals, with their real names

![A timeline where the Xid gauge stays at 79 after repair and a naive equals-79 alert keeps firing.](./img/p3-2016-xid-gauge-trap.svg)

*Figure 20.16.2. Alert on the Xid value together with how recently it changed.*

It is the middle of the night and an alert names a metric you have to explain on the spot. Before anyone acts, you must say what it means. NVIDIA's DCGM exporter publishes GPU counters as Prometheus metrics on port 9400. DCGM is NVIDIA's data center GPU manager, and the exporter is the small program that turns its counters into a format Prometheus can scrape. The version I checked is 4.9.0, released 2026-11-06. An important detail: in that release's default counter file, the ECC, throttle and NVLink error counters are present but commented out. You must enable them in your own counters file before they appear. Metric names have also changed between releases, so check `/metrics` on your version before you copy a name. The exporter listens on `:9400` by default. In the 4.9.0 source, GPU series carry the labels `gpu`, `UUID`, `pci_bus_id`, `device` and `modelName`, and host-level series carry `hostname`. The `UUID` label name is selectable in the source, so confirm it on your build. In Kubernetes, `pod`, `namespace` and `container` labels appear only when the exporter's pod mapping is enabled. Labels are the key-value tags on each series, and they let a query narrow down to one GPU or one node. The rules in this chapter select on `instance` and `gpu`.

Of all the signals, the Xid number is the one an on-call engineer reads first. DCGM gives it as `DCGM_FI_DEV_XID_ERROR`, a gauge. A gauge is a metric that holds one current value, and this one holds the value of the last Xid seen. That has a trap. The value stays at 79 until another Xid replaces it or the exporter restarts. An alert on "equals 79" therefore keeps firing after the node is repaired unless you also check recency. Recency means checking when the value last changed, not only what it says. Counters such as `DCGM_EXP_XID_ERRORS_TOTAL` exist in the file but are commented out too. A counter only goes up, so it answers "how many times", while the gauge answers "what happened last".

| Signal | DCGM exporter 4.9.0 metric | Enabled by default | What it tells you |
|---|---|---|---|
| Last Xid | `DCGM_FI_DEV_XID_ERROR` | yes | Which fault, by catalog number |
| GPU temperature | `DCGM_FI_DEV_GPU_TEMP_CELSIUS` | yes | Cooling problem, or a sick sensor |
| Power draw | `DCGM_FI_DEV_BOARD_POWER_WATTS` | yes | Load and power cap behaviour |
| PCIe retries | `DCGM_FI_DEV_PCIE_REPLAY_TOTAL` | yes | A flaky link between host and GPU |
| Row remap failed | `DCGM_FI_DEV_ROW_REMAP_FAILED` | yes | Memory repair has run out of spare rows |
| Rows remapped | `DCGM_FI_DEV_ROW_REMAP_UNCORRECTABLE_TOTAL` | yes | Memory wearing out |
| Double-bit ECC | `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL` | no, enable it | Uncorrectable memory error |
| Thermal throttle | `DCGM_FI_DEV_GPU_THERMAL_THROTTLE_SECONDS_TOTAL` | no, enable it | Time spent below application clocks from heat |
| Power throttle | `DCGM_FI_DEV_GPU_POWER_THROTTLE_SECONDS_TOTAL` | no, enable it | Same, from the power policy |
| NVLink CRC errors | `DCGM_FI_DEV_NVLINK_CRC_ERROR_TOTAL` | no, enable it | Link errors, Hopper counter |

AI Systems Performance Engineering, chapter 16, says that DCGM tracks Xid counters and exposes throttling reasons through a field it names `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS`. Read that sentence as a lead to check, not as a fact about your exporter. That older field name is not in the 4.9.0 default file, which is a reminder to verify names against your own exporter. The same chapter says the exporter does not expose per-link NVLink bandwidth on all platforms by default. Per-link means one number for each separate NVLink connection, so a platform that does not expose it leaves you guessing about which link is slow.

**Verify each metric name against `/metrics` on your exporter version before you write an alert on it.**

### 3. What each Xid means for the fleet

![An Xid code is ignored, marked suspect, or drained, depending on its catalog action and on whether an application-level code repeats three times within an hour.](./img/x16-xid-policy.svg)

*Figure 20.16.3. The catalog says what one GPU needs, and the fleet policy turns that into ignore, suspect or drain while remembering repeats on each node.*

Now the alert says "Xid 79", and the kernel log shows the same line. An on-call engineer needs to know what to do in the next minute, not in the next hour. NVIDIA's Xid catalog gives each code an immediate action. I fetched it on 2026-11-09. The page shows no version number, so treat the table below as a snapshot and not as a permanent fact. When the catalog's action and your own policy disagree, write down the reason before you act.

| Xid | Catalog meaning | Immediate action in the catalog |
|---|---|---|
| 13 | Graphics engine exception, usually an application fault | Restart the application |
| 31 | GPU memory page fault, an illegal address access | Restart the application |
| 43 | GPU stopped processing | Ignore (investigatory action: contact support) |
| 45 | Preemptive cleanup after other errors | Depends on whether it is alone |
| 48 | Double-bit ECC error | Follow the catalog's Xid 48 workflow |
| 63 | Row or page remapping event | Ignore |
| 64 | Row or page remapping failure | Reset the GPU |
| 74 | NVLink error to another GPU or NVSwitch | Decode the registers, then contact support |
| 79 | GPU inaccessible over PCIe, "fallen off the bus" | Restart the bare metal node (investigatory action: contact support) |
| 94 | Contained memory error, one application | Restart the application |
| 95 | Uncontained memory error | Reset the GPU |
| 119, 120 | GSP timeout or error | Reset the GPU |

The catalog describes what to do for one GPU. A fleet design has to turn that into a policy that works for thousands of GPUs at once. My policy, which Nebius has not published, has three outcomes. Ignore codes that the catalog says to ignore. Mark the node suspect for application-level codes such as 13 and 31 on first sight, because a customer's bad prompt or kernel can cause them. A kernel is a small program that runs on the GPU. Drain the node at once for codes that need a reset or a reboot. Draining means moving work off the node before it is repaired.

A lookup table alone is not a policy, and that is the mistake to avoid in the room. If you read the catalog row and act on it with no memory, a node that throws the same application error every ten minutes will be treated as new each time. The policy needs state. It must remember what this node has already reported, and for how long, so that a repeated warning can become a decision. That memory is why the code below keeps a list of recent Xid times for each node. The catalog tells you what the code means. Your policy tells you what the fleet should do about it, and the second step is yours to defend.

One rule turns suspects into drains, and it exists because a single application error is often noise. The same application-level Xid three times within an hour on one node looks like hardware, not a user bug. The three and the hour are my starting values. Think of it as a fuse that blows only when the same wire heats up again and again. An unknown Xid is never ignored. It becomes a suspect, so that a new failure type cannot slip past silently.

**Translate the catalog into three outcomes, ignore, suspect and drain, and never ignore a code you do not recognise.**

### 4. Passive and active checks

![Passive versus active checks with the four dcgmi diag levels, their durations, and where each runs in the lifecycle.](./img/p3-2016-passive-active-ladder.svg)

*Figure 20.16.4. Use passive checks to find faults and active checks to prove a node before it returns.*

A passive check reads what the hardware already reports, and it is the first thing a fleet monitor should run. Picture a smoke alarm that only sounds when smoke is already in the room. That is cheap and always on, and it is what a passive check is. Its weakness is that it only sees faults that already produced an error. An active check does work on the GPU and compares the result with what a healthy GPU does. It finds weak hardware that has not failed yet, but it uses the GPU, so the node usually has to be out of service while it runs.

DCGM ships an active check, `dcgmi diag`, with four run levels. You pick the level before the run, and the higher levels take longer. The documentation gives the durations below. The Diagnostic plugin multiplies large matrices while watching for Xids, temperature violations and memory errors. Multiplying large matrices is a heavy workload that pushes the GPU hard, and that is the point of the test. The same heavy work is why it cannot share the GPU with customer work.

| Level | Command | Purpose | Duration limit in the docs |
|---|---|---|---|
| 1 | `dcgmi diag -r 1` | Quick check of software, driver and permissions | under 2.5 seconds |
| 2 | `dcgmi diag -r 2` | Extended validation | under 2.5 min on 4 GPUs, under 10.5 min on 8 |
| 3 | `dcgmi diag -r 3` | Hardware diagnostics including stress, power, bandwidth and NCCL tests | under 10 min on 4 GPUs, under 35 min on 8 |
| 4 | `dcgmi diag -r 4` | Adds memory test and power pulse test | under 45 min on 4 GPUs, under 2.25 h on 8 |

Automation needs to read the result without a human in the loop. Exit code 0 means success, and 226 means the diagnostic ran and reported an error. Add `-j` for JSON output that automation can parse, which is safer than scraping text. None of this ran on my Mac, since it needs an NVIDIA GPU and DCGM. Treat the commands as documented, not tested.

The book Supercomputers for Linux Sysadmins, chapter 3, lists the checks to plan for. Those are a full cluster check after maintenance, a node performance check after a fix or replacement, a node readiness check before and after a job, and a periodic node health check. The same chapter says not to run checks from cron jobs that ssh into every node. Cron is the Linux scheduler for recurring jobs, and ssh is the remote login tool. My reading is that one central job logging into every node becomes a bottleneck. Use local timers on each node, save results to shared storage or a queue, and process them on a service node. That advice maps cleanly onto the design here.

My mapping is reasoning, not Nebius practice, and it is simple. Passive signals run continuously on every node. A quick level 1 check runs when a node is about to take traffic. A level 3 run is the gate when a node leaves repair. A multi-node NCCL test is the gate for a node that will join a training or large tensor-parallel group. NCCL is NVIDIA's collective communication library, the library that moves data between GPUs during training. Tensor parallelism splits one model across several GPUs. For Slurm clusters, Part 6 chapter 14 shows the same idea as a health check program that drains a node on failure. Slurm is the workload scheduler many HPC clusters use.

**Use passive checks to find faults, and use active checks to prove a repaired node before it returns.**

### 5. Kubernetes node problem detector: where it fits

![Three boxes for detect, decide and act showing node problem detector feeding a custom controller that calls cordon and drain.](./img/p3-2016-detect-decide-act.svg)

*Figure 20.16.5. Node problem detector reports problems but the repair logic is yours to build.*

The signals above live in GPU land, but Kubernetes only sees nodes, so somebody has to carry the news across. The Kubernetes documentation describes node problem detector as a daemon that collects node problems from various daemons and reports them to the API server as node conditions or as events. A daemon is a background program that runs on every node, and the API server is the front door of the cluster's control plane. A condition marks a lasting state of the node. An event reports something that happened once. Think of a condition as a sign on the door and an event as a note in the logbook.

I read the whole node problem detector page on 2026-11-09. It says the daemon reports problems as node conditions for permanent faults and as events for temporary ones, and it says nothing about repair. That silence is useful. It tells you that detection and remediation are separate jobs, so you must build the repair part yourself. My reading is that a controller of your own watches the conditions, applies the policy from section 3, and calls the cordon and drain APIs. A controller is a program that keeps comparing what you want with what you have, and then acts to close the gap. The capstone in Part 19, chapter 6, builds such a controller and the Go code lives in `code/gpuhealth`. The GPU Operator, described in Part 11 chapter 4, deploys the driver, the DCGM exporter and the validator as node daemons. The operator docs I fetched list them as components but say little about what the validator checks, so read chapter 11.4 for the mechanism.

**Keep detection, decision and action as three separate components, so a bug in one cannot silently do the job of another.**

### 6. The node lifecycle

![Four words for a node out of service: cordon sends no new work, drain moves work off, quarantine holds the node out, and validation runs the active checks.](./img/p2-2016-node-words.svg)

*Figure 20.16.6. Cordon, drain, quarantine and validation are the four words for a node out of service, and a node counts against the budget until it is proven healthy.*

Picture a node that a monitor flagged on Tuesday night. Someone cordoned it, the work moved off, a technician swapped a part, and then the node came back, or did not. A node does not go from broken to fixed in one step. It passes through states, and each state has an owner and a time limit. Make this explicit in the design. Most silent capacity loss comes from a node that entered a state nobody was watching.

![The node lifecycle](./img/m20-16-1.svg)

*Figure 20.16.7. The node lifecycle, as a diagram.*

Four words carry this whole section, and the interviewer will check that you use them correctly. Cordon means "send no new work". Drain means "move the existing work off". Quarantine means "this node is out until a human or a repair process clears it". Validation means "run the active checks". The state machine in the code below enforces these moves. It refuses an illegal jump, such as repairing a node that was never drained, by raising an error.

One detail matters for safety, and it is easy to miss. In the code a node holds its slot in the limiter from the moment it is cordoned until it returns to healthy. A node stuck in repair for nine days still counts against the budget. That is intended. If the budget silently refilled while nodes were missing, the automation would keep draining healthy capacity. The slot is a promise that the fleet is smaller than it looks, and it stays counted until the promise is kept.

**Give every state an owner and a maximum time, and keep the node counted as lost until it is proven healthy.**

### 7. Blast radius: how automation avoids draining the fleet

![Four limits on automated drains stop the seventh flagged node after four cordons, and the circuit breaker freezes the fleet at 196 of 200 serving.](./img/x16-blast-radius.svg)

*Figure 20.16.8. Blast-radius limits make automation stop and hand over to a human when many nodes fail together.*

Think about a bad driver rollout, a wrong exporter configuration or a power event. Many nodes can look sick at the same moment for a reason that is not hardware. An automation that obeys every signal will cordon them all, and capacity falls to zero while the dashboard says you are healthy. This is the most important failure mode of the whole design, and it is what the interviewer is waiting for you to raise. Say it early, before they ask.

The limiter in the code has four defences, and each one stops a different kind of runaway. A fleet budget caps how many nodes may be out at once, set here at 5 percent. A failure domain cap limits how many may be out of one rack, set to one. A failure domain is a group of machines that share something, such as a rack, a power feed or a switch, so one event can take the whole group down. An hourly rate limits how many new drains may start, set to four. A circuit breaker freezes everything when six different nodes ask for a drain within ten minutes, because that pattern points to a shared cause. All the numbers are my starting values for a 200-node example.

When the limiter says no, the node is not forgotten. It stays suspect and appears in a held list for a human to read. The design principle is that automation may act freely on small, rare, well-understood events. It must hand over to a person when the scale of the event surprises it. A held list is what keeps a refusal from turning into a silent failure.

A refusal also needs a reason that a human can read in one glance. The code writes words such as "hourly rate exhausted" or "frozen: many nodes flagged" into the held list, so the on-call engineer knows which defence fired without reading the source. A bare "no" would leave the engineer guessing whether the system is broken or simply careful. Careful is what you want from it. Broken is what you want to know about quickly.

The simulation below replays a bad afternoon. It sends seven Xid 79 reports into a 200-node fleet, one per minute, so you can watch the limiter work step by step. Read the held column as the limiter's reason for saying no. It is real output from `c16_sim_storm.py`.

```text
t=  0s n000 -> cordoned  held=-
t= 60s n017 -> cordoned  held=-
t=120s n034 -> cordoned  held=-
t=180s n051 -> cordoned  held=-
t=240s n068 -> suspect   held=hourly rate exhausted
t=300s n085 -> suspect   held=frozen: many nodes flagged, suspect a fleet-wide cause
t=360s n102 -> suspect   held=frozen: many nodes flagged, suspect a fleet-wide cause
frozen: True | serving: 196 of 200
```

Read the output as a story. Four nodes were cordoned before the rate limit stopped the fifth. The sixth flag tripped the breaker. Two percent of the fleet is out and a human is paged. That two percent is the small share the limiter allowed to leave, and the rest of the fleet keeps serving. The rule file adds a matching alert, `FleetWideXid79`, that pages when three or more GPUs report Xid 79 together. Here are the fleet health state machine and limiter.

```python
# code/part20/c16_fleet_health.py
"""Node health state machine with a blast-radius limiter (chapter 20.16).

Xid actions come from the NVIDIA Xid catalog. The thresholds, dwell times and
limits are starting values chosen for this chapter, not vendor figures.
"""
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    HEALTHY = "healthy"
    SUSPECT = "suspect"
    CORDONED = "cordoned"
    DRAINING = "draining"
    QUARANTINED = "quarantined"
    REPAIRING = "repairing"
    RMA = "rma"
    VALIDATING = "validating"


S = State
LEGAL = {
    S.HEALTHY: {S.SUSPECT, S.CORDONED},
    S.SUSPECT: {S.HEALTHY, S.CORDONED},
    S.CORDONED: {S.DRAINING},
    S.DRAINING: {S.QUARANTINED},
    S.QUARANTINED: {S.REPAIRING},
    S.REPAIRING: {S.VALIDATING, S.RMA},
    S.RMA: {S.VALIDATING},
    S.VALIDATING: {S.HEALTHY, S.QUARANTINED},
}

# Xid -> catalog "immediate action" (NVIDIA Xid catalog, fetched 2026-11-09).
XID_ACTION = {
    13: "RESTART_APP", 31: "RESTART_APP", 43: "IGNORE", 45: "RESTART_FM",
    48: "RESET_GPU", 63: "IGNORE", 64: "RESET_GPU", 74: "NVLINK",
    79: "RESTART_BM", 94: "RESTART_APP", 95: "RESET_GPU",
    119: "RESET_GPU", 120: "RESET_GPU", 121: "IGNORE",
}
REPEAT_LIMIT = 3  # app-level Xids repeating this often on one node look like hardware


def classify_xid(xid, recent_count=0):
    """Return 'ignore', 'suspect' or 'drain'. Unknown codes are never ignored."""
    action = XID_ACTION.get(xid)
    if action == "IGNORE":
        return "ignore"
    if action in ("RESET_GPU", "RESTART_BM", "NVLINK"):
        return "drain"
    if action == "RESTART_APP":
        return "drain" if recent_count + 1 >= REPEAT_LIMIT else "suspect"
    return "suspect"


@dataclass
class Decision:
    allowed: bool
    reason: str


class DrainLimiter:
    """Caps how much of the fleet automation may take out of service.

    A node holds its slot from the moment it is granted until release(), so a
    node that never returns keeps counting against the budget.
    """

    def __init__(self, fleet_size, max_fraction=0.05, max_per_hour=4,
                 max_per_domain=1, trip_flags=6, window_s=600):
        self.budget = max(1, int(fleet_size * max_fraction))
        self.max_per_hour = max_per_hour
        self.max_per_domain = max_per_domain
        self.trip_flags = trip_flags
        self.window_s = window_s
        self.out = {}          # node -> failure domain
        self.grants = deque()  # grant timestamps
        self.flags = deque()   # (time, node) of verdicts that wanted a drain
        self.frozen = False

    def _trim(self, now):
        while self.grants and now - self.grants[0] >= 3600:
            self.grants.popleft()
        while self.flags and now - self.flags[0][0] >= self.window_s:
            self.flags.popleft()

    def request(self, now, node, domain):
        self._trim(now)
        if node in self.out:
            return Decision(True, "already out")
        self.flags.append((now, node))
        if len({n for _, n in self.flags}) >= self.trip_flags:
            self.frozen = True
        if self.frozen:
            return Decision(False, "frozen: many nodes flagged, suspect a fleet-wide cause")
        if len(self.out) >= self.budget:
            return Decision(False, "fleet budget exhausted")
        if sum(1 for d in self.out.values() if d == domain) >= self.max_per_domain:
            return Decision(False, "failure domain budget exhausted")
        if len(self.grants) >= self.max_per_hour:
            return Decision(False, "hourly rate exhausted")
        self.out[node] = domain
        self.grants.append(now)
        return Decision(True, "granted")

    def release(self, node):
        self.out.pop(node, None)

    def unfreeze(self):
        self.frozen = False
        self.flags.clear()


@dataclass
class Node:
    name: str
    domain: str
    state: State = State.HEALTHY
    since: float = 0.0
    reason: str = ""
    recent_xids: deque = field(default_factory=deque)


DEFAULT_MAX_DWELL_S = {
    State.SUSPECT: 3600, State.CORDONED: 600, State.DRAINING: 1800,
    State.QUARANTINED: 4 * 3600, State.REPAIRING: 24 * 3600,
    State.RMA: 14 * 24 * 3600, State.VALIDATING: 4 * 3600,
}


class Fleet:
    def __init__(self, nodes, limiter, xid_window_s=3600):
        self.nodes = {n.name: n for n in nodes}
        self.limiter = limiter
        self.xid_window_s = xid_window_s
        self.held = {}  # node -> reason, for a human to look at

    def _move(self, node, to, now, reason=""):
        if to not in LEGAL[node.state]:
            raise ValueError(f"illegal move {node.state.value} -> {to.value}")
        node.state, node.since, node.reason = to, now, reason
        if to is S.HEALTHY:
            self.limiter.release(node.name)
            self.held.pop(node.name, None)

    def report_xid(self, name, now, xid):
        node = self.nodes[name]
        while node.recent_xids and now - node.recent_xids[0] >= self.xid_window_s:
            node.recent_xids.popleft()
        verdict = classify_xid(xid, len(node.recent_xids))
        node.recent_xids.append(now)
        if verdict == "ignore" or node.state not in (S.HEALTHY, S.SUSPECT):
            return node.state
        if verdict == "suspect":
            if node.state is S.HEALTHY:
                self._move(node, S.SUSPECT, now, f"xid {xid}")
            return node.state
        decision = self.limiter.request(now, name, node.domain)
        if decision.allowed:
            self._move(node, S.CORDONED, now, f"xid {xid}")
            self.held.pop(name, None)
        else:
            if node.state is S.HEALTHY:
                self._move(node, S.SUSPECT, now, f"xid {xid}")
            self.held[name] = decision.reason
        return node.state

    def advance(self, name, now, to, reason=""):
        self._move(self.nodes[name], to, now, reason)

    def stuck(self, now, max_dwell=None):
        """Nodes that sit in a state longer than allowed: silent capacity loss."""
        limits = max_dwell or DEFAULT_MAX_DWELL_S
        return sorted(n.name for n in self.nodes.values()
                      if n.state in limits and now - n.since > limits[n.state])

    def serving(self):
        return sum(1 for n in self.nodes.values() if n.state in (S.HEALTHY, S.SUSPECT))
```

A cordon on its own is cheap, since no work is lost. It still removes capacity, though, so the limiter counts it. If you want a softer design, allow cordon-only for held nodes. I did not do that here, because it hides the budget. A cordon that the budget does not see is capacity you lost without writing it down.

**Cap how much automation may remove at once, and make it stop and call a human when many nodes fail together.**

### 8. Spare pool and X+1 sizing

![A table showing spares rising from 2 to 7 as repair time grows, beside a comparison of pooled and per-customer spares.](./img/p3-2016-repair-time-spares.svg)

*Figure 20.16.9. A slower repair loop raises the spare count from three to seven without any change in failure rate.*

![A 512-node fleet with 10 percent annual failure and 72-hour repairs averages 0.42 nodes in repair and needs 3 spares for 99.9 percent coverage.](./img/x16-spare-math.svg)

*Figure 20.16.10. The average number of nodes in repair is failure rate times repair time, and a Poisson tail turns that average into a spare count.*

Suppose a customer buys 30 replicas on a dedicated endpoint, which is a private serving setup for one customer, and the platform promises 99.9 percent availability. Availability here means the share of time the endpoint can answer requests. If one node fails and the only copy of that capacity is the node, the promise is broken until repair finishes. A spare pool is a set of healthy nodes kept ready to take the place of failed ones. The question is how many spares the pool needs.

X+1 means you need X units to serve the load and you keep one more. It is the right idea but the wrong size for a large fleet, because one spare for a whole fleet is too few for some groups and wasteful for others. The right size depends on two numbers: how often nodes need repair and how long repair takes. Little's law gives the average number of nodes in repair at any moment, which is the arrival rate multiplied by the time each node stays. Little's law is a plain identity from queueing theory: the average number in a system equals the rate of arrivals times the average time each one spends there. Repair arrivals are rare and independent, so a Poisson model gives the chance that more than the average are out together. A Poisson model assumes events arrive at random, at a steady average rate, with no memory of the past.

Here is the worked example, and the first thing to notice is that every input is an assumption, not a measurement. Say that out loud in the room. The fleet has 512 nodes. Each node has a 10 percent chance per year of needing repair. A repair takes 72 hours. Work the arithmetic in the block below one line at a time, because each line uses the one before it.

```text
arrival rate  = 512 x 0.10 / 8760 hours = 0.00584 nodes per hour
in repair     = 0.00584 x 72 hours       = 0.42 nodes on average
P(out <= 2)   = 0.9909     P(out <= 3) = 0.9991
spares for 99.9 percent coverage = 3
```

Now change one input and watch the answer move. If the repair goes through a vendor and takes 14 days, which is 336 hours, the average in repair is 1.96 nodes and 7 spares are needed for the same coverage. The fleet did not get less reliable. The repair loop got slower, and that alone raised the spare count from three to seven. For 24 hours the answer is 2. The table is real output from `c16_spare_pool.py`.

| Repair time | Average nodes in repair | Spares for 99.9 percent |
|---|---|---|
| 24 hours | 0.14 | 2 |
| 72 hours | 0.42 | 3 |
| 336 hours | 1.96 | 7 |

Two lessons come out of this. First, repair time is as important as failure rate, so shortening the loop is a way to buy capacity without buying a single node. Second, pooled spares beat per-customer spares. If 16 dedicated endpoints of 32 nodes each keep their own X+1, that is 16 spare nodes for 512 nodes. A shared pool needs 3 to 7. The catch is that a spare must match the GPU type and region, and it must load the customer's model weights before it can serve. The model weights are the trained numbers that make up the model, and they are large enough that loading them takes time. A cold spare takes minutes to be useful, so keep a warm tier for the most demanding customers. A warm spare already holds the weights and is ready to serve at once.

The unit of failure also matters, because it sets the size of the spare. If one bad GPU takes down an eight-GPU replica, then the replica is the unit. For a rack-scale system with 72 GPUs in one NVLink domain, one fault can affect a much larger unit and the spare must be larger as well. A rack-scale system is a whole rack built and wired as one large GPU machine, and an NVLink domain is the set of GPUs that share those fast links. I did not verify how failures are contained in such a rack, so say that out loud rather than guess. An honest "I would check that" is a better answer than a confident number you cannot defend.

```python
# code/part20/c16_spare_pool.py
"""Spare pool sizing from a failure rate and a repair time (chapter 20.16).

Inputs are assumptions you pass in. Nothing here is a measured fleet figure.
"""
import math


def expected_in_repair(fleet_nodes, annual_failure_rate, mttr_hours):
    """Little's law: arrivals per hour times hours each node stays out."""
    return fleet_nodes * annual_failure_rate / 8760.0 * mttr_hours


def poisson_cdf(k, mean):
    term = total = math.exp(-mean)
    for i in range(1, k + 1):
        term *= mean / i
        total += term
    return total


def spares_needed(fleet_nodes, annual_failure_rate, mttr_hours, coverage=0.999):
    """Smallest s with P(nodes in repair <= s) >= coverage, Poisson model."""
    mean = expected_in_repair(fleet_nodes, annual_failure_rate, mttr_hours)
    s = 0
    while poisson_cdf(s, mean) < coverage:
        s += 1
    return s


def x_plus_k(required_replicas, nodes_per_replica, spares):
    """Node count to buy for a customer promise of required_replicas."""
    return required_replicas * nodes_per_replica + spares


def effective_capacity(total_nodes, in_repair, stuck, in_maintenance=0):
    """Serving nodes. Stuck nodes are in repair on paper and lost in practice."""
    return total_nodes - in_repair - stuck - in_maintenance


if __name__ == "__main__":
    for mttr in (24, 72, 336):
        mean = expected_in_repair(512, 0.10, mttr)
        print(f"MTTR {mttr:>3} h  mean in repair {mean:5.2f}  "
              f"spares for 99.9%: {spares_needed(512, 0.10, mttr)}")
```

**Size the spare pool from failure rate times repair time, then pool it across customers, and shorten the repair loop before you buy more spares.**

### 9. Silent capacity loss: nodes that never rejoin

![Ways a node can go missing quietly and the three defence layers that each catch a different kind of silence.](./img/p3-2016-silent-capacity-layers.svg)

*Figure 20.16.11. No single layer is enough because each one catches a different kind of silence.*

Picture an on-call shift where every dashboard panel is green, yet the customer's requests are slower and the capacity graph slopes down. The Nebius case study describes workers that restarted and sometimes did not rejoin the pool. Capacity shrank without any alert, because every alert was about a failure and nothing had failed. The pool was simply smaller. This is the hardest class of problem to see, since the evidence is an absence, and an absence does not fire an alarm.

A node can go missing in many ways, and each one looks like a normal node from far away. It was cordoned and the uncordon step never ran, so it stays out of service with no ticket to bring it back. Uncordon is the reverse of cordon, and it is the step that lets the scheduler place work on the node again. It passed repair but the validation job crashed and nobody read the result. It came back but its readiness probe never passed. A readiness probe is the health check that tells the cluster a pod can take traffic. The device plugin did not re-register its GPUs. The device plugin is the piece that advertises GPUs to the Kubernetes scheduler. The node is up and the dashboard is green, but it advertises zero GPUs.

Defend in three layers, so that one missed step does not hide a whole node. First, give every non-healthy state a time limit and alert when it is exceeded. The method `stuck()` in the code does that, and `NodeCordonedTooLong` in the rule file does the same in Prometheus. Second, track the supply directly. Compare the number of GPUs the cluster advertises with the number your inventory says exist. A gap is lost capacity, whatever the cause. Third, count a missing node against the budget in the limiter, as the code does. Each layer catches a different kind of silence, so none of them can be dropped.

Notice why no single layer is enough. A time limit catches a node that was forgotten, but not a node whose state was never recorded at all. The supply comparison catches that case, because it looks at the hardware inventory and not at the state machine. The budget layer then makes sure a missing node cannot quietly give back its slot. Each layer assumes the others can fail, and that assumption is what a good design looks like.

The lesson from chapter 20.18 about aggressive liveness probes applies here as well. A liveness probe decides when the platform should restart a container. If the probe is too strict, it kills healthy workers and starts the rejoin problem in the first place. Link the two failures in your answer, because the interviewer will see the same root in both.

**Alert on the distance between the GPUs you own and the GPUs that are actually serving, not only on errors.**

### 10. Draining a node that is serving inference

![A 4,096-token answer at 40 tokens per second needs 102 seconds, so a 120-second grace period covers it while the default 30 seconds would cut it.](./img/x16-grace-period.svg)

*Figure 20.16.12. The termination grace period is a promise that a stream in progress will finish, so it must exceed the longest stream.*

Imagine a customer who is halfway through a long answer when their node is drained. Inference is different from batch work. A request is a stream that may last a minute or more, and a customer is watching it. If you kill the pod, the stream breaks. So draining has an order. Stop new requests first. Let current streams finish. Then stop the process. Batch work can be retried later with little harm, but a half-written answer that a person is reading cannot be undone.

In Kubernetes the sequence for a planned drain goes like this. Picture the steps as a checklist that runs in order. The cordon marks the node unschedulable, so nothing new lands there. The eviction API then removes pods one by one, and it respects PodDisruptionBudgets and the termination grace period. A PodDisruptionBudget is a rule that limits how many replicas of an app may be down at once, and the termination grace period is the time a pod has to shut down cleanly. The Kubernetes documentation says an eviction blocked by a budget returns HTTP 429 and may be retried. HTTP 429 is the "too many requests" status, here meaning the eviction must wait. The same documentation says the control plane removes the pod from endpoint slices during deletion. Endpoint slices are the lists that tell a load balancer where to send traffic. Production Kubernetes, chapter 14, adds that a pre-stop hook runs first, then the container gets SIGTERM, and the grace period clock starts at 30 seconds by default. A pre-stop hook is a command the pod runs before shutdown begins, and SIGTERM is the polite stop signal a process receives. The pod lifecycle page, fetched 2026-11-09, confirms that order. It also says endpoint removal runs at the same time as shutdown, not before it, and that terminating endpoints keep `serving` true while `ready` is false. A load balancer that reads only `ready` stops sending new requests, but ones already in flight continue. For vLLM at tag v0.33.0, `--shutdown-timeout` defaults to 0, which aborts in-flight requests. vLLM is an open-source server for running language models, and in-flight requests are the ones already running. A value above 0 waits for them. Set it from your longest stream and keep it below the grace period. The pre-stop hook does not run when a node fails outright.

The grace period must be longer than your longest stream. Worked example with assumed inputs: a maximum output of 4,096 tokens at 40 tokens per second is 102 seconds. A grace period of 120 seconds covers it. The default of 30 seconds would cut every long answer in the middle. Set the value from your maximum output length and your slowest realistic token rate. To check the arithmetic, divide the token count by the rate, and then add a margin so the last token has room to finish.

The reason the number matters is simple to state and easy to forget. The grace period is a promise to the customer that a stream already in progress will finish. If the promise is shorter than the longest stream, some customers lose their answers every time a node drains, and they blame the platform, not the drain. A long grace period has a cost too, since the node stays busy longer during maintenance. So the right value is the longest honest stream plus a small margin, not an arbitrary big number.

There are two paths, and the design must choose between them. Pick the path by asking whether the GPU still works. In a graceful drain the GPU is healthy, for instance a thermal warning, so you stop routing, wait for streams and then evict. A thermal warning means the card is running hot but still computing. In a hard drain the GPU has already failed, for instance Xid 79, and the streams on it are already dead. Waiting for them is pointless. Fence the node at the router at once so retries go elsewhere, then evict immediately. Fencing means cutting the node off from new traffic, and it is the router's job. Chapter 20.21, planned for this volume, covers retry budgets, which cap how many retries the system may send so that retries do not swamp a struggling pool.

![Draining a node that is serving inference](./img/m20-16-2.svg)

*Figure 20.16.13. Draining a node that is serving inference, as a diagram.*

A PodDisruptionBudget protects availability during voluntary disruption, which means planned maintenance rather than a sudden crash. On a node with a dead GPU, the budget may protect a replica that is not serving anyway and block the drain. That is the conflict to name. The kubectl drain page says its timeout of zero means wait forever. The eviction page says a stuck eviction can return 429 or 500 until someone intervenes, and suggests pausing the automation or deleting the pod directly. For a hardware drain I would set a timeout and then escalate to a deletion of the pod, accepting the budget violation because the replica is already broken. That is my judgment, and you should state the trade-off out loud, because a budget violation is a real cost even when it is the right call.

**Set the grace period from your longest stream, fence a hard-failed node at the router first, and put a timeout on every drain.**

### 11. A fleet-level capacity SLO

![Three capacity SLIs with an example objective of 99 percent spare pool and a 5 day repair p90.](./img/p3-2016-capacity-slos.svg)

*Figure 20.16.14. Supply SLIs warn before any customer-facing SLO moves.*

Imagine the review meeting where someone asks whether the fleet is healthy. Your availability SLO, the service level objective that measures requests, is about requests. A capacity SLO is about supply, and it leads the request SLO by hours or days. Define it so that an interviewer can see you measure what matters. Chapter 20.19 covers the request SLIs, which are the measured indicators behind the request objective, so this section adds the supply side only.

Three SLIs are enough, and each one answers a question a manager would ask. An SLI is a service level indicator, a number you measure. The first is the share of time that each dedicated endpoint has at least its minimum number of ready replicas. This ties straight to the 99.9 percent availability that Nebius states for dedicated endpoints. The second is the share of time the spare pool is at or above its target size. The third is the repair time, measured from quarantine to healthy, at the 90th percentile. The 90th percentile describes most repairs and leaves out only the slowest tail, which a plain average would blur.

An example objective, with numbers I chose, reads like this: spare pool at or above target 99 percent of the time, and 90th percentile repair time under 5 days. Treat these as a starting point to argue about, not as a standard. The rule file has a ratio of cordoned nodes and an alert at 5 percent, which matches the limiter's budget. If that alert ever fires, the automation has failed to stop, which is itself a finding. Burn-rate alerting from chapter 20.19 applies to the spare pool SLI too. A burn rate says how fast you are spending your error budget, and a fast burn deserves a page.

**Alert on spare pool shrinkage and slow repair, because they warn you before any customer-facing SLO moves.**

### 12. The vendor RMA flow, at a conceptual level

![The vendor RMA flow quarantines the node, keeps the evidence, opens a case, waits for replacement and validates before the node returns to the pool.](./img/p2-2016-rma-queue.svg)

*Figure 20.16.15. The vendor RMA flow quarantines the node, keeps the evidence, waits for a replacement and validates before return, tracking the age of each open case.*

Picture a technician on a cold floor holding a replacement part, with the faulty card in a bag. When a node's GPU is truly broken, a swap is needed. RMA means return merchandise authorisation, the vendor process for replacing faulty hardware. I did not find Nebius's process published, and it also depends on contract terms. The outline below is a reasonable design, not a description of Nebius.

Quarantine the node and keep its evidence before anything is changed. The evidence is the Xid history, the diagnostic output, the temperature and ECC counters for the days before the fault, and the serial numbers of the GPU and the board. Open a case with the vendor or the hardware integrator and attach that evidence, because it shortens the argument about whether the part is faulty. A technician swaps the part. After the swap the node goes into validation, not straight into service, and runs the level 3 diagnostic and a multi-node bandwidth test. Only a passing result returns it to the pool. A bandwidth test measures how fast data moves between machines, which is where a repaired link can still be weak.

The part that most designs miss is the clock. A case that sits waiting for a technician is a node counted as lost, and every day of waiting is capacity missing from the pool. Section 8 showed that a 14-day wait asks for seven spares where a 72-hour wait asks for three. Track the age of every open case. Chase the oldest. An age list is the simplest queue you can build, and it puts the stuck work at the top where someone must look at it.

Time also changes the economics of the case. A node that is out for a week costs the pool a slot, and a node that is out for a month may have been replaced in the plan by a spare that now needs to be returned to its owner. The age list is therefore a planning tool as well as a chasing tool. When you show it in the interview, say who reads it each morning, because a list that nobody reads is the same silence as a node nobody watches.

**Treat the RMA as a queue with an age limit, and always run validation before the node returns.**

## How to answer out loud

You have 45 minutes and a whiteboard. Say the structure first, then fill it in. An interviewer who hears the structure can follow you even when one detail goes wrong. Here are the questions most likely to come, with the order to speak.

**Question 1. Design the system that catches a failing GPU before the customer notices.** Start with the loop in one sentence: detect, decide, isolate, repair, validate, return. Treat that sentence as the map you draw before the details. Then list the three signal sources: hardware counters such as Xid and ECC, physical state such as temperature and throttling, and workload effect such as per-replica tokens per second against peers. Say that the third catches throttled GPUs that raise no error. Name the real components: DCGM exporter into Prometheus, node problem detector for node conditions, a controller for decisions. Expect the follow-up "what is your false positive rate". A false positive is an alarm with nothing wrong behind it. Answer that suspect states and active diagnostics exist to bring it down, and that you would measure it by checking how many drained nodes pass level 3.

**Question 2. How do you stop the automation from draining the fleet.** This is the question the interview is built around, so slow down here. Give the four defences in order: fleet budget, failure-domain cap, hourly rate, circuit breaker. Give the example numbers, 5 percent, one per rack, four per hour, six flags in ten minutes. Say they are starting values to tune, not facts. Say that a held node goes to a human and stays counted. Expect "what if the cause is a real fleet-wide hardware issue". Answer that the freeze costs you minutes of human attention. A wrong mass drain costs you the fleet, so you accept the first.

**Question 3. How many spares do you keep.** Start with the rule in words: failure rate times repair time gives the average number in repair. Then size the pool to a coverage target with a Poisson tail, which is the rare-event part of the model. Give the worked case one step at a time: 512 nodes, assumed 10 percent per year, 72 hours, average 0.42, and three spares for 99.9 percent. Then change the repair to 14 days and get seven. State that those inputs are assumptions you would replace with fleet data. Expect "per customer or shared". Answer shared, and name the constraints of GPU type, region and warm weights.

**Question 4. A node is being drained and customers are streaming from it.** Say stop new requests first. Then let streams finish, up to a grace period set from your longest stream, and only then evict. Give the example of 4,096 tokens at 40 per second. That is 102 seconds, so a grace of 120 covers it. Name the hard-failure exception, where you fence and evict at once. Expect "what if the budget blocks the eviction". Answer with the 429, the timeout, and the escalation to deletion for a node that is already broken.

**Question 5. How do you know capacity is shrinking silently.** Start from the absence: nothing fired, yet the pool is smaller. Compare owned GPUs to serving GPUs, time-limit every non-healthy state, and alert on cordons older than a day. Tie the answer to the case study about workers that did not rejoin, so the interviewer hears that you know why it matters.

## Worked scenarios

### Scenario A. Three GPUs report Xid 79 within five minutes

![A five step ladder from recognising a cross-rack pattern to confirming the Xid in dmesg and draining only confirmed nodes.](./img/p3-2016-xid79-triage.svg)

*Figure 20.16.16. Read the pattern and check recent changes before draining anything.*

The pager shows Xid 79 on three nodes in different racks, all within five minutes. A new engineer might drain all three, because each alert looks like a bad GPU. Reason it through step by step, and do not act until you have read the pattern.

Xid 79 means a GPU fell off the PCIe bus. That is serious on one node. Three nodes at once is a pattern, and a shared cause is likelier than three coincident hardware faults. A coincident fault is one that happens by chance at the same moment. Candidates are a driver or firmware rollout, a bad exporter restart that re-emitted a stuck gauge, or a power or cooling event. A stuck gauge is the last-value trap from section 2, where a number stays high after its cause is gone. First check what changed in the last hour. Next, check `dmesg` on one node to confirm the Xid is real, not only a gauge value that stayed high. If the limiter allowed it, the first drains went ahead, which is acceptable because the rate was small. The `FleetWideXid79` alert tells you to freeze.

Answer: confirm on one node, check recent changes, keep the freeze, and drain only the nodes whose logs show a new Xid. Say the order out loud, because the order is the answer. The simulation in section 7 shows the system doing the freeze by itself, so you can point to it as evidence that the design holds.

### Scenario B. The spare pool for a growing fleet

![Three fleet sizes showing spares growing from 3 to 4 to 7 while the share of the fleet shrinks.](./img/p3-2016-spare-growth.svg)

*Figure 20.16.17. Spares grow much more slowly than the fleet, so repair speed matters more than node count.*

A planner asks: "We have 512 nodes and we are adding 256. How many more spares?" This is a question about growth, and the trap is to assume that spares grow in step with nodes. Use the calculator. The inputs remain assumptions. For 768 nodes at 10 percent per year and 72 hours, the average in repair is 0.63. The calculator gives 4 spares, so the 256 new nodes need one more spare, not eight.

```text
python3 -c "from c16_spare_pool import spares_needed; print(spares_needed(768, 0.10, 72))"
```

Do not just quote the output. Explain that spares do not scale linearly with fleet size. At 512 nodes the answer is 3, about 0.6 percent of the fleet. At 2,048 nodes it is 7, about 0.3 percent. A bigger pool is cheaper per node. Then ask what the repair time really is, because tripling it triples the mean. The decision is usually to invest in repair speed before buying nodes. Say the reason plainly, since a planner needs to hear why the answer is so small.

Be ready for the follow-up about where the inputs come from. The honest answer is that the failure rate and the repair time come from the fleet's own history, and until that history exists, the 10 percent and the 72 hours are placeholders. A planner who hears you say that will trust the arithmetic more, because you have shown which numbers are soft.

### Scenario C. A node has been cordoned for nine days

![A decision tree from a nine-day cordon alert to vendor chasing or ownerless node, ending in a validation failure fix.](./img/p3-2016-cordoned-nine-days.svg)

*Figure 20.16.18. Find who owns the node before asking why it got stuck.*

Prometheus fires `NodeCordonedTooLong`, and the page is about a node that has been out for nine days. Reason like this. Look at the lifecycle state first. If the node is in `repairing` and a vendor case is open, the age is a vendor issue and you chase the case. If the node is in `cordoned` with no ticket, nothing owns it. This is the silent loss. Run the stuck-state check, find the ticketless nodes, and give each an owner. Then ask why it happened. A common cause is a validation step that failed and was only logged. The fix is a rule that a failed validation sends the node back to quarantine and raises a ticket, which is the `VALIDATING` to `QUARANTINED` edge in the state machine.

Notice the order of the questions. You ask about the state before the cause, because the state tells you who must act right now. The cause matters for the fix, but a node with no owner needs an owner first, even before anyone understands why it got there.

## Hands-on lab

Here is the lab, and it is the one place where you can run things yourself. I ran these steps on a Mac with Python 3 and `promtool`, which is the Prometheus rule checker. The `dcgmi` and `kubectl drain` steps need NVIDIA hardware or a cluster, so they are marked not run. Read each step as a small experiment with an expected result, and write down what you actually saw next to it.

1. Start at the repo root and run `python3 -m pytest -q code/part20/test_c16_fleet_health.py code/part20/test_c16_spare_pool.py`. The expected and observed result is 19 passed.
2. Change into the code folder and run `cd code/part20 && python3 c16_spare_pool.py`. The observed spares are 2, 3 and 7 for the three repair times in the table above.
3. Run `python3 c16_sim_storm.py` in the same directory. Compare the output with the eight lines shown in section 7. Then change `trip_flags` to 10 and ask whether the hourly rate alone still protects you.
4. Run `promtool check rules c16_gpu_health_rules.yml` and then `promtool test rules c16_gpu_health_rules_test.yml`. The observed result is 15 rules found and a passing test.
5. On a GPU node with DCGM, run `dcgmi diag -r 1 -j`. Not run. The expected shape is JSON with a result per test and exit code 0 when all pass.
6. On a cluster, run `kubectl drain <node> --ignore-daemonsets --timeout=300s`. Not run. The expected shape is pods evicted one by one, and a message about a disruption budget if one blocks.

The rule file below uses the metric names from section 2, so you can check every name against the table you already read. Each alert also names the action it asks for, which is how the automation and the human share one vocabulary.

```yaml
# code/part20/c16_gpu_health_rules.yml
# Metric names: dcgm-exporter 4.9.0 etc/default-counters.csv and kube-state-metrics
# node-metrics docs. In that file the ECC, throttle and NVLink counters are
# commented out. Enable them in your counters CSV before the matching alert can fire.
# Thresholds are starting values for this chapter, not vendor figures.
groups:
  - name: gpu-node-health
    rules:
      - alert: GpuFallenOffBus
        expr: max_over_time(DCGM_FI_DEV_XID_ERROR[5m]) == 79
        labels: {severity: page, action: drain}
        annotations:
          summary: "Xid 79: a GPU is inaccessible over PCIe on {{ $labels.instance }}"
          note: "DCGM_FI_DEV_XID_ERROR holds the last Xid seen, so it stays at 79 until another Xid or an exporter restart."

      - alert: GpuXidDrainClass
        expr: |
          (max_over_time(DCGM_FI_DEV_XID_ERROR[5m]) == 48)
          or (max_over_time(DCGM_FI_DEV_XID_ERROR[5m]) == 64)
          or (max_over_time(DCGM_FI_DEV_XID_ERROR[5m]) == 74)
          or (max_over_time(DCGM_FI_DEV_XID_ERROR[5m]) == 95)
          or (max_over_time(DCGM_FI_DEV_XID_ERROR[5m]) == 119)
          or (max_over_time(DCGM_FI_DEV_XID_ERROR[5m]) == 120)
        labels: {severity: ticket, action: drain}
        annotations:
          summary: "Xid needing a GPU reset or reboot on {{ $labels.instance }}"

      - alert: GpuMissingFromExporter
        expr: count by (instance) (DCGM_FI_DEV_GPU_TEMP_CELSIUS) < 8
        for: 5m
        labels: {severity: page, action: drain}
        annotations:
          summary: "{{ $labels.instance }} reports fewer than 8 GPUs"
          note: "The 8 is the GPU count of the assumed node type. Change it per pool."

      - alert: GpuExporterDown
        expr: up{job="dcgm-exporter"} == 0
        for: 5m
        labels: {severity: ticket}
        annotations:
          summary: "No GPU telemetry from {{ $labels.instance }}"

      - alert: GpuPcieReplays
        expr: increase(DCGM_FI_DEV_PCIE_REPLAY_TOTAL[1h]) > 10
        labels: {severity: ticket, action: suspect}
        annotations:
          summary: "PCIe replays climbing on {{ $labels.instance }}"

      - alert: GpuRowRemapFailed
        expr: DCGM_FI_DEV_ROW_REMAP_FAILED == 1
        labels: {severity: page, action: drain}
        annotations:
          summary: "GPU row remapping failed on {{ $labels.instance }}"

      - alert: GpuEccDoubleBit
        expr: increase(DCGM_FI_DEV_ECC_DBE_VOL_TOTAL[1h]) > 0
        labels: {severity: page, action: drain}
        annotations:
          summary: "Double-bit ECC error on {{ $labels.instance }}"

      - alert: GpuThermalThrottle
        expr: rate(DCGM_FI_DEV_GPU_THERMAL_THROTTLE_SECONDS_TOTAL[10m]) > 0.1
        for: 10m
        labels: {severity: ticket, action: suspect}
        annotations:
          summary: "GPU below application clocks for thermal reasons on {{ $labels.instance }}"

      - alert: GpuTemperatureHigh
        expr: DCGM_FI_DEV_GPU_TEMP_CELSIUS > 85
        for: 10m
        labels: {severity: ticket, action: suspect}
        annotations:
          summary: "GPU above 85 C for 10 minutes on {{ $labels.instance }}"

      - alert: GpuNvlinkCrcErrors
        expr: increase(DCGM_FI_DEV_NVLINK_CRC_ERROR_TOTAL[1h]) > 0
        labels: {severity: ticket, action: suspect}
        annotations:
          summary: "NVLink CRC errors on {{ $labels.instance }} (Hopper counter)"

      - alert: FleetWideXid79
        expr: count(max_over_time(DCGM_FI_DEV_XID_ERROR[10m]) == 79) >= 3
        labels: {severity: page, action: freeze-automation}
        annotations:
          summary: "Three or more GPUs report Xid 79 at once. Suspect a shared cause, not three bad GPUs."

  - name: gpu-fleet-capacity
    rules:
      - record: fleet:nodes_cordoned:ratio
        expr: sum(kube_node_spec_unschedulable) / count(kube_node_spec_unschedulable)

      - alert: FleetCordonedBudgetExceeded
        expr: fleet:nodes_cordoned:ratio > 0.05
        for: 15m
        labels: {severity: page}
        annotations:
          summary: "More than 5 percent of nodes are cordoned. Automation should have stopped before this."

      - alert: NodeCordonedTooLong
        expr: kube_node_spec_unschedulable == 1
        for: 24h
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.node }} cordoned for 24 hours: silent capacity loss"

      - alert: NodeNotReadyTooLong
        expr: kube_node_status_condition{condition="Ready",status="true"} == 0
        for: 30m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.node }} not Ready for 30 minutes"
```

The test file feeds in fake series and checks that the right alerts fire. It is `code/part20/c16_gpu_health_rules_test.yml`. Testing alerts this way means a rule that never fires is caught before a real incident. The `kube_node_spec_unschedulable` and `kube_node_status_condition` names come from the kube-state-metrics node metrics documentation. I did not rely on DCGM label names such as host or GPU index, because I could not verify them from the pages I fetched. The rules keep whatever labels the exporter gives.

## Drill questions

<details><summary>1. Name the three places a failing GPU shows up before the customer sees it.</summary>

Hardware counters such as Xid, ECC, PCIe replays and NVLink errors. Physical state such as temperature, power and throttling. Workload effect, which is per-replica token rate compared with peers. The third catches throttled GPUs that raise no error.
</details>

<details><summary>2. What does Xid 79 mean and what does the catalog say to do?</summary>

The GPU is inaccessible over PCIe, which people call fallen off the bus. The catalog's immediate action is to restart the bare metal node. Contact support is the follow-up action.
</details>

<details><summary>3. Why does an alert on DCGM_FI_DEV_XID_ERROR equal to 79 need care?</summary>

The metric is a gauge holding the last Xid seen. It stays at 79 until another Xid replaces it or the exporter restarts. A repaired node can keep alerting unless you check recency.
</details>

<details><summary>4. Which DCGM exporter counters are off in the 4.9.0 default file?</summary>

The ECC counters, the throttle counters and the NVLink error counters are commented out. You must enable them in your counters file. Metric names also change across releases, so check `/metrics`.
</details>

<details><summary>5. What are the four dcgmi diag levels and why not run level 3 on a serving node?</summary>

Level 1 is quick, level 2 is extended, level 3 is hardware diagnostics, level 4 adds memory and power pulse tests. Level 3 runs stress, power and bandwidth tests on the GPUs, so it competes with customer work and belongs in quarantine.
</details>

<details><summary>6. List the four defences that keep automation from draining the fleet.</summary>

A fleet budget, a per-failure-domain cap, an hourly drain rate, and a circuit breaker that freezes automation when many nodes are flagged together. A blocked node stays suspect and goes to a human.
</details>

<details><summary>7. A node sits in repair for a week. Does it count against the drain budget?</summary>

Yes. It keeps its slot until it returns healthy. Otherwise the budget would refill while capacity is missing and automation would keep draining healthy nodes.
</details>

<details><summary>8. How do repair time and spare count relate?</summary>

Average nodes in repair equal the arrival rate times the repair time. In the example the average goes from 0.42 at 72 hours to 1.96 at 14 days, and the spares for 99.9 percent go from 3 to 7.
</details>

<details><summary>9. Why is a pooled spare pool cheaper than X+1 per customer, and what limits pooling?</summary>

One shared pool needs a few nodes for the whole fleet, while per-customer spares add one each. The limits are GPU type, region and the time to load a customer's model weights onto the spare.
</details>

<details><summary>10. How do you pick terminationGracePeriodSeconds for an inference pod?</summary>

From your longest stream. With 4,096 maximum output tokens at 40 tokens per second the stream is about 102 seconds, so a grace period of 120 seconds covers it. The default of 30 seconds would cut long answers.
</details>

## Common mistakes and weak answers

- **Draining on every alert.** Interviewers wait for you to notice that one bug can look like a fleet-wide failure. Say the budget and the freeze before you are asked.
- **Only passive checks.** Counters miss weak hardware. Say that an active diagnostic gates the return from repair.
- **One spare, "N+1".** It ignores repair time. Show the arithmetic and say the inputs are assumptions.
- **Forgetting the nodes that never come back.** Say that the budget keeps counting a missing node and that every state has a time limit.
- **Draining with a pod kill.** Streams die. Say stop new requests, wait up to a grace period set from stream length, then evict.
- **Claiming how Nebius does it.** Nebius has not published its design. Say "a reasonable design is".
- **Quoting a metric name from memory.** Say you would check `/metrics` on the exporter version.

## Connections to the rest of the handbook

- Chapter 17.4, DCGM exporter and interpreting GPU metrics, for the full metric families.
- Chapter 17.6, alerting, SLOs and health checks for GPU clusters, and 17.7, failure modes and detection.
- Chapter 11.4, GPU Operator architecture and operands, for the driver, exporter and validator daemons.
- Chapter 6.14, Slurm operations, for health checks and drain reason codes on the HPC side.
- Chapter 19.6, the node-health automation capstone, and `code/gpuhealth` for the Go controller.
- Chapter 20.12 for capacity estimation and 20.13 for the multi-tenant API this fleet serves.
- Chapter 20.18, how LLM serving fails, for Xid errors in the serving context and the silent pool shrink.
- Chapter 20.19, SLIs, SLOs and alerts for token APIs, for burn-rate alerting.
- Chapter 20.26, the stress interview, where this design appears as a role-play incident.

## Sources and review notes

Sources and dates fetched, all 2026-11-09:

- NVIDIA DCGM exporter `etc/default-counters.csv` at tag 4.9.0 and the installation page for port 9400 and the counters file format.
- NVIDIA Xid error catalog, `docs.nvidia.com/deploy/xid-errors`, no version shown.
- NVIDIA DCGM diagnostics page, run levels, durations, exit codes.
- NVIDIA GPU Operator overview, for the list of components.
- Kubernetes documentation: node problem detector page (read in full), safely drain a node, kubectl drain reference, API-initiated eviction, pod lifecycle (termination flow section read in full), all from kubernetes/website main.
- NVIDIA dcgm-exporter tag 4.9.0: `llms.txt`, `etc/default-counters.csv` and `internal/pkg/rendermetrics/render_metrics.go` for labels and the default port. vLLM tag v0.33.0 `config/vllm.py` and `arg_utils.py` for `shutdown_timeout`. All fetched 2026-11-09.
- kube-state-metrics node metrics documentation.
- Book chapters: AI Systems Performance Engineering chapter 16. Supercomputers for Linux Sysadmins chapter 3. Production Kubernetes chapter 14. The AI Factory book and Systems Performance, second edition, were searched and had no GPU health or drain material for this topic, so I did not cite them.
- Nebius sources are the plan's section 1: the chat-app case study on silent pool shrink and X+1, and the 99.9 percent dedicated endpoint SLA.

### Verification log

Checked 5, confirmed 3 (SIGTERM order and endpoint removal timing, node problem detector scope, default port 9400), corrected 1 (the pod lifecycle claim now cites the page and adds the concurrent endpoint removal), added 1 (label names), removed 0, still unverified 2 (vLLM HTTP server drain path, `dcgmi diag` behaviour on hardware).

Explicitly labelled inferences: the three-outcome Xid policy and its thresholds, the limiter numbers, the repair-state dwell times, the peer-comparison check, the 10 percent annual repair rate, the 72 hour and 14 day repair times, the SLO numbers, the RMA outline, and the choice to escalate a blocked hardware drain to pod deletion.

Not verified: `dcgmi diag` and `kubectl drain` were not run, there is no GPU or cluster here. What vLLM's HTTP server does between SIGTERM and exit was not traced. I confirmed only the `shutdown_timeout` setting and its help text. Whether Nebius uses any of this is unknown. The prompt "detect a failing GPU before the customer does" comes from a secondary source and is unverified as a real question.
