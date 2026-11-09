#!/usr/bin/env python3
"""Pull the facts out of a Linux OOM killer log (dmesg or journalctl -k).

Line shapes come from the kernel source, mm/oom_kill.c and mm/memcontrol.c (v6.6):
  <comm> invoked oom-killer: gfp_mask=0x.., order=N, oom_score_adj=N
  oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=..,mems_allowed=..,
      oom_memcg=/path,task_memcg=/path,task=NAME,pid=N,uid=N
  Memory cgroup out of memory: Killed process PID (NAME) total-vm:..kB, anon-rss:..kB,
      file-rss:..kB, shmem-rss:..kB, UID:N pgtables:..kB oom_score_adj:N
  [  pid  ]   uid  tgid total_vm      rss pgtables_bytes swapents oom_score_adj name
Usage: dmesg | python3 c05_oom_parse.py
"""
import re
import sys

TS = r"^(?:\[\s*\d+\.\d+\]\s*)?"
INVOKED = re.compile(TS + r"(\S+) invoked oom-killer: gfp_mask=(\S+), order=(\d+), "
                     r"oom_score_adj=(-?\d+)")
SUMMARY = re.compile(TS + r"oom-kill:constraint=(\w+),")
MEMCG = re.compile(r",oom_memcg=([^,\s]+)")
KILLED = re.compile(TS + r"(Out of memory|Memory cgroup out of memory): Killed process "
                    r"(\d+) \((.+?)\) total-vm:(\d+)kB, anon-rss:(\d+)kB, file-rss:(\d+)kB, "
                    r"shmem-rss:(\d+)kB, UID:(\d+) pgtables:(\d+)kB oom_score_adj:(-?\d+)")
TASK = re.compile(TS + r"\[\s*(\d+)\]\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+"
                  r"(-?\d+)\s+(\S.*)$")


def parse(text):
    """Return a dict describing the first OOM event in the text."""
    info = {"tasks": []}
    for line in text.splitlines():
        m = INVOKED.match(line)
        if m:
            info.update(trigger=m[1], gfp_mask=m[2], order=int(m[3]))
        m = SUMMARY.match(line)
        if m:
            found = MEMCG.search(line)
            info.update(constraint=m[1], oom_memcg=found[1] if found else None)
        m = KILLED.match(line)
        if m:
            info.update(kind=m[1], victim_pid=int(m[2]), victim=m[3],
                        total_vm_kb=int(m[4]), anon_rss_kb=int(m[5]),
                        file_rss_kb=int(m[6]), shmem_rss_kb=int(m[7]),
                        uid=int(m[8]), victim_adj=int(m[10]))
            continue
        m = TASK.match(line)
        if m:
            info["tasks"].append({"pid": int(m[1]), "rss_pages": int(m[5]),
                                  "swapents": int(m[7]), "adj": int(m[8]), "name": m[9]})
    return info


def explain(info):
    """A short human reading: who was killed, in which scope, and by how much."""
    if "victim" not in info:
        return "no 'Killed process' line found"
    scope = ("container/cgroup limit" if info.get("constraint") == "CONSTRAINT_MEMCG"
             else "whole-node memory")
    mib = info["anon_rss_kb"] / 1024
    return "%s (pid %d) killed for %s; anon-rss %.0f MiB, file-rss %.0f MiB" % (
        info["victim"], info["victim_pid"], scope, mib, info["file_rss_kb"] / 1024)


def top_tasks(info, count=3):
    """Largest tasks by resident pages (dump_tasks table, memory values in pages)."""
    return sorted(info["tasks"], key=lambda t: t["rss_pages"], reverse=True)[:count]


if __name__ == "__main__":
    result = parse(sys.stdin.read())
    print(explain(result))
    for task in top_tasks(result):
        print("  %-16s pid %-6d rss %d pages" % (task["name"], task["pid"], task["rss_pages"]))
