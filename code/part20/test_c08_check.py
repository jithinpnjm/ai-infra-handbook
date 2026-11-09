import c08_check as ck


def add(a, b):
    return a + b


def test_all_pass():
    assert ck.check(add, [((1, 2), 3), ((0, 0), 0)], verbose=False) == []


def test_reports_failure_and_exception():
    bad = ck.check(add, [((1, 2), 4), ((1, "x"), 0)], verbose=False)
    assert [f[0] for f in bad] == [0, 1]
    assert "TypeError" in bad[1][2]


def test_deepcopy_protects_later_cases():
    def eat(xs):
        xs.pop()
        return len(xs)
    shared = [1, 2, 3]
    assert ck.check(eat, [((shared,), 2), ((shared,), 2)], verbose=False) == []


def test_unordered_and_tolerance():
    assert ck.check(lambda: [2, 1], [((), [1, 2])], unordered=True, verbose=False) == []
    assert ck.check(lambda: 0.1 + 0.2, [((), 0.3)], tol=1e-9, verbose=False) == []
    assert ck.check(lambda: 0.1 + 0.2, [((), 0.3)], verbose=False) != []


def test_stress_finds_a_wrong_fast_version():
    def fast(xs):
        return max(xs[:-1]) if len(xs) > 1 else xs[0]   # bug: ignores last item

    def brute(xs):
        return sorted(xs)[-1]

    def gen(rng):
        return ([rng.randint(0, 9) for _ in range(rng.randint(1, 6))],)

    assert ck.stress(fast, brute, gen) is not None
    assert ck.stress(max, brute, gen) is None
