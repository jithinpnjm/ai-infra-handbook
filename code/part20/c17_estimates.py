# code/part20/c17_estimates.py
"""Sizing arithmetic for the twelve drill prompts in chapter 20.17.
Every input is an ASSUMPTION written in the A_* dictionaries. None is a
measurement and none is a Nebius figure. Standard library only."""
import math

# Model facts reused from chapter 20.12 (Qwen3-8B BF16 on one H100 SXM 80 GB).
KV_BYTES_PER_TOKEN = 2 * 36 * 8 * 128 * 2          # 147,456
WEIGHTS_GB, HBM_BW_GBS = 16.4, 3350.0
KV_BUDGET_GB = 50.6                                # 20.12: 72 - 16.4 - 5


def decode_ceiling(batch, ctx=2500):
    """Tokens per second at one decode step, from memory traffic alone."""
    step_s = (WEIGHTS_GB + batch * ctx * KV_BYTES_PER_TOKEN / 1e9) / HBM_BW_GBS
    return batch / step_s


A1 = dict(gpus=4096, per_node=8, gpu_mtbf_h=50_000, job_gpus=512, ckpt_s=120,
          restart_s=600, shares=(50, 30, 20), block_nodes=32, job_nodes=8, busy=3)


def p01_scheduler(a=A1):
    nodes = a["gpus"] // a["per_node"]
    mtbi_h = a["gpu_mtbf_h"] / a["job_gpus"]
    interval = math.sqrt(2 * a["ckpt_s"] * mtbi_h * 3600)       # Young's rule
    lost = interval / 2 + a["restart_s"]
    free = a["block_nodes"] - a["busy"]
    return dict(nodes=nodes, fail_per_day=a["gpus"] * 24 / a["gpu_mtbf_h"],
                job_mtbi_h=mtbi_h, ckpt_interval_min=interval / 60,
                lost_min_per_failure=lost / 60,
                overhead_pct=100 * (a["ckpt_s"] / interval + lost / (mtbi_h * 3600)),
                fair_gpus=[a["gpus"] * s / sum(a["shares"]) for s in a["shares"]],
                jobs_fit_fragmented=free // a["job_nodes"],
                jobs_fit_clean=a["block_nodes"] // a["job_nodes"])


A2 = dict(req_s=300, out_tokens=300, derate=0.6, burst=3, batch=64)


def p02_serving(a=A2):
    per_gpu = a["derate"] * decode_ceiling(a["batch"])
    need = a["req_s"] * a["out_tokens"]
    gpus = math.ceil(need / per_gpu)
    return dict(ceiling_tok_s=decode_ceiling(a["batch"]), per_gpu_tok_s=per_gpu,
                demand_tok_s=need, gpus=gpus, gpus_n_plus_1=gpus + 1,
                burst_gpus=math.ceil(need * a["burst"] / per_gpu))


A3 = dict(gpus=4096, mb_s_per_gpu=50, params_b=70, bytes_per_param=14,
          write_s=60, interval_min=30, keep=5, dataset_tb=2000, hot_frac=0.10,
          hot_usd_gb=0.10, cold_usd_gb=0.02)


def p03_training_storage(a=A3):
    ckpt_gb = a["params_b"] * a["bytes_per_param"]
    gb = a["dataset_tb"] * 1000
    return dict(read_gb_s=a["gpus"] * a["mb_s_per_gpu"] / 1000, ckpt_gb=ckpt_gb,
                write_gb_s=ckpt_gb / a["write_s"],
                avg_write_gb_s=ckpt_gb / (a["interval_min"] * 60),
                kept_tb=ckpt_gb * a["keep"] / 1000,
                all_hot_usd=gb * a["hot_usd_gb"],
                tiered_usd=gb * (a["hot_frac"] * a["hot_usd_gb"]
                                 + (1 - a["hot_frac"]) * a["cold_usd_gb"]))


A4 = dict(nodes=2000, per_node=8, afr=0.05, fields=40, scrape_s=15,
          req_s_replica=2, customer_min=15, detect_min=2)


def p04_gpu_detection(a=A4):
    gpus = a["nodes"] * a["per_node"]
    per_event = a["req_s_replica"] * 60 * (a["customer_min"] - a["detect_min"])
    per_day = gpus * a["afr"] / 365
    return dict(gpus=gpus, failures_per_day=per_day,
                series=gpus * a["fields"], samples_s=gpus * a["fields"] / a["scrape_s"],
                requests_saved_per_event=per_event,
                requests_saved_per_day=per_day * per_event)


A5 = dict(slo=0.999, days=30, fleet=400, in_use=320, growth=0.08, lead_months=3, headroom=0.20)


def p05_sre(a=A5):
    hours = a["days"] * 24
    demand = a["in_use"] * (1 + a["growth"]) ** a["lead_months"]
    need = math.ceil(demand * (1 + a["headroom"]))
    return dict(budget_min=(1 - a["slo"]) * hours * 60,
                budget_pct_14_4_for_1h=100 * 14.4 * 1 / hours,
                budget_pct_6_for_6h=100 * 6 * 6 / hours,
                budget_pct_1_for_72h=100 * 1 * 72 / hours,
                demand_in_lead=demand, gpus_needed=need, gpus_to_order=need - a["fleet"])


A6 = dict(gpus_per_replica=2, replicas=8, usd_gpu_h=3.0, hours=730, warm_frac=0.25,
          detect_min=5, decide_min=5, create_min=15, slo_budget_min=43.2)


def p06_failover(a=A6):
    gpus = a["gpus_per_replica"] * a["replicas"]
    cold = a["detect_min"] + a["decide_min"] + a["create_min"]
    warm = a["detect_min"] + a["decide_min"]
    return dict(gpus=gpus, active_usd=gpus * a["hours"] * a["usd_gpu_h"],
                warm_usd=gpus * a["warm_frac"] * a["hours"] * a["usd_gpu_h"],
                cold_outage_min=cold, cold_budget_pct=100 * cold / a["slo_budget_min"],
                warm_outage_min=warm, warm_budget_pct=100 * warm / a["slo_budget_min"])


A7 = dict(req_s=1000, in_tok=800, out_tok=300, usd_m_in=0.10, usd_m_out=0.40,
          retry_dup=0.02, loss=0.001, event_bytes=200, key_bytes=16)


def p07_metering(a=A7):
    day = a["req_s"] * 86_400
    rev = day * (a["in_tok"] * a["usd_m_in"] + a["out_tok"] * a["usd_m_out"]) / 1e6
    return dict(events_day=day, gb_day=day * a["event_bytes"] / 1e9,
                dedupe_gb=day * a["key_bytes"] / 1e9, revenue_day=rev,
                loss_usd_day=rev * a["loss"], overbill_usd_day=rev * a["retry_dup"])


A8 = dict(prefixes=5000, prefix_tok=2000, dram_gb=512, nvme_gb=8000, pcie_gbs=128,
          nvme_gbs=7, eff=0.5, prefill_flops=400e12, params=8.2e9)


def p08_cache_tier(a=A8):
    one_gb = a["prefix_tok"] * KV_BYTES_PER_TOKEN / 1e9
    return dict(prefix_gb=one_gb, hot_set_tb=a["prefixes"] * one_gb / 1000,
                hbm_fit=int(KV_BUDGET_GB // one_gb), dram_fit=int(a["dram_gb"] // one_gb),
                nvme_fit=int(a["nvme_gb"] // one_gb),
                recompute_ms=1000 * 2 * a["params"] * a["prefix_tok"] / a["prefill_flops"],
                dram_load_ms=1000 * one_gb / (a["pcie_gbs"] * a["eff"]),
                nvme_load_ms=1000 * one_gb / a["nvme_gbs"])


A9 = dict(nodes=100, racks=10, weights_gb=70, origin_gbs=10, node_gbs=3, nvme_gbs=7)


def p09_weights(a=A9):
    naive = a["nodes"] * a["weights_gb"] / a["origin_gbs"]
    seed = a["racks"] * a["weights_gb"] / a["origin_gbs"]
    rounds = math.ceil(math.log2(a["nodes"] / a["racks"]))
    per_round = a["weights_gb"] / a["node_gbs"]
    return dict(naive_s=naive, seed_s=seed, rack_rounds=rounds,
                rack_s=rounds * per_round, tree_s=seed + rounds * per_round,
                gpu_load_s=a["weights_gb"] / a["nvme_gbs"])


A10 = dict(tpm=100_000, prompt=800, max_tokens=1024, actual_out=300,
           tenants=5000, models=50, bucket_bytes=64, gateways=20, req_s=2000)


def p10_rate_limiter(a=A10):
    reserve = a["prompt"] + a["max_tokens"]
    actual = a["prompt"] + a["actual_out"]
    return dict(refill_tok_s=a["tpm"] / 60, reserve=reserve,
                burst_reqs_reserve=a["tpm"] // reserve,
                burst_reqs_actual=a["tpm"] // actual,
                refund_per_req=reserve - actual,
                state_mb=a["tenants"] * a["models"] * a["bucket_bytes"] / 1e6,
                store_ops_s=2 * a["req_s"], lease_tok_per_gw=a["tpm"] / a["gateways"])


A11 = dict(long_ctx=30_000, normal_ctx=2500, tenant_cap=0.25)


def p11_noisy_neighbour(a=A11):
    long_gb = a["long_ctx"] * KV_BYTES_PER_TOKEN / 1e9
    norm_gb = a["normal_ctx"] * KV_BYTES_PER_TOKEN / 1e9
    n_long = int(KV_BUDGET_GB // long_gb)
    left = KV_BUDGET_GB - n_long * long_gb
    return dict(long_gb=long_gb, normal_gb=norm_gb, normal_alone=int(KV_BUDGET_GB // norm_gb),
                long_fill=n_long, left_gb=left, normal_while_long=int(left // norm_gb),
                capped_long=int(a["tenant_cap"] * KV_BUDGET_GB // long_gb))


A12 = dict(endpoints=1000, replicas=6, engine_series=30, hist=4, buckets=12, slis=4,
           windows=5, pairs=3, eval_s=60)


def p12_slo_platform(a=A12):
    per_replica = a["engine_series"] + a["hist"] * a["buckets"]
    return dict(raw_series=a["endpoints"] * a["replicas"] * per_replica,
                slos=a["endpoints"] * a["slis"],
                recorded=a["endpoints"] * a["slis"] * a["windows"],
                alert_rules=a["endpoints"] * a["slis"] * a["pairs"],
                evals_s=a["endpoints"] * a["slis"] * a["pairs"] / a["eval_s"])


ALL = [p01_scheduler, p02_serving, p03_training_storage, p04_gpu_detection, p05_sre,
       p06_failover, p07_metering, p08_cache_tier, p09_weights, p10_rate_limiter,
       p11_noisy_neighbour, p12_slo_platform]

if __name__ == "__main__":
    for fn in ALL:
        print(f"== {fn.__name__}")
        for k, v in fn().items():
            print(f"  {k}: {[round(x, 2) for x in v] if isinstance(v, list) else round(v, 3)}")
