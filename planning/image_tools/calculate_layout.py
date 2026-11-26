import re

# Exact labels
labels = [
    "Kernel OOM kill versus kubelet eviction",
    "Kernel cgroup OOM kill",
    "memory.current reaches memory.max (set from limits.memory)",
    "Linux kernel, synchronous, SIGKILL",
    "container exits OOMKilled, exit code 137; kubelet restarts it in place if restartPolicy allows; memory.events shows oom and oom_kill",
    "Kubelet node-pressure eviction",
    "node-wide memory.available below evictionHard (for example 100Mi) or nodefs.available below 10 percent",
    "kubelet eviction manager in user space",
    "BestEffort, then Burstable over requests, then Guaranteed",
    "whole pod Failed with Reason Evicted; owning controller reschedules",
    "Eviction ignores PodDisruptionBudgets; BestEffort and Burstable over requests are preferred OOM victims via oom_score_adj"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. '{l}'")
