#!/usr/bin/env python3
"""Review a `vllm serve` argument set for contradictions and risky combinations.

Standard library only. Every rule names the vLLM v0.32.0 document or source file
that states the behaviour. Rules marked "inference" are reasoning, not documentation.

Usage:
  python3 c22_vllm_config_review.py --gpus-per-node 8 --gpu-arch hopper -- \
      vllm serve meta-llama/Llama-3.3-70B-Instruct --tensor-parallel-size 4
"""
import argparse
import sys
from dataclasses import dataclass

# Flags that take no value. Everything else takes one value, except the two lists below.
BOOL_FLAGS = {
    "enforce-eager", "enable-expert-parallel", "headless", "numa-bind",
    "enable-chunked-prefill", "no-enable-chunked-prefill",
    "enable-prefix-caching", "no-enable-prefix-caching",
}
LIST_FLAGS = {"numa-bind-nodes", "numa-bind-cpus"}
INT_FLAGS = {
    "tensor-parallel-size", "pipeline-parallel-size", "data-parallel-size",
    "max-model-len", "max-num-seqs", "max-num-batched-tokens", "nnodes",
    "kv-cache-memory",
}


@dataclass
class Finding:
    rule: str
    severity: str  # error | warn | info
    message: str
    source: str


def parse_args(argv):
    """Turn a command line into a dict keyed by flag name without dashes, underscores as dashes."""
    out, i = {}, 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("-O") and tok[2:].isdigit():
            out["optimization-level"] = int(tok[2:])
            i += 1
            continue
        if not tok.startswith("--"):
            i += 1  # "vllm", "serve", the model name
            continue
        name, eq, value = tok[2:].partition("=")
        name = name.replace("_", "-")
        if name in BOOL_FLAGS:
            out[name] = True
            i += 1
        elif name in LIST_FLAGS:
            vals, i = ([value] if eq else []), i + 1
            while i < len(argv) and not argv[i].startswith("-"):
                vals.append(argv[i])
                i += 1
            out[name] = vals
        else:
            if not eq:
                i += 1
                value = argv[i] if i < len(argv) else ""
            out[name] = int(value) if name in INT_FLAGS and value.lstrip("-").isdigit() else value
            i += 1
    return out


def _num(args, key, default=None):
    v = args.get(key, default)
    return v if isinstance(v, (int, float)) else default


def _float(args, key):
    try:
        return float(args[key])
    except (KeyError, ValueError):
        return None


def review(args, gpus_per_node=None, gpu_arch=None, kv_cache_tokens=None):
    """Return a list of Findings. Context arguments come from the node, not from vLLM flags."""
    f = []
    tp = _num(args, "tensor-parallel-size", 1)
    pp = _num(args, "pipeline-parallel-size", 1)
    dp = _num(args, "data-parallel-size", 1)
    nnodes = _num(args, "nnodes", 1)
    mml = _num(args, "max-model-len")
    mnbt = _num(args, "max-num-batched-tokens")
    mns = _num(args, "max-num-seqs")
    backend = args.get("distributed-executor-backend")

    # 1. Chunked prefill off requires a token budget above max_model_len.
    if args.get("no-enable-chunked-prefill"):
        if mnbt is not None and mml is not None and mnbt < mml:
            f.append(Finding("chunked-prefill-budget", "error",
                f"chunked prefill is off and max-num-batched-tokens={mnbt} is below max-model-len={mml}. "
                "vLLM may crash at start-up.",
                "docs/configuration/optimization.md, Chunked Prefill warning"))
        elif mnbt is None or mml is None:
            f.append(Finding("chunked-prefill-budget", "warn",
                "chunked prefill is off but max-num-batched-tokens or max-model-len is not set here. "
                "The budget must exceed max-model-len. Read both values from the start-up log.",
                "docs/configuration/optimization.md, Chunked Prefill warning"))

    # 2. kv-cache-memory overrides the utilisation fraction.
    util = _float(args, "gpu-memory-utilization")
    if util is not None and not (0 < util <= 1):
        f.append(Finding("gpu-util-range", "error",
            f"gpu-memory-utilization={util} is outside (0, 1].",
            "vllm/config/cache.py, Field(gt=0, le=1)"))
    if "kv-cache-memory" in args and util is not None:
        f.append(Finding("kv-cache-memory-ignores-util", "warn",
            "kv-cache-memory is set together with gpu-memory-utilization. "
            "The explicit KV size wins and the fraction is ignored.",
            "vllm/config/cache.py, kv_cache_memory_bytes docstring"))
    if "kv-cache-memory" in args:
        f.append(Finding("kv-cache-memory-sizing", "info",
            "kv-cache-memory skips memory profiling, which shortens start-up. "
            "A low value caps concurrency and a high value can fail at allocation.",
            "docs/configuration/optimization.md, Faster Startup"))

    # 3. Parallel layout against the hardware.
    if gpus_per_node is not None:
        total = gpus_per_node * nnodes
        if tp * pp > total and backend != "ray":
            f.append(Finding("world-size-exceeds-gpus", "error",
                f"tensor x pipeline = {tp * pp} but only {total} GPUs are available. "
                "Without enough GPUs on the host and without nnodes, multi-process mode raises an error. "
                "Ray must be chosen explicitly for multi-node.",
                "vllm/config/parallel.py, distributed_executor_backend docstring"))
        if tp > gpus_per_node:
            f.append(Finding("tp-crosses-nodes", "warn",
                f"tensor-parallel-size={tp} is larger than the {gpus_per_node} GPUs per node. "
                "The guidance is tensor parallel equal to GPUs per node and pipeline parallel equal to nodes. "
                "Tensor parallelism across nodes needs fast inter-node links.",
                "docs/serving/parallelism_scaling.md, Multi-node deployment"))
        if "numa-bind-nodes" in args and len(args["numa-bind-nodes"]) != gpus_per_node:
            f.append(Finding("numa-nodes-count", "error",
                f"numa-bind-nodes has {len(args['numa-bind-nodes'])} entries for {gpus_per_node} visible GPUs. "
                "It takes one NUMA node per visible GPU.",
                "docs/configuration/optimization.md, NUMA Binding"))
    if nnodes > 1 and backend != "ray" and "master-addr" not in args:
        f.append(Finding("mp-multinode-needs-master", "error",
            "nnodes > 1 with multiprocessing needs master-addr, and node-rank on each node.",
            "docs/serving/parallelism_scaling.md, Running vLLM with MultiProcessing"))
    if ("numa-bind-nodes" in args or "numa-bind-cpus" in args) and not args.get("numa-bind"):
        f.append(Finding("numa-flags-without-switch", "warn",
            "numa-bind-nodes or numa-bind-cpus given without numa-bind. "
            "Inference: the docs show the lists only alongside numa-bind.",
            "docs/configuration/optimization.md, NUMA Binding (inference)"))
    if args.get("enable-expert-parallel") and tp * dp == 1:
        f.append(Finding("ep-without-sharding", "warn",
            "enable-expert-parallel uses the tensor-parallel degree and MoE layers shard over tensor x data. "
            "Both are 1 here, so there is nothing to spread experts across.",
            "docs/configuration/optimization.md, Expert Parallelism and Data Parallelism"))

    # 4. Quantisation against hardware.
    quant = str(args.get("quantization", "")).lower()
    if quant == "awq" and gpu_arch == "volta":
        f.append(Finding("awq-on-volta", "error",
            "AWQ is not supported on Volta in the compatibility table.",
            "docs/features/quantization/README.md, Supported Hardware"))
    if quant == "fp8" and gpu_arch in {"volta", "turing", "ampere"}:
        f.append(Finding("fp8-w8a8-hardware", "warn",
            "The table marks llm-compressor FP8 W8A8 as supported on Ada, Hopper and AMD GPUs only. "
            "Other FP8 paths such as Marlin may behave differently. Check the start-up log.",
            "docs/features/quantization/README.md, Supported Hardware"))

    # 5. Capacity: worst-case concurrency from the start-up log.
    if kv_cache_tokens and mml and mns:
        worst = kv_cache_tokens / mml
        if mns > worst:
            f.append(Finding("seqs-exceed-worst-case-kv", "info",
                f"max-num-seqs={mns} is above {worst:.2f}, the number of full-length requests the KV cache holds "
                f"({kv_cache_tokens} tokens / {mml}). Safe for short requests, but a burst of long ones preempts.",
                "docs/serving/parallelism_scaling.md, Maximum concurrency log line; docs/configuration/optimization.md, Preemption"))

    # 6. Start-up and speed trade-offs.
    if args.get("enforce-eager"):
        f.append(Finding("enforce-eager", "warn",
            "enforce-eager skips compilation and CUDA graph capture. Start-up is fast and steady-state decode is slower.",
            "docs/configuration/optimization.md, Faster Startup"))
    if args.get("optimization-level") == 0:
        f.append(Finding("opt-level-0", "warn",
            "-O0 gives the fastest start-up and the lowest performance. Production default is -O2.",
            "docs/configuration/optimization.md, Optimization Levels"))
    if mnbt is not None and mnbt <= 2048:
        f.append(Finding("small-token-budget", "info",
            f"max-num-batched-tokens={mnbt}. Smaller values favour inter-token latency, larger values favour "
            "time to first token. The guide recommends more than 8192 for throughput.",
            "docs/configuration/optimization.md, Performance Tuning with Chunked Prefill"))

    # 7. Prefix caching.
    if args.get("no-enable-prefix-caching"):
        f.append(Finding("prefix-caching-off", "info",
            "Prefix caching is on by default in v0.32.0. Turning it off removes reuse of shared prompt prefixes.",
            "vllm/config/cache.py, enable_prefix_caching default; docs/design/prefix_caching.md"))
    if args.get("prefix-caching-hash-algo") in {"xxhash", "xxhash_cbor"}:
        f.append(Finding("weak-prefix-hash", "warn",
            "xxhash is not cryptographically secure and raises the theoretical risk of hash collisions. "
            "The default is sha256.",
            "docs/design/prefix_caching.md, Note 2"))

    # 8. Speculative decoding.
    if "speculative-config" in args or "speculative-model" in args:
        f.append(Finding("speculative-decoding-load", "info",
            "Speculative decoding targets medium to low QPS, memory-bound workloads. "
            "Measure at peak load before enabling it for everyone.",
            "docs/features/speculative_decoding/README.md"))

    if mml is None:
        f.append(Finding("max-model-len-unset", "info",
            "max-model-len is not set, so it comes from the model configuration. "
            "The concurrency estimate in the log is computed from it.",
            "docs/serving/parallelism_scaling.md, Maximum concurrency log line"))
    return f


def render(findings):
    order = {"error": 0, "warn": 1, "info": 2}
    lines = [f"[{x.severity.upper()}] {x.rule}: {x.message}\n        source: {x.source}"
             for x in sorted(findings, key=lambda x: order[x.severity])]
    return "\n".join(lines) if lines else "no findings"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gpus-per-node", type=int)
    ap.add_argument("--gpu-arch", choices=["volta", "turing", "ampere", "ada", "hopper", "blackwell"])
    ap.add_argument("--kv-cache-tokens", type=int, help="'GPU KV cache size' tokens from the start-up log")
    ap.add_argument("vllm_args", nargs=argparse.REMAINDER)
    ns = ap.parse_args(argv)
    rest = [a for a in ns.vllm_args if a != "--"]
    findings = review(parse_args(rest), ns.gpus_per_node, ns.gpu_arch, ns.kv_cache_tokens)
    print(render(findings))
    return 1 if any(x.severity == "error" for x in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
