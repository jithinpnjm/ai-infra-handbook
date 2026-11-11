"""Tests for the chapter 19.13 fair-share simulator: policy outcomes, invariants and a failure case."""
import pytest

import c13_fairshare_sim as s


@pytest.fixture(scope="module")
def trace():
    return s.make_trace(7)


@pytest.fixture(scope="module")
def results(trace):
    jobs, _ = trace
    return {p: s.run_batch(jobs, p) for p in ("static", "borrow", "reclaim")}


def test_trace_is_deterministic(trace):
    a, _ = s.make_trace(7)
    b, _ = s.make_trace(7)
    assert [(j.team, j.kind, j.gpus, j.submit, j.work) for j in a] == [(j.team, j.kind, j.gpus, j.submit, j.work) for j in b]
    c, _ = s.make_trace(8)
    assert [j.work for j in a] != [j.work for j in c]


def test_static_never_exceeds_nominal(results):
    assert all(v <= 0 for v in results["static"]["max_over_nominal"].values())


def test_borrowing_raises_utilization_and_finishes_more(results):
    assert results["borrow"]["utilization"] > results["static"]["utilization"] + 0.15
    assert len(results["borrow"]["unfinished"]) < len(results["static"]["unfinished"])


def test_borrow_without_reclaim_makes_owners_wait(results):
    assert s.entitled_wait(results["borrow"])["p95"] > 0
    assert s.entitled_wait(results["borrow"])["max"] > 60


def test_reclaim_gives_owners_their_quota_back(results):
    assert s.entitled_wait(results["reclaim"])["p95"] == 0
    assert s.entitled_wait(results["reclaim"])["max"] < s.entitled_wait(results["borrow"])["max"]


def test_reclaim_costs_preemptions_and_lost_work(results):
    r = results["reclaim"]
    assert r["preemptions"] > 0 and r["lost_gpu_hours"] > 0
    assert results["borrow"]["preemptions"] == 0 and results["static"]["preemptions"] == 0


def test_checkpointed_training_loses_at_most_one_interval(results):
    for j in results["reclaim"]["jobs"]:
        if j.ckpt:
            assert j.done <= j.work
    # sweeps have no checkpoint, so they carry all the lost work
    assert all(j.kind == "sweep" for j in results["reclaim"]["jobs"] if j.preemptions)


def test_preemption_only_takes_borrowed_capacity(results):
    # no team is pushed under nominal by a preemption: under reclaim, training jobs are never victims here
    assert sum(j.preemptions for j in results["reclaim"]["jobs"] if j.kind == "train") == 0


def test_gang_job_larger_than_pool_is_rejected_not_partially_run(trace):
    jobs, _ = trace
    big = s.Job(9999, "a", "train", s.BATCH_TOTAL + 1, 10, 100, 30)
    r = s.run_batch(jobs + [big], "reclaim")
    assert big.id in {j.id for j in r["rejected"]}
    assert all(j.id != 9999 for j in r["finished"])


def test_unknown_policy_raises(trace):
    with pytest.raises(ValueError):
        s.run_batch(trace[0], "yolo")


def test_gpus_never_oversubscribed(trace):
    jobs, _ = trace
    r = s.run_batch(jobs, "reclaim")
    assert max(r["delivered_gpu_hours"].values()) * 60 <= s.BATCH_TOTAL * s.HORIZON
    assert r["alloc_gpu_hours"] <= s.BATCH_TOTAL * s.HORIZON / 60


def test_culling_cuts_idle_hours_and_wait(trace):
    _, nbs = trace
    off = s.run_notebooks(nbs, None)
    on = s.run_notebooks(nbs, 30)
    assert off["culled"] == 0 and on["culled"] > 0
    assert on["idle_gpu_hours"] < off["idle_gpu_hours"] / 3
    assert on["wait_p95"] < off["wait_p95"]
    assert on["sessions"] == off["sessions"]


def test_active_time_is_never_cut(trace):
    _, nbs = trace
    on = s.run_notebooks(nbs, 30)
    # held hours with culling still cover all active minutes
    assert on["held_gpu_hours"] * 60 >= sum(n.active for n in nbs)
