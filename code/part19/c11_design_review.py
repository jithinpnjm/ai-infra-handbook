"""Design review checklist runner over a design dict (chapter 19.11).

Each check returns PASS, FAIL or WARN with one sentence. A missing key is a FAIL, not a
crash: a design that cannot answer the question has not passed it. Thresholds
(3 percent checkpoint budget, 90 percent quota rule) are MY policy defaults.
"""
import math

REQUIRED_SIGNALS = {"gpu_xid", "nccl_busbw", "ib_link_errors", "step_time", "checkpoint_age"}


def _get(d, *path):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


def run_review(d, ckpt_budget=0.03):
    out = []

    def rec(name, ok, msg, warn=False):
        out.append((name, "PASS" if ok else ("WARN" if warn else "FAIL"), msg))

    w = _get(d, "workload")
    if not w or any(k not in w for k in ("params", "tokens", "days")):
        rec("requirements", False, "workload needs params, tokens and days")
    else:
        rec("requirements", True, "workload stated")
        need = 6 * w["params"] * w["tokens"]
        g = _get(d, "pool")
        if g and all(k in g for k in ("gpus", "peak_tflops", "mfu")):
            have = g["gpus"] * g["peak_tflops"] * 1e12 * g["mfu"] * w["days"] * 86400
            rec("compute", have >= need,
                "pool delivers %.2e FLOPs, job needs %.2e" % (have, need))
        else:
            rec("compute", False, "pool needs gpus, peak_tflops and mfu")
    m = _get(d, "memory")
    if m and all(k in m for k in ("state_gb_per_gpu", "hbm_gb")):
        rec("memory", m["state_gb_per_gpu"] <= 0.8 * m["hbm_gb"],
            "state %.1f GB of %.0f GB HBM (80 percent rule)" % (m["state_gb_per_gpu"], m["hbm_gb"]))
    else:
        rec("memory", False, "memory needs state_gb_per_gpu and hbm_gb")
    f = _get(d, "fabric")
    if f and "leaf_oversub" in f:
        rec("fabric", f["leaf_oversub"] == 1,
            "leaf oversubscription %s:1" % f["leaf_oversub"], warn=f["leaf_oversub"] <= 2)
    else:
        rec("fabric", False, "fabric needs leaf_oversub")
    r = _get(d, "rack")
    if r and all(k in r for k in ("nodes_per_rack", "node_kw", "rack_limit_kw")):
        kw = r["nodes_per_rack"] * r["node_kw"]
        rec("power", kw <= r["rack_limit_kw"], "rack draws %.1f kW of %.1f kW" % (kw, r["rack_limit_kw"]))
    else:
        rec("power", False, "rack needs nodes_per_rack, node_kw and rack_limit_kw")
    s = _get(d, "spares")
    if s and all(k in s for k in ("have", "nodes", "node_mtbf_h", "repair_h")):
        need_s = math.ceil(s["nodes"] * s["repair_h"] / s["node_mtbf_h"]) + 1
        rec("spares", s["have"] >= need_s, "%d spare nodes, rule asks for %d" % (s["have"], need_s))
    else:
        rec("spares", False, "spares needs have, nodes, node_mtbf_h and repair_h")
    st = _get(d, "storage")
    if st and all(k in st for k in ("ckpt_write_s", "ckpt_interval_s")):
        frac = st["ckpt_write_s"] / st["ckpt_interval_s"]
        rec("checkpoint", frac <= ckpt_budget, "synchronous stall %.2f percent, budget %.0f percent"
            % (100 * frac, 100 * ckpt_budget))
    else:
        rec("checkpoint", False, "storage needs ckpt_write_s and ckpt_interval_s")
    sc = _get(d, "scheduler")
    rec("scheduler", bool(sc and sc.get("choice") and sc.get("reasons")),
        "scheduler named with reasons" if sc and sc.get("choice") else "scheduler or reasons missing")
    ob = set(_get(d, "observability") or [])
    gap = sorted(REQUIRED_SIGNALS - ob)
    rec("observability", not gap, "all signals present" if not gap else "missing: " + ", ".join(gap))
    q = _get(d, "tenants")
    pool = _get(d, "pool", "gpus")
    if q and pool:
        tot = sum(q.values())
        rec("quota", tot <= pool, "quotas total %d GPUs of %d" % (tot, pool))
    else:
        rec("quota", False, "tenants and pool.gpus needed")
    fh = _get(d, "failure_plan")
    rec("failure_plan", bool(fh and fh.get("health_check") and fh.get("auto_restart")),
        "health check and automatic restart named" if fh and fh.get("health_check") and fh.get("auto_restart")
        else "failure_plan needs health_check and auto_restart")
    return out


def passed(results):
    return all(s == "PASS" for _, s, _ in results)
