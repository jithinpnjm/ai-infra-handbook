"""Tests for the MIG profile table and partition planner (Chapter 19.8)."""
import json

import pytest

import c08_mig_planner as m

H100 = "H100 80GB (PCIe and SXM5)"
A100_40 = "A100-SXM4-40GB"
B200 = "B200"


# ------------------------------------------------------------ profile table


def test_table_has_every_row_of_the_guide():
    data = m.load_data()
    counts = {t["product"]: len(t["rows"]) for t in data["tables"]}
    # row counts per table as printed in the guide (checked by eye against the page)
    assert counts == {
        "GB300 (DGX Station)": 7,
        "B300": 7,
        "GB200": 7,
        "B200": 7,
        "RTX PRO 6000 Blackwell (Workstation, Max-Q Workstation and Server Edition)": 11,
        "RTX PRO 5000 Blackwell": 7,
        "RTX PRO 4500 Blackwell": 6,
        "Thor iGPU (GB10B)": 7,
        "H100 80GB (PCIe and SXM5)": 7,
        "H100 94GB (PCIe and SXM5)": 7,
        "H100 96GB (H100 on GH200)": 7,
        "H200 141GB": 7,
        "A100-SXM4-40GB": 7,
        "A30 24GB": 5,
    }
    assert sum(counts.values()) == 99


def test_source_metadata_is_present():
    src = m.load_data()["source"]
    assert src["page_last_updated"] == "2026-11-04"
    assert src["fetched"] == "2026-11-10"
    assert src["url"].endswith("supported-mig-profiles.html")


@pytest.mark.parametrize(
    "product,expected",
    [
        (H100, {"1g.10gb": 7, "1g.10gb+me": 1, "1g.20gb": 4, "2g.20gb": 3, "3g.40gb": 2, "4g.40gb": 1, "7g.80gb": 1}),
        (A100_40, {"1g.5gb": 7, "1g.5gb+me": 1, "1g.10gb": 4, "2g.10gb": 3, "3g.20gb": 2, "4g.20gb": 1, "7g.40gb": 1}),
        ("H200 141GB", {"1g.18gb": 7, "1g.18gb+me": 1, "1g.35gb": 4, "2g.35gb": 3, "3g.71gb": 2, "4g.71gb": 1, "7g.141gb": 1}),
        (B200, {"1g.23gb": 7, "1g.23gb+me": 1, "1g.45gb": 4, "2g.45gb": 3, "3g.90gb": 2, "4g.90gb": 1, "7g.180gb": 1}),
    ],
)
def test_instance_counts_match_the_guide(product, expected):
    got = {p.name: p.max_instances for p in m.profiles_for(product).values()}
    assert got == expected


def test_a100_lgip_sm_counts_are_14_per_slice():
    rows = m.load_data()["a100_40gb_lgip"]["rows"]
    for name, _pid, _n, _gib, _p2p, sm, _ce in rows:
        slices = int(name[0])
        assert sm == 14 * slices, name


# ------------------------------------------------------------ placement model


def test_placements_come_from_the_lgipp_listing():
    prof = m.profiles_for(A100_40)
    assert prof["1g.5gb"].starts == (0, 1, 2, 3, 4, 5, 6)
    assert prof["1g.10gb"].starts == (0, 2, 4, 6)
    assert prof["2g.10gb"].starts == (0, 2, 4)
    assert prof["3g.20gb"].starts == (0, 4)
    assert prof["4g.20gb"].starts == (0,)
    assert prof["7g.40gb"].starts == (0,)


def test_guide_example_geometries_are_feasible():
    p = m.profiles_for(A100_40)
    # 4-2-1 (example 1), 3-2-1-1 (example 2), 2-1-1-1-1-1 (example 3), 3g x2 (create example)
    assert m.feasible([p["4g.20gb"], p["2g.10gb"], p["1g.5gb"]])
    assert m.feasible([p["3g.20gb"], p["2g.10gb"], p["1g.5gb"], p["1g.5gb"]])
    assert m.feasible([p["2g.10gb"]] + [p["1g.5gb"]] * 5)
    assert m.feasible([p["3g.20gb"]] * 2)


def test_placement_start_positions_match_guide_example_two():
    p = m.profiles_for(A100_40)
    placed = dict((pr.name, s) for pr, s in m.feasible([p["3g.20gb"], p["2g.10gb"], p["1g.5gb"], p["1g.5gb"]]))
    # the guide shows 3g.20gb at 4:4 and 2g.10gb at 2:2 for this geometry
    assert placed["3g.20gb"] == 4
    assert placed["2g.10gb"] in (0, 2)


@pytest.mark.parametrize(
    "names",
    [
        ["4g.40gb", "4g.40gb"],  # only one 4g placement
        ["3g.40gb"] * 3,  # only two 3g placements
        ["7g.80gb", "1g.10gb"],  # the whole GPU
        ["1g.10gb"] * 8,  # eight 1g needs eight SM slices
        ["1g.20gb"] * 4 + ["1g.10gb"],  # memory is full after four 1g.20gb
        ["3g.40gb", "3g.40gb", "1g.10gb"],  # 3g+3g uses all 8 memory slices
        ["4g.40gb", "4g.40gb", "1g.10gb"],
        ["1g.10gb+me", "1g.10gb+me"],  # only one +me per GPU
    ],
)
def test_impossible_geometries_are_rejected(names):
    p = m.profiles_for(H100)
    assert m.feasible([p[n] for n in names]) is None


@pytest.mark.parametrize(
    "names",
    [
        ["1g.10gb"] * 7,
        ["2g.20gb"] * 3 + ["1g.10gb"],
        ["4g.40gb", "3g.40gb"],
        ["3g.40gb", "3g.40gb"],
        ["1g.20gb"] * 4,
        ["4g.40gb", "2g.20gb", "1g.10gb"],
        ["3g.40gb", "1g.10gb", "1g.10gb", "1g.10gb", "1g.10gb"],
    ],
)
def test_valid_geometries_are_accepted(names):
    p = m.profiles_for(H100)
    assert m.feasible([p[n] for n in names]) is not None


def test_all_nineteen_figure_configs_are_feasible_and_cover_the_model():
    data = m.load_data()
    cfgs = data["seven_slice_valid_configs_figure"]["configs"]
    assert len(cfgs) == 19
    prof = m.profiles_for(H100)
    by_sm = {1: prof["1g.10gb"], 2: prof["2g.20gb"], 3: prof["3g.40gb"], 4: prof["4g.40gb"], 7: prof["7g.80gb"]}
    figure = m.figure_multisets(data)
    for ms in figure:
        assert m.feasible([by_sm[s] for s in ms]) is not None, ms
    maximal = m.maximal_multisets(H100, data)
    # every maximal mix the model finds is drawn in the figure
    assert maximal <= figure
    # every drawn mix is either maximal or sits inside a maximal one
    for ms in figure - maximal:
        assert any(sum(1 for _ in ms) < len(mx) and _is_sub(ms, mx) for mx in maximal), ms


def _is_sub(small, big):
    pool = list(big)
    for x in small:
        if x not in pool:
            return False
        pool.remove(x)
    return True


def test_creation_order_puts_the_3g_profile_first():
    p = m.profiles_for(A100_40)
    order = m.creation_order([p["1g.5gb"], p["1g.5gb"], p["2g.10gb"], p["3g.20gb"]])
    assert order[0] == "3g.20gb"


def test_unsupported_gpu_is_refused():
    with pytest.raises(m.PlannerError, match="seven-slice"):
        m.profiles_for("A30 24GB")
    with pytest.raises(m.PlannerError, match="unknown GPU"):
        m.profiles_for("V100")


# ------------------------------------------------------------ planner


def test_plan_packs_a_tenant_mix_and_reports_the_shortfall():
    demand = [
        ("search-embeddings", "1g.10gb", 10),
        ("chat-llm", "3g.40gb", 4),
        ("notebooks", "2g.20gb", 6),
        ("finetune", "4g.40gb", 2),
        ("batch-eval", "7g.80gb", 1),
    ]
    assert m.min_gpus(H100, demand) == 8
    ok = m.plan(H100, 8, demand)
    assert ok.unplaced == []
    placed = ok.placed_by_tenant()
    assert placed["chat-llm"] == {"3g.40gb": 4}
    assert sum(placed["search-embeddings"].values()) == 10
    short = m.plan(H100, 7, demand)
    assert short.unplaced == [("search-embeddings", "1g.10gb", 1)]


def test_lower_bounds_are_below_the_packed_result():
    """SM slices alone say 7 GPUs; the packer needs 8. The gap is packing loss."""
    demand = [("a", "1g.10gb", 10), ("b", "3g.40gb", 4), ("c", "2g.20gb", 6), ("d", "4g.40gb", 2), ("e", "7g.80gb", 1)]
    prof = m.profiles_for(H100)
    sm = sum(prof[p].sm_slices * n for _, p, n in demand)
    assert sm == 49 and -(-sm // 7) == 7
    assert m.min_gpus(H100, demand) == 8


def test_every_plan_is_valid_on_every_gpu():
    demand = [("a", "1g.10gb", 9), ("b", "2g.20gb", 4), ("c", "3g.40gb", 3), ("d", "1g.20gb", 2)]
    p = m.plan(H100, 6, demand)
    for g in p.gpus:
        assert m.feasible(g.profiles()) is not None
        assert g.used_sm_slices <= 7 and g.used_mem_slices <= 8


def test_three_3g_do_not_fit_one_gpu_but_fit_two():
    assert m.plan(H100, 1, [("t", "3g.40gb", 3)]).unplaced == [("t", "3g.40gb", 1)]
    two = m.plan(H100, 2, [("t", "3g.40gb", 3)])
    assert two.unplaced == []


def test_fragmentation_stats_for_seven_small_slices():
    p = m.plan(H100, 1, [("t", "1g.10gb", 7)])
    s = p.stats()[0]
    assert s["used_sm_slices"] == 7 and s["free_sm_slices"] == 0
    assert s["free_mem_slices"] == 1  # 70 GB of 80 GB used
    assert s["stranded_mem_slices"] == 1


def test_two_3g_leave_one_sm_slice_stranded():
    p = m.plan(H100, 1, [("t", "3g.40gb", 2)])
    s = p.stats()[0]
    assert s["free_mem_slices"] == 0
    assert s["free_sm_slices"] == 1


def test_repacking_hides_fragmentation_that_a_live_gpu_cannot_avoid():
    prof = m.profiles_for(H100)
    one_g = prof["1g.10gb"]
    # two 1g.10gb instances happen to sit at starts 0 and 4, as after earlier churn
    live = [(one_g, 0), (one_g, 4)]
    stats = m.fixed_fragmentation(live, prof)
    assert stats["free_mem_slices"] == 6
    # 4g.40gb needs start 0 and 3g.40gb needs 0 or 4: all blocked, though 6 slices are free
    assert m.place_into_fixed(live, prof["4g.40gb"]) is None
    assert m.place_into_fixed(live, prof["3g.40gb"]) is None
    assert stats["largest_placeable_mem_slices"] == 2
    assert stats["fragmentation"] == 0.667
    # a planner that may move instances finds room for the 3g.40gb
    assert m.feasible([one_g, one_g, prof["3g.40gb"]]) is not None


def test_fixed_placement_respects_instance_limits():
    prof = m.profiles_for(H100)
    live = [(prof["4g.40gb"], 0)]
    assert m.place_into_fixed(live, prof["4g.40gb"]) is None  # only one 4g per GPU
    assert m.place_into_fixed(live, prof["3g.40gb"]) == 4


def test_three_2g_leave_room_for_one_more_small_instance():
    p = m.plan(H100, 1, [("t", "2g.20gb", 3)])
    s = p.stats()[0]
    assert s["free_mem_slices"] == 2
    assert s["largest_free_mem_slices"] == 2  # a 1g.20gb still starts at slice 6
    assert s["fragmentation"] == 0.0


def test_unknown_profile_and_negative_counts_are_errors():
    with pytest.raises(m.PlannerError, match="not a profile"):
        m.plan(H100, 1, [("t", "1g.5gb", 1)])  # that is an A100-40GB name
    with pytest.raises(m.PlannerError):
        m.plan(H100, 1, [("t", "1g.10gb", -1)])
    with pytest.raises(m.PlannerError):
        m.plan(H100, -1, [])


def test_demand_that_cannot_fit_anywhere_raises_from_min_gpus():
    with pytest.raises(m.PlannerError):
        m.min_gpus(H100, [("t", "7g.80gb", 5)], limit=4)


def test_other_seven_slice_gpus_use_their_own_names():
    p = m.plan(B200, 1, [("t", "4g.90gb", 1), ("u", "3g.90gb", 1)])
    assert p.unplaced == []
    with pytest.raises(m.PlannerError):
        m.plan(B200, 1, [("t", "1g.10gb", 1)])


def test_profile_json_round_trips():
    data = m.load_data()
    assert json.loads(json.dumps(data)) == data
