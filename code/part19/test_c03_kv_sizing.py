import pytest

import c03_kv_sizing as k


def test_llama31_8b_kv_bytes_per_token_is_128_kib():
    assert k.kv_bytes_per_token(k.LLAMA31_8B) == 131072


def test_gqa_saves_a_factor_of_four_against_mha_for_this_model():
    p = k.plan(k.LLAMA31_8B, 40, 0.90, 3.0, 1024, 256, 16384, 64)
    assert p["mha_over_gqa"] == 4.0


def test_weights_are_about_15_gib_in_bf16():
    assert round(k.weights_bytes(k.LLAMA31_8B) / k.GIB, 2) == 14.96


def test_default_plan_numbers_quoted_in_chapter():
    p = k.plan(k.LLAMA31_8B, 40, 0.90, 3.0, 1024, 256, 16384, 64)
    assert round(p["kv_budget_gib"], 2) == 18.04
    assert p["capacity_tokens"] == 147_803
    assert p["seqs_at_avg_len"] == 115
    assert p["seqs_at_max_model_len"] == 9
    assert p["typical_batch_fits"] is True
    assert round(p["typical_batch_gib"], 1) == 10.0
    # The failure case: 64 sequences that all reach max_model_len do not fit.
    assert p["worst_case_fits"] is False


def test_more_overhead_shrinks_capacity():
    a = k.plan(k.LLAMA31_8B, 40, 0.90, 3.0, 1024, 256, 16384, 64)["capacity_tokens"]
    b = k.plan(k.LLAMA31_8B, 40, 0.90, 6.0, 1024, 256, 16384, 64)["capacity_tokens"]
    assert b < a


def test_budget_never_negative_capacity():
    # A model that does not fit gives zero capacity, not a negative number.
    assert k.token_capacity(k.kv_budget_bytes(10, 0.9, k.LLAMA31_8B, 3.0), k.LLAMA31_8B) == 0


def test_rejects_bad_inputs():
    with pytest.raises(ValueError):
        k.kv_budget_bytes(40, 1.2, k.LLAMA31_8B, 3.0)
    with pytest.raises(ValueError):
        k.sequences_that_fit(100, 0)
