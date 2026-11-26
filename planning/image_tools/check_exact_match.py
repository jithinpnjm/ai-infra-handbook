from verify_text import cards

expected = {
    "L1 Trigger": "memory.current reaches memory.max (set from limits.memory)",
    "L1 Actor": "Linux kernel, synchronous, SIGKILL",
    "L1 Result": "container exits OOMKilled, exit code 137; kubelet restarts it in place if restartPolicy allows; memory.events shows oom and oom_kill",
    "L2 Trigger": "node-wide memory.available below evictionHard (for example 100Mi) or nodefs.available below 10 percent",
    "L2 Actor": "kubelet eviction manager in user space",
    "L2 Ranking": "BestEffort, then Burstable over requests, then Guaranteed",
    "L2 Result": "whole pod Failed with Reason Evicted; owning controller reschedules",
    "Footer": "Eviction ignores PodDisruptionBudgets; BestEffort and Burstable over requests are preferred OOM victims via oom_score_adj"
}

all_match = True
for key, exp_str in expected.items():
    joined = " ".join([l[0] for l in cards[key]])
    match = (joined == exp_str)
    if not match:
        all_match = False
        print(f"MISMATCH in {key}!")
        print(f"  Exp: '{exp_str}'")
        print(f"  Got: '{joined}'")
    else:
        print(f"[OK] {key} matches exactly!")

print(f"\nAll match exactly: {all_match}")
