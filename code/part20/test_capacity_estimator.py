"""Expected values are the hand calculations in chapter 20.12."""
import pytest
from capacity_estimator import (
    cost_per_m_tokens, decode_tps, goodput_qps, kv_bytes_per_token,
    max_concurrent, per_gpu_capacity, prefill_tps, replicas_needed, weights_gb,
)

QWEN3_BPT = 147_456  # 2 x 36 layers x 8 kv heads x 128 x 2 bytes


def test_weights_by_precision():
    assert weights_gb(8.2, 4) == pytest.approx(32.8)
    assert weights_gb(8.2, 2) == pytest.approx(16.4)
    assert weights_gb(8.2, 1) == pytest.approx(8.2)
    assert weights_gb(8.2, 0.5) == pytest.approx(4.1)


def test_kv_per_token_book_example_llama2_7b():
    assert kv_bytes_per_token(32, 32, 128, 2) == 524_288


def test_kv_per_token_qwen3_and_gqa_saving():
    assert kv_bytes_per_token(36, 8, 128, 2) == QWEN3_BPT
    assert kv_bytes_per_token(36, 32, 128, 2) == 4 * QWEN3_BPT


def test_kv_per_token_qwen25_72b():
    assert kv_bytes_per_token(80, 8, 128, 2) == 327_680


def test_concurrent_requests_h100_qwen3():
    req_gb = 2500 * QWEN3_BPT / 1e9
    assert req_gb == pytest.approx(0.36864)
    assert max_concurrent(80, 1, 0.90, 16.4, 5, req_gb) == 137


def test_concurrent_requests_fp8_weights_and_72b_tp4():
    assert max_concurrent(80, 1, 0.90, 8.2, 5, 0.36864) == 159
    assert max_concurrent(80, 4, 0.90, 145.4, 5, 0.8192) == 149


def test_decode_ceiling_batch_1_and_64():
    assert decode_tps(1, 2500, 16.4, QWEN3_BPT, 3350) == pytest.approx(200, abs=0.5)
    assert decode_tps(64, 2500, 16.4, QWEN3_BPT, 3350) == pytest.approx(5361, abs=1)


def test_decode_batching_helps_then_flattens():
    t = [decode_tps(b, 2500, 16.4, QWEN3_BPT, 3350) for b in (1, 8, 32, 64, 128)]
    assert t == sorted(t) and t[-1] / t[-2] < 1.3


def test_prefill_ceiling():
    assert prefill_tps(989.5, 0.4, 8.2) == pytest.approx(24134, abs=1)


def test_per_gpu_capacity_mixed_prefill_and_decode():
    rate, latency, tpot = per_gpu_capacity(2000, 500, 64, 24134, 5361)
    assert rate == pytest.approx(5.68, abs=0.01)
    assert latency == pytest.approx(11.27, abs=0.02)
    assert tpot * 1000 == pytest.approx(22.4, abs=0.1)


def test_replicas_with_headroom_and_spare():
    assert replicas_needed(40, 5.68, 0.9) == 9
    assert replicas_needed(40, 5.68, 0.9, spare=0) == 8


def test_cost_per_million_output_tokens():
    out_tps = 5.68 * 500
    assert cost_per_m_tokens(4.50, 1, out_tps, 1.0) == pytest.approx(0.44, abs=0.005)
    assert cost_per_m_tokens(4.50, 1, out_tps, 0.5) == pytest.approx(0.88, abs=0.01)


def test_goodput():
    assert goodput_qps(40, 0.95) == pytest.approx(38)
