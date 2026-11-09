"""A deliberately slow function and its cProfile report."""
import cProfile
import io
import pstats


def dedupe_slow(items):
    seen = []
    for x in items:
        if x not in seen:      # list scan: O(n) per item
            seen.append(x)
    return seen


def dedupe_fast(items):
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def profile_text(fn, items, top=4):
    pr = cProfile.Profile()
    pr.enable()
    fn(items)
    pr.disable()
    out = io.StringIO()
    pstats.Stats(pr, stream=out).sort_stats("tottime").print_stats(top)
    return out.getvalue()


if __name__ == "__main__":
    data = [i % 4000 for i in range(20_000)]
    print(profile_text(dedupe_slow, data))
    print(profile_text(dedupe_fast, data))
