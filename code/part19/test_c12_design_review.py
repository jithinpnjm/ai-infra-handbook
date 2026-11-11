import c12_design_review as r


def test_good_design_has_no_findings():
    assert r.review(r.GOOD) == []


def test_bad_design_findings():
    f = r.review(r.BAD)
    assert len(f) == 21
    sections = {s for s, _ in f}
    assert sections == {"1", "3", "4", "5", "6", "7", "9", "10"}


def test_single_defects_are_caught_alone():
    import copy
    d = copy.deepcopy(r.GOOD)
    d["spare_gpus"] = 2
    assert [m for _, m in r.review(d)] == [
        "spare GPUs are smaller than the largest replica, so one node loss cannot be absorbed"]
    d = copy.deepcopy(r.GOOD)
    d["metrics"] = ["ttft"]
    assert len(r.review(d)) == 1
