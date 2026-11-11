"""Worked example for chapter 19.9. Prints every number the chapter quotes.
All prices, failure rates and lead times come from c09_assumptions.json and are placeholders."""
from c09_capacity_model import (HOURS_PER_MONTH, forecast_band, horizon_months, monte_carlo,
                                run_plan, size_training, young_interval_seconds, inflation)
from c09_scenario_runner import format_table, load, run_all
from c09_sensitivity import format_table as sens_table, sensitivity


def main():
    doc = load()
    a = doc["base"]
    r = run_plan(a)
    t = r["training"]
    print("== training")
    print(f"6ND FLOPs            {t['flops']:.3e}")
    print(f"ideal GPU-hours      {t['ideal_gpu_hours']:,.0f}")
    print(f"checkpoint write     {t['ckpt_seconds']:.1f} s")
    print(f"inflation            {t['inflation']:.4f}")
    print(f"effective GPU-hours  {t['effective_gpu_hours']:,.0f}")
    print(f"GPUs for deadline    {t['gpus']} ({t['nodes']} nodes), wall clock {t['wall_clock_h']:.0f} h")
    tr = a["training"]
    mtbf_s = tr["gpu_mtbf_h"] * 3600.0 / t["gpus"]
    best = young_interval_seconds(t["ckpt_seconds"], mtbf_s)
    print(f"cluster MTBF         {mtbf_s / 3600:.0f} h; Young interval {best:.0f} s")
    for label, interval in (("1 h", 3600), ("Young", best), ("6 h", 21600)):
        print(f"  interval {label:<6} inflation {inflation(t['ckpt_seconds'], interval, tr['restart_s'], mtbf_s):.4f}")
    slow = size_training(tr["params"], tr["tokens"], tr["deadline_h"], 989.5, tr["mfu"],
                         tr["ckpt_bytes_per_param"], 0.5, tr["ckpt_interval_s"], tr["restart_s"],
                         tr["gpu_mtbf_h"])
    print(f"slow storage 0.5 GB/s: checkpoint {slow['ckpt_seconds']:.0f} s, inflation {slow['inflation']:.4f}, "
          f"GPUs {slow['gpus']}")
    print("== inference")
    i = r["inference"]
    print(f"per-GPU ceiling      {i['rate']:.2f} req/s, latency {i['latency']:.1f} s, TPOT {i['tpot'] * 1000:.1f} ms")
    b = i["band"]
    print(f"QPS in 12 months     P10 {b['p10']:.1f}  P50 {b['p50']:.1f}  P90 {b['p90']:.1f}; trend {b['monthly_growth']:.1%} per month")
    print(f"planned QPS (P90)    {i['qps_end']:.1f}; GPUs at month 12: {i['gpus_end']}")
    print("== estate")
    print(f"fine-tune average GPUs {r['finetune_avg_gpus']:.1f}; notebook GPUs {r['notebook_gpus']}")
    m = r["monthly"]
    print("month  inference training finetune notebooks   total")
    for k in range(a["horizon_months"]):
        print(f"{k + 1:>5}  {m['inference'][k]:>9.0f} {m['training'][k]:>8.1f} {m['finetune'][k]:>8.1f} "
              f"{m['notebooks'][k]:>9.0f} {m['total'][k]:>7.1f}")
    print(f"peak {r['peak_gpus']:.1f} GPUs, spare nodes {r['spare_nodes']}, pool {r['pool_gpus']} GPUs")
    print("== cost (placeholder prices)")
    p = r["prices"]
    print(f"on-demand {p['on_demand']:.2f}, reserved {p['reserved']:.2f}, owned {p['owned']:.2f} USD per GPU-hour; "
          f"owning beats on-demand above {p['breakeven_util']:.1%} utilisation")
    c = r["cost"]
    print(f"all on-demand        {c['all_on_demand']:>12,.0f} USD/yr")
    print(f"reserved, commit {c['reserved_commit'][0]:>3} {c['reserved_commit'][1]:>12,.0f} USD/yr")
    print(f"owned, commit {c['owned_commit'][0]:>3}    {c['owned_commit'][1]:>12,.0f} USD/yr")
    tot = m["total"]
    k = c["owned_commit"][0]
    used = sum(min(x, k) for x in tot) / (k * len(tot))
    print(f"average demand {sum(tot) / len(tot):.1f} GPUs; owned base of {k} is busy {used:.1%} of the time")
    print(f"base hours per month {HOURS_PER_MONTH:.0f}")
    print("== lead times (placeholder days)")
    for k, v in r["lead"].items():
        h = horizon_months(v["days"])
        fb = forecast_band(a["inference"]["qps_history"], h)
        print(f"{k:<10} {v['days']:>4} days -> forecast {h} months ahead, P90 QPS {fb['p90']:.1f}")
    print("== uncertainty (1000 samples, seed 19)")
    mc = monte_carlo(a, 1000, 19)
    print("pool GPUs P10/P50/P90 " + " / ".join(f"{x:.0f}" for x in mc["pool"]))
    print("on-demand USD/yr P10/P50/P90 " + " / ".join(f"{x:,.0f}" for x in mc["cost"]))
    print("== scenarios")
    print(format_table(run_all(doc)))
    print("== sensitivity")
    b0, rows = sensitivity(doc)
    print(sens_table(b0, rows, doc["sensitivity"]["swing"]))


if __name__ == "__main__":
    main()
