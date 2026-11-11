"""Worked example for chapter 19.11. Run: python3 c11_worked_example.py
Workload (all inputs are stated assumptions): 70e9 parameters, 2e12 tokens, 30 days,
B200 at 2250 TFLOPS dense BF16, MFU 0.40, per-GPU MTBF 50,000 h, restart 10 min,
repair 24 h, 4 bytes per token, checkpoint written at 45 GB/s."""
import json
import pathlib

import c11_choose_scheduler as cs
import c11_design_review as dr
import c11_design_storage as ds
import c11_select_topology as tp
import c11_size_gpu_pool as sz

P, T, DAYS = 70e9, 2e12, 30
PEAK, MFU = 2250.0, 0.40
HERE = pathlib.Path(__file__).parent


def build():
    ckpt_s = ds.checkpoint_write_s(P, 45.0)
    pool = sz.size_gpu_pool(P, T, DAYS, PEAK, MFU, ckpt_s, 600.0, 50000.0, 24.0)
    tok_s = T / (DAYS * 86400)
    return ckpt_s, pool, tok_s


def main():
    ckpt_s, pool, tok_s = build()
    print("FLOPs: %.3e" % pool["flops"])
    print("ideal GPUs: %.1f" % pool["ideal_gpus"])
    print("checkpoint bytes: %.0f GB, write %.1f s at 45 GB/s" % (ds.checkpoint_bytes(P) / 1e9, ckpt_s))
    print("cluster MTBF: %.1f h, Young interval: %.0f s" % (pool["cluster_mtbf_h"], pool["ckpt_interval_s"]))
    print("inflation: %.4f" % pool["inflation"])
    print("training nodes %d (%d GPUs), spares %d, total nodes %d (%d GPUs)" % (
        pool["training_nodes"], pool["training_gpus"], pool["spare_nodes"],
        pool["total_nodes"], pool["total_gpus"]))
    print("state floor: %d GPUs at 16 B/param on 192 GB at 80 percent" % sz.min_gpus_for_state(P, 16, 192))
    print("dataset read: %.1f MB/s" % (ds.dataset_read_gbs(tok_s, 4) * 1000))
    print("sync stall at 1800 s: %.2f percent" % (100 * ds.stall_fraction(ckpt_s, 1800)))
    print("write bandwidth for 3 percent at 1800 s: %.1f GB/s" % ds.min_write_gbs(P, 1800, 0.03))
    print("retained 5 checkpoints: %.2f TB" % ds.retained_tb(P, 5))
    cost = sz.run_cost(pool["training_gpus"], DAYS, 8.50)
    print("run cost at 8.50 per GPU-hour, %d GPUs, %d days: %.0f USD" % (pool["training_gpus"], DAYS, cost))
    print("sync checkpoint stall costs: %.0f USD" % (cost * ds.stall_fraction(ckpt_s, 1800)))
    g41 = sz.ideal_gpus(pool["flops"], PEAK, MFU + 0.01, DAYS)
    print("one more MFU point saves %.1f GPUs, %.0f USD" % (pool["ideal_gpus"] - g41, sz.run_cost(pool["ideal_gpus"] - g41, DAYS, 8.50)))
    ft = tp.fat_tree(pool["total_gpus"], 64)
    print("fabric (64-port): %s" % json.dumps(ft))
    print("max two-tier endpoints at 64 ports: %d" % tp.max_two_tier_endpoints(64))
    print("scale-up to scale-out ratio, 1800 GB/s vs 400 Gb/s: %.0f" % tp.scale_up_to_out_ratio(1800, 400))
    racks = -(-pool["total_nodes"] // 2)
    print("racks at 2 nodes each: %d, power %.1f kW" % (racks, pool["total_nodes"] * 14.3))
    d = json.loads((HERE / "c11_design_example.json").read_text())
    dec = cs.choose_scheduler(d["scheduler_profile"])
    print("scheduler: %s (slurm %d, k8s %d)" % (dec["choice"], dec["slurm_score"], dec["k8s_score"]))
    alt = cs.choose_scheduler(d["scheduler_profile_alt"])
    print("alternative profile: %s (slurm %d, k8s %d)" % (alt["choice"], alt["slurm_score"], alt["k8s_score"]))
    for name, status, msg in dr.run_review(d["design"]):
        print("%-14s %-4s %s" % (name, status, msg))


if __name__ == "__main__":
    main()
