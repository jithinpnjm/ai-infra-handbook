"""Back-of-envelope inference capacity maths. Standard library only.
Every function is one formula from chapter 20.12. Results are ceilings, not measurements."""
import argparse
import math

GB = 1e9  # decimal gigabytes, the unit GPU datasheets use
# name: (params in billions, layers, kv heads, head dim) from the model cards
MODELS = {"qwen3-8b": (8.2, 36, 8, 128), "qwen2.5-72b": (72.7, 80, 8, 128)}
# name: (memory GB, bandwidth GB/s, dense bf16 TFLOPS, USD per GPU-hour)
GPUS = {"h100": (80, 3350, 989.5, 4.50), "h200": (141, 4800, 989.5, 5.40)}


def weights_gb(params_b, bytes_per_param):
    return params_b * bytes_per_param


def kv_bytes_per_token(layers, kv_heads, head_dim, dtype_bytes=2):
    return 2 * layers * kv_heads * head_dim * dtype_bytes


def max_concurrent(gpu_gb, n_gpus, util, w_gb, overhead_gb, req_kv_gb):
    free = gpu_gb * n_gpus * util - w_gb - overhead_gb * n_gpus
    return max(0, int(free // req_kv_gb))


def decode_tps(batch, ctx_tokens, w_gb, bpt, bw_gbs):
    """Every decode step reads all weights once plus every request's KV cache."""
    step_s = (w_gb + batch * ctx_tokens * bpt / GB) / bw_gbs
    return batch / step_s


def prefill_tps(tflops, mfu, params_b):
    """About 2 FLOPs per parameter per prompt token, at an assumed utilisation."""
    return tflops * 1e12 * mfu / (2 * params_b * 1e9)


def per_gpu_capacity(in_tok, out_tok, batch, p_tps, d_tps):
    """Prefill and decode share the GPU, so their seconds add per request."""
    gpu_s = in_tok / p_tps + out_tok / d_tps
    rate = 1 / gpu_s
    latency = batch / rate  # Little's law: concurrency = rate x time in system
    return rate, latency, (latency - in_tok / p_tps) / out_tok


def replicas_needed(qps, replica_qps, target_util, spare=1):
    return math.ceil(qps / (replica_qps * target_util)) + spare


def cost_per_m_tokens(usd_per_gpu_hour, gpus, tokens_per_s, utilisation):
    return usd_per_gpu_hour * gpus / (tokens_per_s * 3600 * utilisation) * 1e6


def goodput_qps(qps, fraction_within_slo):
    return qps * fraction_within_slo


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--model", choices=MODELS, default="qwen3-8b")
    a.add_argument("--gpu", choices=GPUS, default="h100")
    a.add_argument("--tp", type=int, default=1, help="GPUs per replica")
    a.add_argument("--bytes-per-param", type=float, default=2)
    a.add_argument("--in-tokens", type=int, default=2000)
    a.add_argument("--out-tokens", type=int, default=500)
    a.add_argument("--batch", type=int, default=64)
    a.add_argument("--qps", type=float, default=40)
    a.add_argument("--mem-util", type=float, default=0.90)
    a.add_argument("--overhead-gb", type=float, default=5, help="per GPU, assumed")
    a.add_argument("--mfu", type=float, default=0.40, help="assumed")
    a.add_argument("--target-util", type=float, default=0.90)
    a.add_argument("--gpu-utilisation", type=float, default=1.0)
    a.add_argument("--kv-bytes", type=int, default=2)
    x = a.parse_args()
    params, layers, kvh, hd = MODELS[x.model]
    mem, bw, tflops, price = GPUS[x.gpu]
    w = weights_gb(params, x.bytes_per_param)
    bpt = kv_bytes_per_token(layers, kvh, hd, x.kv_bytes)
    req_gb = (x.in_tokens + x.out_tokens) * bpt / GB
    fit = max_concurrent(mem, x.tp, x.mem_util, w, x.overhead_gb, req_gb)
    ctx = x.in_tokens + x.out_tokens
    d_tps = decode_tps(x.batch, ctx, w, bpt, bw * x.tp)
    p_tps = prefill_tps(tflops * x.tp, x.mfu, params)
    rate, lat, tpot = per_gpu_capacity(x.in_tokens, x.out_tokens, x.batch, p_tps, d_tps)
    n = replicas_needed(x.qps, rate, x.target_util)
    cost = cost_per_m_tokens(price, x.tp, rate * x.out_tokens, x.gpu_utilisation)
    print(f"weights {w:.1f} GB, KV {bpt} B/token, {req_gb:.4f} GB/request, fits {fit} requests")
    print(f"decode ceiling {d_tps:.0f} tok/s at batch {x.batch}, prefill {p_tps:.0f} tok/s")
    print(f"replica ceiling {rate:.2f} req/s, latency {lat:.1f} s, TPOT {tpot * 1000:.1f} ms")
    print(f"{n} replicas, {n * x.tp} GPUs for {x.qps:g} QPS; ${cost:.2f} per million output tokens")


if __name__ == "__main__":
    main()
