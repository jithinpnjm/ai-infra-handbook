"""Turn parsed 60-second output into USE-style findings.

Each rule cites the place in Systems Performance (2nd edition) that gives
the test. Where the book gives no number, the rule says so and the number
is a default you can change.
"""
from collections import namedtuple

Finding = namedtuple("Finding", "resource kind message")  # kind is U, S or E


def load_findings(load, cpus):
    """Load per CPU above 1 means demand is above capacity (Chapter 6, uptime)."""
    out = []
    per_cpu = load["load1"] / cpus
    if per_cpu > 1:
        out.append(Finding("cpu", "S", f"load1 {load['load1']} on {cpus} CPUs = {per_cpu:.2f} per CPU; "
                           "load also counts tasks in uninterruptible I/O, so confirm with vmstat r"))
    trend = "rising" if load["load1"] > load["load15"] else "falling or steady"
    out.append(Finding("cpu", "U", f"load trend is {trend} ({load['load1']}, {load['load5']}, {load['load15']})"))
    return out


def vmstat_findings(rows, cpus):
    """Skip the first row, then test r against the CPU count and si/so against zero."""
    out, live = [], [r for r in rows if not r["since_boot"]]
    if not live:
        return [Finding("vmstat", "E", "no live rows: run vmstat with an interval and a count")]
    if max(r["r"] for r in live) > cpus:
        out.append(Finding("cpu", "S", f"run queue r above the CPU count {cpus}"))
    if any(r["si"] > 0 or r["so"] > 0 for r in live):
        out.append(Finding("memory", "S", "swapping: si or so above zero in a live row"))
    if min(r["id"] for r in live) == 0:
        out.append(Finding("cpu", "U", "idle reached 0 in a live row"))
    if max(r["wa"] for r in live) > 0:
        out.append(Finding("disk", "U", "wa above 0: threads were waiting on I/O; check iostat"))
    return out


def free_findings(free, min_available_pct=10.0):
    """Look at available, not free. The 10 percent default is a choice, not the book's number."""
    mem = free["mem"]
    pct = 100 * mem["available"] / mem["total"]
    msg = f"available {mem['available']:.0f} of {mem['total']:.0f} ({pct:.0f} percent)"
    out = [Finding("memory", "S" if pct < min_available_pct else "U", msg)]
    if free["swap"] and free["swap"]["used"] > 0:
        out.append(Finding("memory", "S", f"swap in use: {free['swap']['used']:.0f}; swapping needs vmstat si/so"))
    return out


def iostat_findings(parsed):
    """Appendix A: saturation is aqu-sz above 1 or a high await. %util alone only says busy."""
    out = []
    for d in parsed["disks"]:
        name, util = d["device"], d.get("%util")
        qsz = d.get("aqu-sz", d.get("avgqu-sz"))
        if util is not None and util >= 99:
            out.append(Finding("disk", "U", f"{name} busy {util:.0f} percent in block {d['block']}"))
        if qsz is not None and qsz > 1:
            out.append(Finding("disk", "S", f"{name} queue {qsz} requests in block {d['block']}"))
    cpu = parsed["cpu"]
    if cpu and cpu.get("iowait", 0) > 0:
        out.append(Finding("disk", "U", f"iowait {cpu['iowait']} percent: idle CPU time spent waiting on I/O"))
    return out


def psi_findings(name, psi):
    """PSI is rising when avg10 is above avg300 (Chapter 7, PSI)."""
    some = psi.get("some", {})
    if some.get("avg10", 0) > some.get("avg300", 0):
        return [Finding(name, "S", f"pressure rising: avg10 {some['avg10']} above avg300 {some['avg300']}")]
    return []


def mpstat_findings(rows):
    """Use the all row for utilisation: 100 minus idle (Appendix A, CPU utilization)."""
    alls = [r for r in rows if r["CPU"] == "all"]
    if not alls:
        return []
    avg = [r for r in alls if r["average"]] or alls
    busy = 100 - sum(r["%idle"] for r in avg) / len(avg)
    return [Finding("cpu", "U", f"mpstat all busy {busy:.1f} percent")]
