import sys

# Test labels
title = "Kernel OOM kill versus kubelet eviction"

lane1_title = "Kernel cgroup OOM kill"
l1_trigger = "memory.current reaches memory.max (set from limits.memory)"
l1_actor = "Linux kernel, synchronous, SIGKILL"
l1_result = "container exits OOMKilled, exit code 137; kubelet restarts it in place if restartPolicy allows; memory.events shows oom and oom_kill"

lane2_title = "Kubelet node-pressure eviction"
l2_trigger = "node-wide memory.available below evictionHard (for example 100Mi) or nodefs.available below 10 percent"
l2_actor = "kubelet eviction manager in user space"
l2_ranking = "BestEffort, then Burstable over requests, then Guaranteed"
l2_result = "whole pod Failed with Reason Evicted; owning controller reschedules"

footer = "Eviction ignores PodDisruptionBudgets; BestEffort and Burstable over requests are preferred OOM victims via oom_score_adj"

print("All labels defined.")
