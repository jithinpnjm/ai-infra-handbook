import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from c22_vllm_config_review import main, parse_args, review  # noqa: E402


def rules(cmd, **ctx):
    return {f.rule: f.severity for f in review(parse_args(cmd.split()), **ctx)}


def test_parse_forms():
    a = parse_args("vllm serve m --tensor-parallel-size=4 --max_model_len 8192 --enforce-eager -O0".split())
    assert a["tensor-parallel-size"] == 4 and a["max-model-len"] == 8192
    assert a["enforce-eager"] is True and a["optimization-level"] == 0


def test_parse_list_flag_stops_at_next_flag():
    a = parse_args("--numa-bind --numa-bind-nodes 0 0 1 1 --max-num-seqs 64".split())
    assert a["numa-bind-nodes"] == ["0", "0", "1", "1"] and a["max-num-seqs"] == 64


def test_chunked_prefill_off_budget_below_model_len_is_error():
    r = rules("--no-enable-chunked-prefill --max-num-batched-tokens 2048 --max-model-len 32768")
    assert r["chunked-prefill-budget"] == "error"


def test_chunked_prefill_off_budget_ok():
    r = rules("--no-enable-chunked-prefill --max-num-batched-tokens 32768 --max-model-len 32768")
    assert "chunked-prefill-budget" not in r


def test_util_out_of_range():
    assert rules("--gpu-memory-utilization 1.2")["gpu-util-range"] == "error"
    assert "gpu-util-range" not in rules("--gpu-memory-utilization 0.9")


def test_kv_cache_memory_overrides_util():
    r = rules("--kv-cache-memory 1000 --gpu-memory-utilization 0.9")
    assert r["kv-cache-memory-ignores-util"] == "warn"


def test_world_size_exceeds_gpus():
    r = rules("--tensor-parallel-size 8 --pipeline-parallel-size 2", gpus_per_node=8)
    assert r["world-size-exceeds-gpus"] == "error"


def test_tp_pp_beyond_host_without_nnodes():
    r = rules("--tensor-parallel-size 4 --pipeline-parallel-size 2", gpus_per_node=4)
    assert r["world-size-exceeds-gpus"] == "error"


def test_ray_backend_skips_host_gpu_count():
    r = rules("--tensor-parallel-size 4 --pipeline-parallel-size 2 --distributed-executor-backend ray",
              gpus_per_node=4)
    assert "world-size-exceeds-gpus" not in r


def test_multinode_mp_needs_master_addr():
    r = rules("--tensor-parallel-size 8 --pipeline-parallel-size 2 --nnodes 2", gpus_per_node=8)
    assert r["mp-multinode-needs-master"] == "error"
    ok = rules("--tensor-parallel-size 8 --pipeline-parallel-size 2 --nnodes 2 --master-addr 10.0.0.1",
               gpus_per_node=8)
    assert "mp-multinode-needs-master" not in ok and "world-size-exceeds-gpus" not in ok


def test_tp_across_nodes_warns():
    r = rules("--tensor-parallel-size 16 --nnodes 2 --master-addr x", gpus_per_node=8)
    assert r["tp-crosses-nodes"] == "warn"


def test_numa_nodes_count():
    r = rules("--numa-bind --numa-bind-nodes 0 0 1", gpus_per_node=4)
    assert r["numa-nodes-count"] == "error"
    assert "numa-nodes-count" not in rules("--numa-bind --numa-bind-nodes 0 0 1 1", gpus_per_node=4)


def test_expert_parallel_without_sharding():
    assert rules("--enable-expert-parallel")["ep-without-sharding"] == "warn"
    assert "ep-without-sharding" not in rules("--enable-expert-parallel --tensor-parallel-size 8")


def test_awq_on_volta():
    assert rules("--quantization awq", gpu_arch="volta")["awq-on-volta"] == "error"
    assert "awq-on-volta" not in rules("--quantization awq", gpu_arch="hopper")


def test_fp8_on_ampere_warns():
    assert rules("--quantization fp8", gpu_arch="ampere")["fp8-w8a8-hardware"] == "warn"
    assert "fp8-w8a8-hardware" not in rules("--quantization fp8", gpu_arch="hopper")


def test_seqs_exceed_worst_case_kv():
    r = rules("--max-num-seqs 128 --max-model-len 40960", kv_cache_tokens=72064)
    assert r["seqs-exceed-worst-case-kv"] == "info"
    assert "seqs-exceed-worst-case-kv" not in rules("--max-num-seqs 1 --max-model-len 40960",
                                                    kv_cache_tokens=72064)


def test_eager_and_o0_warn():
    r = rules("--enforce-eager -O0")
    assert r["enforce-eager"] == "warn" and r["opt-level-0"] == "warn"


def test_prefix_hash_and_disable():
    r = rules("--no-enable-prefix-caching --prefix-caching-hash-algo xxhash")
    assert r["prefix-caching-off"] == "info" and r["weak-prefix-hash"] == "warn"


def test_cli_exit_code(capsys):
    assert main(["--gpus-per-node", "8", "--", "vllm", "serve", "m", "--tensor-parallel-size", "16"]) == 1
    assert "world-size-exceeds-gpus" in capsys.readouterr().out
    assert main(["--", "vllm", "serve", "m", "--max-model-len", "8192"]) == 0
