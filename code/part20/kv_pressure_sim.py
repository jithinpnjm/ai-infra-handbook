# code/part20/kv_pressure_sim.py
"""Toy model of KV-cache pressure with preemption by recompute. NOT vLLM.
Capacity comes from the Hands-On LLM Serving book example: Llama-2-7B in FP16
on a 24 GB GPU leaves 10 GB, and each token needs 0.5 MB of KV cache."""
import json
import sys
from collections import deque


def simulate(n_req=16, prompt=3000, out=1000, free_gb=10.0, mb_per_token=0.5):
    cap = int(free_gb * 1024 / mb_per_token)
    waiting = deque({"p": prompt, "left": out, "gen": 0} for _ in range(n_req))
    running, steps, preempts, peak, max_wait, recompute = [], 0, 0, 0.0, 0, 0
    done = 0
    while waiting or running:
        steps += 1
        used = sum(r["p"] + r["gen"] for r in running)
        while waiting and used + waiting[0]["p"] + waiting[0]["gen"] <= cap:
            r = waiting.popleft()
            used += r["p"] + r["gen"]
            running.append(r)
        max_wait = max(max_wait, len(waiting))
        for r in running:
            r["gen"] += 1
            r["left"] -= 1
        used = sum(r["p"] + r["gen"] for r in running)
        while used > cap and len(running) > 1:  # newest request is evicted
            v = running.pop()
            used -= v["p"] + v["gen"]
            recompute += v["p"] + v["gen"]
            v["p"], v["gen"] = v["p"] + v["gen"], 0  # redo prompt plus generated text
            waiting.appendleft(v)
            preempts += 1
        peak = max(peak, used / cap)
        finished = [r for r in running if r["left"] <= 0]
        done += len(finished)
        running = [r for r in running if r["left"] > 0]
    return {"capacity_tokens": cap, "steps": steps, "preemptions": preempts,
            "peak_kv_usage": round(peak, 3), "max_waiting": max_wait,
            "recomputed_tokens": recompute, "finished": done}


if __name__ == "__main__":
    kw = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(simulate(**kw), indent=2))
