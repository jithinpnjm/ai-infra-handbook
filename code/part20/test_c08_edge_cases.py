import pytest
import c08_check as ck
import c08_edge_cases as e


def test_compress():
    cases = [("", ""), ("a", "a"), ("ab", "ab"), ("aa", "aa"), ("aaa", "a3"),
             ("aabcccccaaa", "a2b1c5a3"), ("abc", "abc"), ("AaAa", "AaAa")]
    assert ck.check(e.compress, cases, verbose=False) == []


def test_two_sum():
    cases = [(([], 1), None), (([3], 6), None), (([3, 3], 6), (0, 1)),
             (([2, 7, 11, 15], 9), (0, 1)), (([-1, -2, -3], -5), (1, 2))]
    assert ck.check(e.two_sum, cases, verbose=False) == []


def test_top_k_tie_goes_to_smaller_item():
    assert e.top_k_frequent("abracadabra", 2) == ["a", "b"]
    assert e.top_k_frequent("bbaa", 1) == ["a"]
    assert e.top_k_frequent([], 3) == []
    assert e.top_k_frequent("ab", 5) == ["a", "b"]


def test_merge_intervals_checklist():
    cases = [([], []), ([(1, 2)], [(1, 2)]), ([(1, 2), (2, 3)], [(1, 3)]),
             ([(1, 5), (2, 3)], [(1, 5)]), ([(3, 4), (1, 2)], [(1, 2), (3, 4)])]
    assert ck.check(e.merge_intervals, cases, verbose=False) == []


def test_brackets():
    for text, want in [("", True), ("()[]{}", True), ("(]", False), ("(", False), (")", False), ("([{}])", True)]:
        assert e.valid_brackets(text) is want


def test_longest_unique_window_against_brute_force():
    def brute(s):
        best = 0
        for i in range(len(s)):
            for j in range(i, len(s)):
                if len(set(s[i:j + 1])) == j - i + 1:
                    best = max(best, j - i + 1)
        return best

    def gen(rng):
        return ("".join(rng.choice("abc") for _ in range(rng.randint(0, 8))),)

    assert ck.stress(e.longest_unique_window, brute, gen) is None


@pytest.mark.parametrize("probe", e.EDGE_CHECKLISTS["string"])
def test_string_probes_do_not_crash(probe):
    e.compress(probe)
    e.valid_brackets(probe)
    assert 0 <= e.longest_unique_window(probe) <= len(probe)
