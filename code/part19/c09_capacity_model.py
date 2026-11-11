"""Capacity model for a mixed GPU estate (chapter 19.9). Standard library only.

Every function is one formula with its source named in the docstring.
All prices, failure rates and lead times are PLACEHOLDER inputs that the caller
supplies. Nothing here is a vendor quote or a measurement.
Inference maths is imported from code/part20/capacity_estimator.py (chapter 20.12)
and spare-pool maths from code/part20/c16_spare_pool.py (chapter 20.16).
"""
import copy
import math
import pathlib
import random
import sys

_PART20 = pathlib.Path(__file__).resolve().parents[1] / "part20"
if str(_PART20) not in sys.path:
    sys.path.insert(0, str(_PART20))
import capacity_estimator as ce  # noqa: E402  (20.12: per-GPU capacity, replicas)
import c16_spare_pool as sp  # noqa: E402  (20.16: spares from failure rate x repair time)

HOURS_PER_MONTH = 730.0  # 8760 / 12, the convention used for monthly billing maths
Z80 = 1.2816  # normal quantile for a two-sided 80 percent band (P10 to P90); see chapter caveat


# ---------------------------------------------------------------- training and fine-tuning
def train_flops(params, tokens):
    """About 6 FLOPs per parameter per token, forward plus backward, for a dense
    transformer. Source: Distributed AI Systems, ch. 2 (cites PaLM, Appendix B)."""
    return 6.0 * params * tokens


def gpu_hours_ideal(flops, peak_tflops, mfu):
    """MFU = (model FLOPs / time) / peak FLOPS, so time = FLOPs / (peak x MFU).
    Source: Distributed AI Systems, ch. 2 (MFU definition)."""
    return flops / (peak_tflops * 1e12 * mfu) / 3600.0


def checkpoint_seconds(params, bytes_per_param, write_gb_per_s):
    """Time to write one checkpoint: bytes / bandwidth. bytes_per_param is an input:
    Distributed AI Systems ch. 2 says Adam state is about 2x the model size, so
    bf16 weights plus Adam state is 2 + 4 = 6 bytes per parameter by that book's count."""
    return params * bytes_per_param / (write_gb_per_s * 1e9)


def young_interval_seconds(ckpt_s, cluster_mtbf_s):
    """Young's first-order optimal checkpoint interval sqrt(2 x C x MTBF).
    Standard result, NOT from the gem books; labelled unverified in the chapter."""
    return math.sqrt(2.0 * ckpt_s * cluster_mtbf_s)


def inflation(ckpt_s, interval_s, restart_s, cluster_mtbf_s):
    """Wall-clock multiplier from checkpointing and failures (my first-order model).
    1 + checkpoint write share + expected lost work per failure / time between failures.
    Lost work per failure is half an interval plus the restart time."""
    write_share = ckpt_s / interval_s
    failure_share = (interval_s / 2.0 + restart_s) / cluster_mtbf_s
    return 1.0 + write_share + failure_share


def size_training(params, tokens, deadline_h, peak_tflops, mfu, ckpt_bytes_per_param,
                  write_gb_per_s, interval_s, restart_s, gpu_mtbf_h, gpus_per_node=8):
    """GPUs needed to finish by the deadline. GPU count changes cluster MTBF
    (MTBF_cluster = MTBF_gpu / GPUs, independent failures) and MTBF changes the
    inflation, so iterate to a fixed point."""
    flops = train_flops(params, tokens)
    ideal_h = gpu_hours_ideal(flops, peak_tflops, mfu)
    ckpt_s = checkpoint_seconds(params, ckpt_bytes_per_param, write_gb_per_s)
    gpus = math.ceil(ideal_h / deadline_h / gpus_per_node) * gpus_per_node
    infl = 1.0
    for _ in range(50):
        mtbf_s = gpu_mtbf_h * 3600.0 / gpus
        infl = inflation(ckpt_s, interval_s, restart_s, mtbf_s)
        need = math.ceil(ideal_h * infl / deadline_h / gpus_per_node) * gpus_per_node
        if need == gpus:
            break
        gpus = need
    effective_h = ideal_h * infl
    return {"flops": flops, "ideal_gpu_hours": ideal_h, "ckpt_seconds": ckpt_s,
            "inflation": infl, "effective_gpu_hours": effective_h, "gpus": gpus,
            "wall_clock_h": effective_h / gpus, "nodes": gpus // gpus_per_node}


# ---------------------------------------------------------------- inference and notebooks
def inference_replica_rate(cfg, gpu):
    """Per-GPU request ceiling, using the 20.12 functions unchanged."""
    params, layers, kvh, hd = ce.MODELS[cfg["model"]]
    mem, bw, tflops, _price = ce.GPUS[gpu]
    w = ce.weights_gb(params, cfg.get("bytes_per_param", 2))
    bpt = ce.kv_bytes_per_token(layers, kvh, hd)
    ctx = cfg["in_tokens"] + cfg["out_tokens"]
    d_tps = ce.decode_tps(cfg["batch"], ctx, w, bpt, bw)
    p_tps = ce.prefill_tps(tflops, cfg["mfu"], params)
    rate, latency, tpot = ce.per_gpu_capacity(cfg["in_tokens"], cfg["out_tokens"],
                                               cfg["batch"], p_tps, d_tps)
    return rate, latency, tpot


def inference_gpus(qps, rate, target_util, spares):
    """20.12 section 8: ceil(QPS / (rate x target)) + spare replicas (one GPU each here)."""
    return ce.replicas_needed(qps, rate, target_util, spares)


def notebook_gpus(users, peak_concurrency, sessions_per_gpu):
    """Concurrent sessions at the peak, shared several to a GPU. My arithmetic."""
    return math.ceil(users * peak_concurrency / sessions_per_gpu)


def finetune_avg_gpus(runs_per_month, params, tokens, peak_tflops, mfu, batch_util):
    """Monthly GPU-hours from 6ND and MFU, spread over the month, divided by the
    utilisation target the platform can actually reach for batch work."""
    h = runs_per_month * gpu_hours_ideal(train_flops(params, tokens), peak_tflops, mfu)
    return h / HOURS_PER_MONTH / batch_util


# ---------------------------------------------------------------- forecasting
def fit_log_linear(history):
    """Ordinary least squares on ln(y) against month index. Returns (a, b, s, n)."""
    n = len(history)
    ys = [math.log(v) for v in history]
    xbar = (n - 1) / 2.0
    ybar = sum(ys) / n
    sxx = sum((i - xbar) ** 2 for i in range(n))
    b = sum((i - xbar) * (y - ybar) for i, y in enumerate(ys)) / sxx
    a = ybar - b * xbar
    sse = sum((y - (a + b * i)) ** 2 for i, y in enumerate(ys))
    s = math.sqrt(sse / (n - 2)) if n > 2 else 0.0
    return a, b, s, n


def forecast_band(history, months_ahead, z=Z80):
    """Prediction band for a log-linear trend: ln y0 +/- z x s x sqrt(1 + 1/n + (x0-xbar)^2/Sxx).
    Standard OLS prediction interval; normal z is an approximation for small n."""
    a, b, s, n = fit_log_linear(history)
    xbar = (n - 1) / 2.0
    sxx = sum((i - xbar) ** 2 for i in range(n))
    x0 = n - 1 + months_ahead
    centre = a + b * x0
    se = s * math.sqrt(1.0 + 1.0 / n + (x0 - xbar) ** 2 / sxx)
    return {"p10": math.exp(centre - z * se), "p50": math.exp(centre),
            "p90": math.exp(centre + z * se), "monthly_growth": math.exp(b) - 1.0}


def horizon_months(lead_days):
    """Months you must forecast ahead for an option with this lead time (30-day months)."""
    return math.ceil(lead_days / 30.0)


# ---------------------------------------------------------------- cost
def reserved_price(on_demand, discount):
    return on_demand * (1.0 - discount)


def owned_cost_per_gpu_hour(capex, life_years, opex_per_gpu_hour):
    """Straight-line amortisation of capex over the life, plus running cost.
    Charged for every hour, used or not."""
    return capex / (life_years * 8760.0) + opex_per_gpu_hour


def breakeven_utilisation(owned_hourly, rent_hourly):
    """Owning is cheaper than renting on demand when used hours / owned hours
    exceeds owned_hourly / rent_hourly."""
    return owned_hourly / rent_hourly


def spot_effective_price(spot, rework_fraction):
    """Spot price divided by the share of paid time that is useful work."""
    return spot / (1.0 - rework_fraction)


def annual_cost_with_commit(demand_by_month, commit, od, res):
    """Reserved or owned-like base of `commit` GPUs paid every hour at `res`,
    demand above it bought on demand at `od`. Demand is average GPUs per month."""
    cost = 0.0
    for d in demand_by_month:
        cost += commit * res * HOURS_PER_MONTH + max(0.0, d - commit) * od * HOURS_PER_MONTH
    return cost


def best_commit(demand_by_month, od, res):
    """Search whole-GPU commits from 0 to the peak; return (commit, cost)."""
    top = math.ceil(max(demand_by_month))
    best = min(range(top + 1), key=lambda c: annual_cost_with_commit(demand_by_month, c, od, res))
    return best, annual_cost_with_commit(demand_by_month, best, od, res)


# ---------------------------------------------------------------- the whole plan
def monthly_inference_qps(q0, q_end, months):
    g = (q_end / q0) ** (1.0 / months) - 1.0
    return [q0 * (1.0 + g) ** m for m in range(1, months + 1)], g


def run_plan(a):
    """One deterministic plan from an assumptions dict (see c09_assumptions.json)."""
    gpu = a["gpu"]
    peak_tflops = ce.GPUS[gpu][2]
    gpn = a.get("gpus_per_node", 8)
    months = a["horizon_months"]
    bu = a["batch_util"]

    inf = a["inference"]
    rate, latency, tpot = inference_replica_rate(inf, gpu)
    band = forecast_band(inf["qps_history"], months)
    qps_end = band[inf["planning_percentile"]] * inf["qps_multiplier"]
    q0 = inf["qps_history"][-1]
    qps_m, g = monthly_inference_qps(q0, qps_end, months)
    inf_m = [inference_gpus(q, rate, inf["target_util"], inf["spares"]) for q in qps_m]

    t = a["training"]
    tr = size_training(t["params"], t["tokens"] * t.get("token_multiplier", 1.0), t["deadline_h"],
                       peak_tflops, t["mfu"], t["ckpt_bytes_per_param"], t["write_gb_per_s"],
                       t["ckpt_interval_s"], t["restart_s"], t["gpu_mtbf_h"], gpn)
    tr_m = [tr["gpus"] * f / bu for f in t["active_fraction_by_month"][:months]]

    f = a["finetune"]
    ft_avg = finetune_avg_gpus(f["runs_per_month"], f["params"], f["tokens"], peak_tflops,
                               f["mfu"], bu)
    ft_m = [ft_avg] * months

    n = a["notebooks"]
    nb = notebook_gpus(n["users"], n["peak_concurrency"], n["sessions_per_gpu"])
    nb_m = [float(nb)] * months

    total_m = [i + x + y + z for i, x, y, z in zip(inf_m, tr_m, ft_m, nb_m)]
    peak = max(total_m)
    fleet_nodes = math.ceil(peak / gpn)
    sr = a["spares"]
    spare_nodes = sp.spares_needed(fleet_nodes, sr["annual_failure_rate"], sr["mttr_hours"],
                                   sr["coverage"])
    pool = math.ceil(peak / gpn) * gpn + spare_nodes * gpn

    pr = a["prices"]
    od = pr["on_demand_per_gpu_hour"]
    res = reserved_price(od, pr["reserved_discount"])
    own = owned_cost_per_gpu_hour(pr["own_capex_per_gpu"], pr["own_life_years"],
                                  pr["own_opex_per_gpu_hour"])
    all_od = sum(total_m) * HOURS_PER_MONTH * od
    c_res, cost_res = best_commit(total_m, od, res)
    c_own, cost_own = best_commit(total_m, od, own)
    cost_own += spare_nodes * gpn * own * 8760.0  # owned spares are paid for every hour
    return {
        "inference": {"rate": rate, "latency": latency, "tpot": tpot, "band": band,
                      "monthly_growth": g, "qps_end": qps_end, "gpus_end": inf_m[-1]},
        "training": tr, "finetune_avg_gpus": ft_avg, "notebook_gpus": nb,
        "monthly": {"inference": inf_m, "training": tr_m, "finetune": ft_m, "notebooks": nb_m,
                    "total": total_m},
        "peak_gpus": peak, "spare_nodes": spare_nodes, "pool_gpus": pool,
        "prices": {"on_demand": od, "reserved": res, "owned": own,
                   "breakeven_util": breakeven_utilisation(own, od)},
        "cost": {"all_on_demand": all_od, "reserved_commit": (c_res, cost_res),
                 "owned_commit": (c_own, cost_own)},
        "lead": {k: {"days": v, "months_ahead": horizon_months(v)}
                 for k, v in a["lead_days"].items()},
    }


# ---------------------------------------------------------------- uncertainty
def set_path(d, path, value):
    keys = path.split(".")
    for k in keys[:-1]:
        d = d[k]
    d[keys[-1]] = value


def get_path(d, path):
    for k in path.split("."):
        d = d[k]
    return d


def percentile(sorted_vals, q):
    """Linear-interpolated percentile of an ascending list, q in 0..1."""
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def monte_carlo(a, n=1000, seed=19):
    """Sample each a['uncertainty'] entry [low, mode, high] from a triangular
    distribution, re-run the plan, return P10, P50, P90 of pool size and annual
    on-demand cost. Seeded, so the output is repeatable."""
    rng = random.Random(seed)
    pools, costs = [], []
    for _ in range(n):
        b = copy.deepcopy(a)
        for path, (lo, mode, hi) in a["uncertainty"].items():
            set_path(b, path, rng.triangular(lo, hi, mode))
        r = run_plan(b)
        pools.append(r["pool_gpus"])
        costs.append(r["cost"]["all_on_demand"])
    pools.sort()
    costs.sort()
    return {"pool": [percentile(pools, q) for q in (0.1, 0.5, 0.9)],
            "cost": [percentile(costs, q) for q in (0.1, 0.5, 0.9)]}
