import pytest

from c02_queue_math import (ClusterQueue, KaiQueue, admit, blast_radius, can_admit, kai_fair_share,
                            max_parallel_drain, partial_placement, reclaimable)


def tree(ds_req, rs_req, parent_quota=12):
    return [KaiQueue("ml", quota=parent_quota, children=[
        KaiQueue("ds", quota=8, request=ds_req), KaiQueue("rs", quota=4, request=rs_req)])]


def test_idle_sibling_quota_is_lent_as_surplus():
    fs = kai_fair_share(12, tree(16, 0))
    assert fs["ds"] == 12 and fs["rs"] == 0


def test_contention_falls_back_to_quota():
    fs = kai_fair_share(12, tree(16, 16))
    assert fs["ds"] == 8 and fs["rs"] == 4


def test_quota_is_capped_by_request():
    fs = kai_fair_share(12, tree(3, 0))
    assert fs["ds"] == 3


def test_surplus_split_by_weight():
    qs = [KaiQueue("a", quota=0, request=10, weight=2), KaiQueue("b", quota=0, request=10, weight=1)]
    fs = kai_fair_share(9, qs)
    assert fs["a"] == pytest.approx(6) and fs["b"] == pytest.approx(3)


def test_priority_overrides_weight():
    # KAI docs: priority 2 weight 1 gets surplus before priority 1 weight 100.
    qs = [KaiQueue("hi", quota=0, request=10, weight=1, priority=2),
          KaiQueue("lo", quota=0, request=10, weight=100, priority=1)]
    fs = kai_fair_share(6, qs)
    assert fs["hi"] == 6 and fs["lo"] == 0


def test_limit_caps_share_and_total_never_exceeded():
    qs = [KaiQueue("a", quota=2, request=10, limit=4), KaiQueue("b", quota=2, request=10)]
    fs = kai_fair_share(10, qs)
    assert fs["a"] == 4 and fs["b"] == 6
    assert sum(fs.values()) <= 10 + 1e-9


def test_unused_pool_is_not_invented():
    fs = kai_fair_share(16, tree(2, 1))
    assert fs["ds"] == 2 and fs["rs"] == 1


def co(train=0, serve=0, **kw):
    return {"t": ClusterQueue("t", 12, used=train), "s": ClusterQueue("s", 4, used=serve, **kw)}


def test_gang_borrows_idle_serving_quota():
    c = co()
    assert admit(c, "t", 16) and c["t"].borrowed() == 4


def test_cannot_borrow_what_is_in_use():
    assert not can_admit(co(serve=4), "t", 16)


def test_lending_limit_zero_blocks_borrowing():
    assert not can_admit(co(lending_limit=0), "t", 13)
    assert can_admit(co(lending_limit=0), "t", 12)


def test_borrowing_limit_blocks_excess():
    c = {"t": ClusterQueue("t", 12, borrowing_limit=2), "s": ClusterQueue("s", 4)}
    assert can_admit(c, "t", 14) and not can_admit(c, "t", 15)


def test_serving_reclaims_borrowed_gpus_but_not_beyond_nominal():
    c = co(train=16)
    assert reclaimable(c, "s", 4) == 4
    assert reclaimable(c, "s", 6) == 4     # entitled only to its nominal quota


def test_nothing_to_reclaim_when_no_one_borrows():
    assert reclaimable(co(train=12), "s", 4) == 0


@pytest.mark.parametrize("n,pct,gpus", [(35, 58.33, 280), (3, 5.0, 24)])
def test_blast_radius_60_nodes(n, pct, gpus):
    r = blast_radius(n, 8, 60)
    assert r["percent"] == pytest.approx(pct, abs=0.01) and r["gpus_unavailable"] == gpus


def test_blast_radius_24_of_120():
    r = blast_radius(24, 8, 120)
    assert r["gpus_unavailable"] == 192 and r["fleet_gpus"] == 960 and r["percent"] == 20


def test_blast_radius_rejects_bad_input():
    with pytest.raises(ValueError):
        blast_radius(61, 8, 60)


def test_drain_ceiling_two_node_pool():
    assert max_parallel_drain(2, 8, 4) == 1
    assert max_parallel_drain(2, 8, 9) == 0


def test_drain_rejects_oversized_protection():
    with pytest.raises(ValueError):
        max_parallel_drain(2, 8, 17)


def test_default_scheduler_deadlocks_two_big_jobs():
    r = partial_placement(12, [8, 8], gang=False)
    assert r["deadlock"] and r["held"] == [6, 6] and r["stranded_nodes"] == 12


def test_gang_runs_one_job_instead():
    r = partial_placement(12, [8, 8], gang=True)
    assert r["running_jobs"] == [0] and not r["deadlock"] and r["stranded_nodes"] == 0


def test_two_node_job_on_one_free_node():
    assert partial_placement(1, [2], gang=False)["stranded_nodes"] == 1
    assert partial_placement(1, [2], gang=True)["stranded_nodes"] == 0


# ---- the YAML files and the arithmetic must agree
import pathlib
import yaml

HERE = pathlib.Path(__file__).parent


def _docs(name):
    return [d for d in yaml.safe_load_all((HERE / name).read_text()) if d]


def test_kueue_quotas_equal_the_pool():
    cqs = [d for d in _docs("c02_kueue_queues.yaml") if d["kind"] == "ClusterQueue"]
    nominal = {d["metadata"]["name"]: d["spec"]["resourceGroups"][0]["flavors"][0]["resources"][0]["nominalQuota"]
               for d in cqs}
    assert nominal == {"cq-training": 12, "cq-serving": 4}
    assert sum(nominal.values()) == 2 * 8            # two a3-highgpu-8g nodes
    assert len({d["spec"]["cohortName"] for d in cqs}) == 1


def test_kai_children_sum_to_parent_quota():
    qs = {d["metadata"]["name"]: d["spec"] for d in _docs("c02_kai_queues.yaml")}
    parent = qs["ml-platform"]["resources"]["gpu"]["quota"]
    kids = sum(s["resources"]["gpu"]["quota"] for s in qs.values() if s.get("parentQueue") == "ml-platform")
    assert parent == kids == 12 == 12   # equals cq-training nominal quota


def test_gang_job_fits_the_pool_only_by_borrowing():
    job = _docs("c02_pytorchjob.yaml")[0]["spec"]["pytorchReplicaSpecs"]
    gpus = sum(r["replicas"] * r["template"]["spec"]["containers"][0]["resources"]["limits"]["nvidia.com/gpu"]
               for r in job.values())
    assert gpus == 16
    c = {"t": ClusterQueue("t", 12), "s": ClusterQueue("s", 4)}
    assert can_admit(c, "t", gpus) and c["t"].nominal < gpus


def test_training_priority_is_preemptible_in_kai():
    pcs = {d["metadata"]["name"]: d["value"] for d in _docs("c02_priority_classes.yaml")}
    assert pcs["training-standard"] < 100 <= pcs["inference-critical"]


def test_serving_group_matches_serving_quota():
    lws = _docs("c02_lws.yaml")[0]["spec"]["leaderWorkerTemplate"]
    per_pod = int(lws["leaderTemplate"]["spec"]["containers"][0]["resources"]["limits"]["nvidia.com/gpu"])
    assert per_pod * lws["size"] == 4
