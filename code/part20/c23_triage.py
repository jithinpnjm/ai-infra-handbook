#!/usr/bin/env python3
"""Triage helper for chapter 20.23: read the text of `kubectl describe pod|node` and
`kubectl get events`, and list likely causes in the order a person would check them.

Standard library only. It reads files or stdin. It never talks to a cluster.

Usage:
    python3 c23_triage.py samples/c23_describe_oomkilled.txt
    python3 c23_triage.py samples/c23_describe_pending_gpu.txt --events samples/c23_get_events_mixed.txt
    kubectl describe pod NAME | python3 c23_triage.py -
"""
import argparse
import re
import sys
from dataclasses import dataclass, field


@dataclass
class Event:
    type: str
    reason: str
    age: str
    source: str
    message: str


@dataclass
class Container:
    name: str
    state: str = ""
    state_reason: str = ""
    last_state: str = ""
    last_reason: str = ""
    exit_code: str = ""
    restarts: int = 0


@dataclass
class Described:
    kind: str = "pod"
    status: str = ""
    containers: list = field(default_factory=list)
    conditions: dict = field(default_factory=dict)
    taints: list = field(default_factory=list)
    events: list = field(default_factory=list)


@dataclass
class Finding:
    cause: str
    confidence: str
    evidence: str
    next_step: str


def _columns(header):
    """Return (name, start) pairs for a table header line, in order."""
    names = ["LAST SEEN", "TYPE", "REASON", "OBJECT", "MESSAGE",
             "Type", "Reason", "Age", "From", "Message"]
    found = []
    for n in names:
        m = re.search(r"(?<!\S)" + re.escape(n) + r"(?!\S)", header)
        if m:
            found.append((n.lower().replace(" ", "_"), m.start()))
    return sorted(found, key=lambda c: c[1])


def parse_events(text):
    """Parse the Events table of `kubectl describe`, or the table of `kubectl get events`."""
    events = []
    cols = None
    for line in text.splitlines():
        if re.match(r"^\s*(Type\s+Reason|LAST SEEN\s+TYPE)", line):
            cols = _columns(line)
            continue
        if cols is None or not line.strip() or re.match(r"^\s*-{3,}", line):
            continue
        if re.match(r"^\S.*:\s*$", line) and "Events" not in line:
            cols = None
            continue
        parts = {}
        for i, (name, start) in enumerate(cols):
            end = cols[i + 1][1] if i + 1 < len(cols) else len(line)
            parts[name] = line[start:end].strip()
        if not parts.get("reason"):
            continue
        events.append(Event(
            type=parts.get("type", ""),
            reason=parts.get("reason", ""),
            age=parts.get("age", parts.get("last_seen", "")),
            source=parts.get("from", parts.get("object", "")),
            message=parts.get("message", "")))
    return events


def parse_describe(text):
    """Parse the parts of `kubectl describe pod|node` that the rules below need."""
    d = Described()
    d.kind = "node" if re.search(r"^Taints:|^Unschedulable:", text, re.M) else "pod"
    lines = text.splitlines()
    section = ""
    cur = None
    block = ""
    for i, line in enumerate(lines):
        if re.match(r"^Events:", line):
            break
        top = re.match(r"^(\S[^:]*):\s*(.*)$", line)
        if top:
            section = top.group(1)
            if section == "Status":
                d.status = top.group(2).strip()
            if section == "Taints" and top.group(2).strip() not in ("", "<none>"):
                d.taints.append(top.group(2).strip())
            continue
        if section == "Taints" and line.strip():
            d.taints.append(line.strip())
        elif section == "Containers":
            m = re.match(r"^  (\S[^:]*):\s*$", line)
            if m:
                cur = Container(name=m.group(1))
                d.containers.append(cur)
                block = ""
                continue
            if cur is None:
                continue
            m = re.match(r"^    (State|Last State):\s*(\S+)", line)
            if m:
                block = m.group(1)
                if block == "State":
                    cur.state = m.group(2)
                else:
                    cur.last_state = m.group(2)
                continue
            m = re.match(r"^      (Reason|Exit Code):\s*(\S+)", line)
            if m and block:
                if m.group(1) == "Reason":
                    if block == "State":
                        cur.state_reason = m.group(2)
                    else:
                        cur.last_reason = m.group(2)
                else:
                    cur.exit_code = m.group(2)
                continue
            m = re.match(r"^    Restart Count:\s*(\d+)", line)
            if m:
                cur.restarts = int(m.group(1))
            elif re.match(r"^    \S", line):
                block = ""
        elif section == "Conditions":
            m = re.match(r"^\s+([A-Za-z]+)\s+(True|False|Unknown)\b", line)
            if m:
                d.conditions[m.group(1)] = m.group(2)
    d.events = parse_events(text)
    return d


def _scheduling_findings(message):
    out = []
    msg = message
    m = re.search(r"(\d+)/(\d+) nodes are available", msg) or re.search(r"(\d+) nodes available", msg)
    scope = f" ({m.group(0)})" if m else ""
    for count, res in re.findall(r"(\d+) Insufficient (\S+?)(?=[.,](?:\s|$))", msg.rstrip(". ") + ". "):
        if res.startswith("nvidia.com/gpu") or "/gpu" in res:
            out.append(Finding(
                "gpu_unavailable", "high",
                f"{count} node(s) report Insufficient {res}{scope}",
                "Check allocatable on GPU nodes: kubectl describe node | grep -A8 Allocatable. "
                "Zero means the device plugin is not advertising. Non-zero means the GPUs are taken or fragmented."))
        else:
            out.append(Finding(
                "cpu_memory_capacity", "high",
                f"{count} node(s) report Insufficient {res}{scope}",
                "Compare the pod request with free allocatable. Lower the request or add nodes."))
    if re.search(r"insufficient (cpu|memory)", msg) and not out:
        out.append(Finding(
            "cpu_memory_capacity", "medium", msg.strip(),
            "Compare the pod request with free allocatable. Lower the request or add nodes."))
    m = re.search(r"(\d+) node\(s\) had (untolerated taint|taints that the pod didn't tolerate)", msg)
    if m:
        out.append(Finding(
            "untolerated_taint", "high", f"{m.group(1)} node(s) have a taint the pod does not tolerate",
            "kubectl describe node | grep Taints, then add a toleration or schedule elsewhere."))
    m = re.search(r"(\d+) node\(s\) didn't match Pod's node affinity/selector", msg)
    if m:
        out.append(Finding(
            "node_selector_mismatch", "high", f"{m.group(1)} node(s) do not match the selector or affinity",
            "kubectl get nodes --show-labels and compare with nodeSelector and affinity."))
    return out


def _event_findings(events):
    out = []
    for e in events:
        msg, reason = e.message, e.reason
        if reason == "FailedScheduling":
            out.extend(_scheduling_findings(msg))
        elif reason == "Unhealthy" and msg.startswith("Liveness probe failed"):
            out.append(Finding("liveness_probe_kill", "high", msg,
                               "Compare probe timing with real start and response time. Use a startupProbe for slow starts."))
        elif reason == "Unhealthy" and msg.startswith("Startup probe failed"):
            out.append(Finding("startup_probe_kill", "high", msg,
                               "Raise failureThreshold times periodSeconds above the worst start time."))
        elif reason == "Unhealthy" and msg.startswith("Readiness probe failed"):
            out.append(Finding("readiness_not_ready", "medium", msg,
                               "The pod is out of Service endpoints, not restarted. Check kubectl get endpointslices."))
        elif reason == "Killing" and "failed liveness probe" in msg:
            out.append(Finding("liveness_probe_kill", "high", msg,
                               "The kubelet restarted a running container. Read logs --previous and the probe settings."))
        elif reason in ("Failed", "BackOff") and ("ErrImagePull" in msg or "Back-off pulling image" in msg):
            out.append(Finding("image_pull_failure", "high", msg,
                               "Check image name, pull secret, registry reachability, and pull time for the image size."))
        elif reason == "Evicted":
            m = re.search(r"low on resource: (\S+?)[.\s]", msg + " ")
            res = m.group(1) if m else "unknown"
            out.append(Finding("node_pressure_eviction", "high", msg.strip(),
                               f"Node was short of {res}. Check the node conditions and which pods use it."))
        elif "failed calling webhook" in msg:
            m = re.search(r'failed calling webhook "([^"]+)"', msg)
            out.append(Finding("admission_webhook_unreachable", "high",
                               f"API server could not call webhook {m.group(1) if m else '?'}",
                               "Check the webhook Service endpoints and its failurePolicy. See the drill for the safe order."))
        elif re.search(r'admission webhook "[^"]+" denied the request', msg):
            out.append(Finding("admission_webhook_denied", "high", msg,
                               "The webhook answered and said no. Read its message, then the policy behind it."))
        elif reason == "NodeNotReady":
            out.append(Finding("node_not_ready", "medium", msg,
                               "kubectl describe node and read Conditions, Taints and Lease."))
    return out


def _container_findings(d):
    out = []
    for c in d.containers:
        if "OOMKilled" in (c.last_reason, c.state_reason):
            out.append(Finding(
                "container_oom_kill", "high",
                f"container {c.name}: last state {c.last_reason or c.state_reason}, exit code {c.exit_code or '?'}, "
                f"restarts {c.restarts}",
                "The container exceeded its memory limit. Compare working set with the limit, then fix the leak or raise the limit."))
        if c.state_reason in ("ImagePullBackOff", "ErrImagePull"):
            out.append(Finding(
                "image_pull_failure", "high", f"container {c.name} waiting: {c.state_reason}",
                "Check image name, pull secret, registry reachability, and pull time for the image size."))
        if c.state_reason == "CrashLoopBackOff" and "OOMKilled" not in (c.last_reason,):
            out.append(Finding(
                "crash_loop_unknown", "medium", f"container {c.name} in CrashLoopBackOff, last reason {c.last_reason or '?'}",
                "kubectl logs --previous, then check exit code and probe events."))
    return out


def _node_findings(d):
    out = []
    ready = d.conditions.get("Ready")
    if ready in ("False", "Unknown"):
        kubelet_silent = ready == "Unknown"
        out.append(Finding(
            "node_not_ready", "high",
            f"Ready is {ready}" + ("; kubelet stopped posting status" if kubelet_silent else "")
            + (f"; taints: {', '.join(d.taints)}" if d.taints else ""),
            "Unknown means no heartbeat: check the machine, network and kubelet. False means the kubelet reports a fault: "
            "read journalctl -u kubelet and the runtime."))
    for cond, cause in (("MemoryPressure", "node_memory_pressure"),
                        ("DiskPressure", "node_disk_pressure"),
                        ("PIDPressure", "node_pid_pressure")):
        if d.conditions.get(cond) == "True":
            out.append(Finding(cause, "high", f"{cond} is True",
                               "The kubelet will evict pods. Find the heaviest users and the reserved settings."))
    return out


_ORDER = {"high": 0, "medium": 1, "low": 2}


def diagnose(describe_text="", events_text=""):
    """Return findings, high confidence first, duplicates removed."""
    findings = []
    events = []
    if describe_text:
        d = parse_describe(describe_text)
        findings.extend(_container_findings(d))
        if d.kind == "node":
            findings.extend(_node_findings(d))
        events.extend(d.events)
    if events_text:
        events.extend(parse_events(events_text))
    findings.extend(_event_findings(events))
    by_cause = {}
    for f in findings:
        if f.cause not in by_cause:
            by_cause[f.cause] = f
        elif f.evidence not in by_cause[f.cause].evidence:
            by_cause[f.cause].evidence += " | " + f.evidence
    unique = list(by_cause.values())
    # Disambiguate exit 137: an OOM kill and a probe kill both look like restarts.
    causes = {f.cause for f in unique}
    if "container_oom_kill" in causes and "liveness_probe_kill" in causes:
        for f in unique:
            if f.cause == "liveness_probe_kill":
                f.confidence = "medium"
    return sorted(unique, key=lambda f: _ORDER[f.confidence])


def render(findings):
    if not findings:
        return "No known pattern matched. Read the full describe output and the node events."
    lines = []
    for i, f in enumerate(findings, 1):
        lines.append(f"{i}. {f.cause} [{f.confidence}]")
        lines.append(f"   evidence: {f.evidence}")
        lines.append(f"   next: {f.next_step}")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("describe", help="file with kubectl describe output, or - for stdin")
    p.add_argument("--events", help="file with kubectl get events output")
    a = p.parse_args(argv)
    text = sys.stdin.read() if a.describe == "-" else open(a.describe).read()
    events = open(a.events).read() if a.events else ""
    print(render(diagnose(text, events)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
