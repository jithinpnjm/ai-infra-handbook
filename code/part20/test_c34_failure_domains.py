import pytest
from c34_failure_domains import (Layout, blast_radius, nodes_lost_on_single_feed_failure,
    psu_node_survives, rail_bandwidth_fraction, surviving_replicas,
    spares_needed, plan_drain, _place)

LAY = Layout(sites=1, halls_per_site=2, rows_per_hall=4, racks_per_row=6,
             nodes_per_rack=8, gpus_per_node=8)


def test_counts():
    assert LAY.racks == 48
    assert LAY.total_nodes == 384
    assert LAY.total_gpus == 3072


def test_blast_radius_levels():
    assert blast_radius(LAY, "node").nodes == 1
    assert blast_radius(LAY, "rack").nodes == 8
    assert blast_radius(LAY, "row").nodes == 48
    hall = blast_radius(LAY, "hall")
    assert hall.nodes == 192 and hall.gpus == 1536
    assert hall.fraction == pytest.approx(0.5)


def test_domain_of_and_nodes_in():
    assert LAY.domain_of(0, "rack") == 0
    assert LAY.domain_of(8, "rack") == 1
    assert LAY.domain_of(383, "hall") == 1
    assert LAY.nodes_in("rack", 1) == list(range(8, 16))
    with pytest.raises(ValueError):
        LAY.domain_of(384, "rack")
    with pytest.raises(ValueError):
        LAY.nodes_in("rack", 48)
    with pytest.raises(ValueError):
        blast_radius(LAY, "planet")


def test_bad_layout():
    with pytest.raises(ValueError):
        Layout(racks_per_row=0)


def test_power_models():
    assert nodes_lost_on_single_feed_failure("interleaved_two_feed", 4) == 4
    assert nodes_lost_on_single_feed_failure("non_interleaved_two_feed", 4) == 2
    assert nodes_lost_on_single_feed_failure("non_interleaved_two_feed", 3) == 2
    assert nodes_lost_on_single_feed_failure("six_discrete_sources", 4) == 0
    with pytest.raises(ValueError):
        nodes_lost_on_single_feed_failure("other", 4)


def test_psu_rule_five_of_six():
    assert psu_node_survives(6) and psu_node_survives(5)
    assert not psu_node_survives(4)
    assert not psu_node_survives(3)  # interleaved, one feed lost


def test_rail_fraction():
    assert rail_bandwidth_fraction(4, 1) == 0.75
    assert rail_bandwidth_fraction(8, 0) == 1.0
    with pytest.raises(ValueError):
        rail_bandwidth_fraction(4, 5)


def test_pack_puts_replicas_in_few_racks():
    placed = _place(LAY, 16, 1, "pack")
    racks = {LAY.domain_of(n[0], "rack") for n in placed}
    assert racks == {0, 1}


def test_spread_uses_many_halls():
    placed = _place(LAY, 8, 1, "spread")
    halls = {LAY.domain_of(n[0], "hall") for n in placed}
    assert halls == {0, 1}
    rows = {LAY.domain_of(n[0], "row") for n in placed}
    assert len(rows) >= 4


def test_replica_stays_inside_one_rack():
    placed = _place(LAY, 10, 4, "spread")
    for nodes in placed:
        assert len({LAY.domain_of(n, "rack") for n in nodes}) == 1
    assert _place(LAY, 1, 9, "pack") is None  # does not fit a rack
    assert _place(LAY, 97, 4, "pack") is None  # more than capacity


def test_surviving_pack_vs_spread():
    pack = surviving_replicas(LAY, 40, 1, "rack", "pack")
    spread = surviving_replicas(LAY, 40, 1, "rack", "spread")
    assert pack == 32 and spread == 39
    assert surviving_replicas(LAY, 40, 1, "hall", "spread") == 20
    assert surviving_replicas(LAY, 40, 1, "hall", "pack") == 0


def test_spares_numbers():
    assert spares_needed(LAY, 40, 1, "rack", "pack") == 8
    assert spares_needed(LAY, 40, 1, "rack", "spread") == 1
    assert spares_needed(LAY, 40, 1, "hall", "spread") == 40
    assert spares_needed(LAY, 40, 1, "node", "spread") == 1


def test_spares_none_when_layout_too_small():
    assert spares_needed(LAY, 300, 1, "hall", "spread") is None
    assert spares_needed(LAY, 5, 2, "rack", "pack") == 4


def test_multi_node_replica_loses_whole_replica():
    # 4-node replicas, 2 per rack, one rack fault kills 2 replicas when packed
    assert surviving_replicas(LAY, 10, 4, "rack", "pack") == 8
    assert surviving_replicas(LAY, 10, 4, "node", "pack") == 9


def test_plan_drain_batches():
    batches = plan_drain(LAY, "rack", 3, 0.01)  # floor(3.84) = 3 nodes out
    assert [len(b) for b in batches] == [3, 3, 2]
    assert sorted(n for b in batches for n in b) == LAY.nodes_in("rack", 3)


def test_plan_drain_least_loaded_first_and_budget():
    load = {24: 9, 25: 1, 26: 5}
    batches = plan_drain(LAY, "rack", 3, 0.01, load=load)
    flat = [n for b in batches for n in b]
    assert flat == [27, 28, 29, 30, 31, 25, 26, 24]
    assert flat[-1] == 24  # busiest last
    assert plan_drain(LAY, "rack", 3, 0.01, already_out=3) is None
