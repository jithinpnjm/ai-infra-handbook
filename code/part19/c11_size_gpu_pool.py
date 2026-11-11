"""GPU pool sizing for a training cluster (chapter 19.11). Standard library only.

Sources
- About 6 FLOPs per parameter per token, forward plus backward, dense transformer:
  Distributed AI Systems, ch. 2.
- MFU = (model FLOPs / time) / peak FLOPS: same chapter. 40 to 60 percent is the
  range that book gives for large models.
- Young's first-order checkpoint interval sqrt(2 x C x MTBF): standard result, confirmed
  in chapter 20.17 against Aupy et al. It is a first-order approximation.
- The wall-clock inflation model and the spare-node rule are MY reasoning (labelled
  in the chapter), not from a book.
Every price, failure rate and restart time is an input the caller supplies.
"""
import math

SECONDS_PER_DAY = 86400.0


def train_flops(params, tokens):
    """6 x parameters x tokens."""
    if params <= 0 or tokens <= 0:
        raise ValueError("params and tokens must be positive")
    return 6.0 * params * tokens


def ideal_gpus(flops, peak_tflops, mfu, days):
    """GPUs needed if nothing ever fails: FLOPs / (peak x MFU x seconds)."""
    if not 0 < mfu <= 1:
        raise ValueError("mfu must be in (0, 1]")
    if peak_tflops <= 0 or days <= 0:
        raise ValueError("peak_tflops and days must be positive")
    return flops / (peak_tflops * 1e12 * mfu * days * SECONDS_PER_DAY)


def young_interval_s(ckpt_s, cluster_mtbf_s):
    return math.sqrt(2.0 * ckpt_s * cluster_mtbf_s)


def inflation(ckpt_s, interval_s, restart_s, cluster_mtbf_s):
    """1 + write share + expected lost work per failure / time between failures.
    Lost work per failure is half an interval plus the restart time (my model)."""
    return 1.0 + ckpt_s / interval_s + (interval_s / 2.0 + restart_s) / cluster_mtbf_s


def spare_nodes(nodes, node_mtbf_h, repair_h):
    """Expected nodes down at once = nodes x repair time / node MTBF; one extra node
    so a single surprise does not stall the job (N+1, my reasoning)."""
    return math.ceil(nodes * repair_h / node_mtbf_h) + 1


def min_gpus_for_state(params, bytes_per_param, hbm_gb, usable=0.8):
    """Fewest GPUs whose HBM holds the sharded training state (weights, gradients,
    optimizer). Activations are NOT included, so treat the answer as a floor."""
    if not 0 < usable <= 1:
        raise ValueError("usable must be in (0, 1]")
    return math.ceil(params * bytes_per_param / (hbm_gb * 1e9 * usable))


def size_gpu_pool(params, tokens, days, peak_tflops, mfu, ckpt_s, restart_s,
                  gpu_mtbf_h, repair_h, gpus_per_node=8):
    """Fixed-point sizing: the pool must also pay for checkpoint writes and lost work,
    and a bigger pool fails more often, so iterate until the node count stops changing."""
    flops = train_flops(params, tokens)
    base = ideal_gpus(flops, peak_tflops, mfu, days)
    nodes = math.ceil(base / gpus_per_node)
    for _ in range(50):
        mtbf_s = gpu_mtbf_h * 3600.0 / (nodes * gpus_per_node)
        interval = young_interval_s(ckpt_s, mtbf_s)
        infl = inflation(ckpt_s, interval, restart_s, mtbf_s)
        new = math.ceil(base * infl / gpus_per_node)
        if new == nodes:
            break
        nodes = new
    else:
        raise RuntimeError("sizing did not converge")
    spares = spare_nodes(nodes, gpu_mtbf_h / gpus_per_node, repair_h)
    return {
        "flops": flops, "ideal_gpus": base, "inflation": infl,
        "cluster_mtbf_h": mtbf_s / 3600.0, "ckpt_interval_s": interval,
        "training_nodes": nodes, "training_gpus": nodes * gpus_per_node,
        "spare_nodes": spares, "total_nodes": nodes + spares,
        "total_gpus": (nodes + spares) * gpus_per_node,
    }


def run_cost(gpus, days, usd_per_gpu_hour):
    """Rental-style cost of holding a pool for the run. The price is an input."""
    if gpus < 0 or days <= 0 or usd_per_gpu_hour < 0:
        raise ValueError("gpus, days and price must be non-negative and days positive")
    return gpus * days * 24.0 * usd_per_gpu_hour
