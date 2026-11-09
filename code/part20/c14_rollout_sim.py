"""Rollout simulator for GPU model endpoints (chapter 20.14).

Three small tools:
  decide()          promote, hold or rollback from canary versus baseline metrics
  rolling_update()  tick-by-tick capacity during a surge-constrained rolling update
  cold_start()      time from "pod scheduled" to "pod ready" for one replica

Every threshold is a starting value chosen for teaching. Nebius has not
published its own gates, so tune them to your SLO.
"""
import json
import math
import sys
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------- canary gate
@dataclass(frozen=True)
class Metrics:
    requests: int          # requests seen in the window
    ttft_p99_s: float      # time to first token, 99th percentile
    itl_p99_s: float       # inter-token latency, 99th percentile
    error_rate: float      # 0..1, HTTP 5xx and engine errors
    length_share: float    # share of finish_reason=length, 0..1
    quality: float         # score on a fixed eval prompt set, 0..1
    tokens_per_s: float    # generation token rate


@dataclass(frozen=True)
class Gates:
    min_requests: int = 200
    ttft_ratio_max: float = 1.25
    itl_ratio_max: float = 1.25
    error_abs_max: float = 0.02         # hard rollback above this
    error_delta_max: float = 0.005      # canary minus baseline
    length_shift_max: float = 0.10      # absolute shift in length share
    quality_drop_max: float = 0.02      # absolute drop on the eval set
    hold_band: float = 0.5              # within this fraction above the gate: hold, not rollback


@dataclass
class Decision:
    action: str                          # "promote", "hold" or "rollback"
    reasons: list = field(default_factory=list)


def decide(base: Metrics, canary: Metrics, g: Gates = Gates()) -> Decision:
    hard, soft = [], []
    if canary.tokens_per_s <= 0 and canary.requests > 0:
        hard.append("canary produced zero tokens while receiving traffic")
    if canary.error_rate > g.error_abs_max:
        hard.append(f"error rate {canary.error_rate:.3f} above hard limit {g.error_abs_max}")
    elif canary.error_rate - base.error_rate > g.error_delta_max:
        soft.append(f"error rate up {canary.error_rate - base.error_rate:.3f} over baseline")
    if base.quality - canary.quality > g.quality_drop_max:
        hard.append(f"quality down {base.quality - canary.quality:.3f} on eval set")
    shift = abs(canary.length_share - base.length_share)
    if shift > g.length_shift_max:
        hard.append(f"finish_reason=length share moved {shift:.2f}")
    for name, c, b, lim in (("ttft_p99", canary.ttft_p99_s, base.ttft_p99_s, g.ttft_ratio_max),
                            ("itl_p99", canary.itl_p99_s, base.itl_p99_s, g.itl_ratio_max)):
        ratio = c / b if b > 0 else float("inf")
        if ratio > lim * (1 + g.hold_band):
            hard.append(f"{name} {ratio:.2f}x baseline, far above {lim}x")
        elif ratio > lim:
            soft.append(f"{name} {ratio:.2f}x baseline, above {lim}x")
    if hard:
        return Decision("rollback", hard + soft)
    if canary.requests < g.min_requests:
        return Decision("hold", [f"only {canary.requests} requests, need {g.min_requests}"] + soft)
    if soft:
        return Decision("hold", soft)
    return Decision("promote", ["all gates passed"])


# ------------------------------------------------------------- rolling update
def rolling_update(replicas: int, max_surge: int, max_unavailable: int,
                   spare_gpu_slots: int, load_ticks: int, max_ticks: int = 200) -> dict:
    """Simulate the Deployment controller's loop, one tick at a time.

    One replica occupies one GPU slot. A new pod holds its slot while loading but is
    not available. The cluster can hold replicas + spare_gpu_slots pods at once.
    Terminating pods free their slot immediately, which is a simplification.
    """
    if max_surge == 0 and max_unavailable == 0:
        raise ValueError("Kubernetes rejects maxSurge=0 with maxUnavailable=0")
    min_available = replicas - max_unavailable
    pod_cap = min(replicas + max_surge, replicas + spare_gpu_slots)
    old, loading, new_ready = replicas, [], 0
    timeline = []
    for tick in range(1, max_ticks + 1):
        loading = [t - 1 for t in loading]
        new_ready += sum(1 for t in loading if t <= 0)
        loading = [t for t in loading if t > 0]
        while old > 0 and old + new_ready - 1 >= min_available:
            old -= 1
        while new_ready + len(loading) < replicas and old + new_ready + len(loading) < pod_cap:
            loading.append(load_ticks)
        timeline.append({"tick": tick, "old": old, "loading": len(loading),
                         "new_ready": new_ready, "available": old + new_ready,
                         "gpus": old + new_ready + len(loading)})
        if new_ready == replicas and old == 0:
            break
    done = new_ready == replicas and old == 0
    return {"done": done, "ticks": len(timeline),
            "min_available": min(r["available"] for r in timeline),
            "peak_gpus": max(r["gpus"] for r in timeline),
            "timeline": timeline}


def blue_green_gpus(replicas: int) -> int:
    """Blue/green keeps the whole old fleet while the whole new fleet loads."""
    return 2 * replicas


def canary_replicas(total_replicas: int, traffic_pct: float) -> int:
    """Replicas needed to carry traffic_pct of traffic at the baseline per-replica load."""
    if not 0 < traffic_pct <= 100:
        raise ValueError("traffic_pct must be in (0, 100]")
    return max(1, math.ceil(total_replicas * traffic_pct / 100))


# ----------------------------------------------------------------- cold start
def cold_start(weights_gb: float, download_gb_s: float, load_gb_s: float,
               compile_s: float, warmup_s: float) -> dict:
    """Seconds from pod scheduled to ready. Stages run one after another."""
    if download_gb_s <= 0 or load_gb_s <= 0:
        raise ValueError("bandwidths must be positive")
    parts = {"download_s": weights_gb / download_gb_s, "load_s": weights_gb / load_gb_s,
             "compile_s": compile_s, "warmup_s": warmup_s}
    parts["total_s"] = sum(parts.values())
    return parts


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "rolling"
    if mode == "rolling":
        for surge, unav, spare in ((1, 0, 1), (1, 0, 0), (0, 1, 0), (2, 0, 2)):
            r = rolling_update(8, surge, unav, spare, load_ticks=4, max_ticks=60)
            print(f"surge={surge} unavail={unav} spare_gpus={spare}: done={r['done']} "
                  f"ticks={r['ticks']} min_available={r['min_available']} peak_gpus={r['peak_gpus']}")
    else:
        data = json.load(open(sys.argv[2]))
        print(json.dumps(asdict(decide(Metrics(**data["base"]), Metrics(**data["canary"]))), indent=2))
