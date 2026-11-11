"""Tests for the chapter 19.11 design scripts: formulas, book and vendor table rows,
the worked example, and failure cases."""
import copy
import json
import pathlib

import pytest

import c11_choose_scheduler as cs
import c11_design_review as dr
import c11_design_storage as ds
import c11_select_topology as tp
import c11_size_gpu_pool as sz
import c11_worked_example as we

EX = json.loads((pathlib.Path(__file__).parent / "c11_design_example.json").read_text())


# ---- sizing
def test_flops_and_ideal_gpus():
    assert sz.train_flops(70e9, 2e12) == pytest.approx(8.4e23)
    assert sz.ideal_gpus(8.4e23, 2250, 0.4, 30) == pytest.approx(360.08, abs=0.01)


def test_book_mfu_round_trip():
    # Distributed AI Systems ch. 2: 860 TFLOP in 2.0 s on 989 TFLOPS peak is MFU about 43 percent.
    gpus = sz.ideal_gpus(860e12, 989, 430 / 989, 2.0 / 86400)
    assert gpus == pytest.approx(1.0)


def test_pool_fixed_point_and_spares():
    ckpt_s, pool, _ = we.build()
    assert ckpt_s == pytest.approx(21.78, abs=0.01)
    assert pool["training_nodes"] == 46 and pool["spare_nodes"] == 2
    assert pool["total_gpus"] == 384
    assert pool["inflation"] == pytest.approx(1.0107, abs=1e-4)


def test_inflation_never_below_one_and_young_minimises():
    mtbf, c, r = 400000.0, 20.0, 600.0
    y = sz.young_interval_s(c, mtbf)
    assert sz.inflation(c, y, r, mtbf) < sz.inflation(c, y / 3, r, mtbf)
    assert sz.inflation(c, y, r, mtbf) < sz.inflation(c, y * 3, r, mtbf)


def test_state_floor():
    assert sz.min_gpus_for_state(70e9, 16, 192) == 8


@pytest.mark.parametrize("args", [(0, 1), (1, 0)])
def test_flops_rejects_nonpositive(args):
    with pytest.raises(ValueError):
        sz.train_flops(*args)


def test_bad_mfu_rejected():
    with pytest.raises(ValueError):
        sz.ideal_gpus(1e20, 1000, 1.5, 10)


# ---- topology: rows printed in the book and the vendor documents
@pytest.mark.parametrize("gpus,leaf,spine", [(256, 8, 4), (512, 16, 8)])
def test_book_two_tier_rows(gpus, leaf, spine):
    r = tp.fat_tree(gpus, 64)
    assert (r["leaf"], r["spine"]) == (leaf, spine)


def test_2048_is_the_two_tier_limit_and_2049_needs_three_tiers():
    # Book Fig. 3-9: 2048 GPUs, 64 leaf switches of 64 x 400G. Its five-stage 2048 row is a
    # two-pod build; plain counting uses two tiers up to the limit.
    r = tp.fat_tree(2048, 64)
    assert (r["tiers"], r["leaf"], r["spine"]) == (2, 64, 32)
    r3 = tp.fat_tree(2049, 64)
    assert r3["tiers"] == 3 and r3["super_spine"] > 0


def test_book_4096_two_to_one_row():
    r = tp.fat_tree(4096, 64, top_oversub=2)
    assert (r["leaf"], r["spine"], r["super_spine"]) == (128, 128, 32)


@pytest.mark.parametrize("sus,nodes,leaf,spine", [(1, 31, 8, 4), (2, 63, 16, 8), (4, 127, 32, 16)])
def test_b200_superpod_table(sus, nodes, leaf, spine):
    # DGX B200 SuperPOD cabling table: GPUs are nodes x 8 but the fabric is built for full SUs.
    r = tp.fat_tree(sus * 32 * 8, 64)
    assert (r["leaf"], r["spine"]) == (leaf, spine)
    assert r["leaf_spine_cables"] == {1: 256, 2: 512, 4: 1024}[sus]


def test_b200_three_su_formula_disagrees_with_table():
    # Table says 16 spines for 3 SUs. Plain counting gives 12. Recorded, not hidden.
    assert tp.fat_tree(3 * 256, 64)["spine"] == 12


@pytest.mark.parametrize("sus,leaf,spine", [(2, 16, 8)])
def test_gb300_table_two_su(sus, leaf, spine):
    r = tp.fat_tree(sus * 576, 144)
    assert (r["leaf"], r["spine"]) == (leaf, spine)


def test_gb300_larger_rows_formula_is_below_table():
    # Table 3 lists 18, 36, 72 spines for 4, 8, 16 SUs; plain counting gives 16, 32, 64.
    got = [tp.fat_tree(n * 576, 144)["spine"] for n in (4, 8, 16)]
    assert got == [16, 32, 64]


def test_worked_example_fabric():
    r = tp.fat_tree(384, 64)
    assert (r["leaf"], r["spine"], r["switches"]) == (12, 6, 18)


def test_two_tier_limit_and_oversub():
    assert tp.max_two_tier_endpoints(64) == 2048
    r = tp.fat_tree(1536, 64, leaf_oversub=3)
    assert r["leaf"] == 32 and r["spine"] == 8 and r["leaf_oversub"] == 3


def test_ratio_and_domains():
    assert tp.scale_up_to_out_ratio(1800, 400) == pytest.approx(36)
    assert tp.nvlink_domains(384, 72) == 6


@pytest.mark.parametrize("kw", [dict(endpoints=0, radix=64), dict(endpoints=8, radix=63),
                                dict(endpoints=8, radix=64, leaf_oversub=0),
                                dict(endpoints=8, radix=10, leaf_oversub=3)])
def test_topology_rejects_bad_input(kw):
    with pytest.raises(ValueError):
        tp.fat_tree(**kw)


def test_too_big_for_three_tiers():
    with pytest.raises(ValueError):
        tp.fat_tree(70000, 64)


def test_three_tier_rejects_leaf_oversub():
    with pytest.raises(ValueError):
        tp.fat_tree(4096, 64, leaf_oversub=3)


# ---- storage
def test_dataset_read_is_tiny_for_text():
    mb = ds.dataset_read_gbs(2e12 / (30 * 86400), 4) * 1000
    assert mb == pytest.approx(3.09, abs=0.01)


def test_checkpoint_size_and_time():
    assert ds.checkpoint_bytes(70e9) == 980e9
    assert ds.checkpoint_write_s(70e9, 45) == pytest.approx(21.78, abs=0.01)
    assert ds.checkpoint_write_s(70e9, 10) == pytest.approx(98.0)


def test_stall_sync_vs_async():
    assert ds.stall_fraction(98, 1800) == pytest.approx(0.0544, abs=1e-4)
    assert ds.stall_fraction(98, 1800, async_snapshot_s=5) == pytest.approx(5 / 1800)


def test_min_write_and_retention():
    assert ds.min_write_gbs(70e9, 1800, 0.03) == pytest.approx(18.15, abs=0.01)
    assert ds.retained_tb(70e9, 5) == pytest.approx(4.9)


def test_guideline_scales_by_units():
    assert ds.meets_guideline(90, 45, "standard", 1)
    assert not ds.meets_guideline(90, 45, "standard", 2)
    assert not ds.meets_guideline(280, 100, "enhanced", 1)


@pytest.mark.parametrize("fn,args", [(ds.checkpoint_write_s, (1e9, 0)), (ds.min_write_gbs, (1e9, 100, 1.5)),
                                     (ds.dataset_read_gbs, (0, 4)), (ds.stall_fraction, (1, 0)),
                                     (ds.meets_guideline, (1, 1, "gold"))])
def test_storage_failure_cases(fn, args):
    with pytest.raises(ValueError):
        fn(*args)


# ---- scheduler
def test_default_profile_picks_slurm():
    d = cs.choose_scheduler(EX["scheduler_profile"])
    assert d["choice"] == "Slurm" and (d["slurm_score"], d["k8s_score"]) == (4, 1)
    assert any("batch training" in r for r in d["reasons"])


def test_shared_estate_picks_kubernetes_kai():
    d = cs.choose_scheduler(EX["scheduler_profile_alt"])
    assert d["choice"] == "Kubernetes with KAI"


def test_kueue_without_fractions():
    p = dict(EX["scheduler_profile_alt"], needs_gpu_fractions=False)
    assert cs.choose_scheduler(p)["choice"] == "Kubernetes with Kueue"


def test_hybrid_when_both_strong():
    p = dict(EX["scheduler_profile"], shared_with_services=True, team_k8s_skill=False)
    assert cs.choose_scheduler(p)["choice"].startswith("Slurm on Kubernetes")


def test_tie_is_reported_not_guessed():
    p = {k: False for k in cs.REQUIRED}
    p["tenants"] = 1
    assert cs.choose_scheduler(p)["choice"].startswith("undecided")


def test_scheduler_missing_answer_and_bad_tenants():
    p = dict(EX["scheduler_profile"])
    del p["tenants"]
    with pytest.raises(ValueError):
        cs.choose_scheduler(p)
    with pytest.raises(ValueError):
        cs.choose_scheduler(dict(EX["scheduler_profile"], tenants=0))


# ---- review
def test_example_design_passes():
    res = dr.run_review(EX["design"])
    assert dr.passed(res) and len(res) == 11


def _status(res, name):
    return [s for n, s, _ in res if n == name][0]


def test_review_catches_each_planted_fault():
    base = EX["design"]
    cases = {
        "compute": ("pool", {"gpus": 300, "peak_tflops": 2250, "mfu": 0.4}),
        "memory": ("memory", {"state_gb_per_gpu": 170, "hbm_gb": 192}),
        "fabric": ("fabric", {"leaf_oversub": 4}),
        "power": ("rack", {"nodes_per_rack": 4, "node_kw": 14.3, "rack_limit_kw": 28.6}),
        "spares": ("spares", {"have": 0, "nodes": 46, "node_mtbf_h": 6250, "repair_h": 24}),
        "checkpoint": ("storage", {"ckpt_write_s": 98, "ckpt_interval_s": 1800}),
        "scheduler": ("scheduler", {"choice": "Slurm", "reasons": []}),
        "observability": ("observability", ["step_time"]),
        "failure_plan": ("failure_plan", {"health_check": "x"}),
    }
    for name, (key, val) in cases.items():
        d = copy.deepcopy(base)
        d[key] = val
        res = dr.run_review(d)
        assert _status(res, name) in ("FAIL", "WARN"), name
        assert not dr.passed(res)


def test_quota_over_pool_fails():
    d = copy.deepcopy(EX["design"])
    d["tenants"]["research"] = 100
    assert _status(dr.run_review(d), "quota") == "FAIL"


def test_missing_sections_fail_not_crash():
    res = dr.run_review({})
    assert all(s == "FAIL" for _, s, _ in res)


def test_run_cost_and_bad_input():
    assert sz.run_cost(368, 30, 8.5) == pytest.approx(2252160)
    with pytest.raises(ValueError):
        sz.run_cost(10, 0, 1)


def test_saved_output_matches_live_output(capsys):
    we.main()
    live = capsys.readouterr().out
    saved = (pathlib.Path(__file__).parent / "c11_worked_example_output.txt").read_text()
    assert live == saved
