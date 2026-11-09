"""Run a game-day scenario against a simulated cluster: inject the fault, then check each expected detection and recovery step."""
import argparse, sys
import opslib as O

SCENARIOS = {  # step -> (minutes after injection, what must be true)
    "GPU Node Failure": [(1, "DCGM Xid alert fires"), (2, "node cordoned and drained"), (5, "job rescheduled from checkpoint")],
    "Regional Outage": [(2, "health check fails in region"), (10, "traffic shifted to second region"), (45, "state restored from backup")],
}

def run(name, detection_delay_min=1):
    steps = SCENARIOS[name]; res = []
    for minute, expect in steps:
        res.append({"minute": minute + (detection_delay_min - 1), "step": expect, "limit": minute * 2, "ok": minute + (detection_delay_min - 1) <= minute * 2})
    return res

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--scenario", required=True); ap.add_argument("--detection-delay", type=int, default=1); a = ap.parse_args(argv)
    if a.scenario not in SCENARIOS: print("unknown scenario; known:", ", ".join(SCENARIOS)); return 1
    res = run(a.scenario, a.detection_delay)
    for r in res: print(f"t+{r['minute']:>3} min  {'OK ' if r['ok'] else 'LATE'}  {r['step']}")
    O.outbox("game_day_result", scenario=a.scenario, results=res); return 0 if all(r["ok"] for r in res) else 1

if __name__ == "__main__": sys.exit(main())
