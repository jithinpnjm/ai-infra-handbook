"""Will a loop over N items finish in a second? Estimate, then measure."""
import time


def plain_loop(n):
    total = 0
    for i in range(n):
        total += i
    return total


def with_call(n):
    def f(x):
        return x + 1
    total = 0
    for i in range(n):
        total += f(i)
    return total


def builtin_sum(n):
    return sum(range(n))


def ns_per_item(fn, n):
    start = time.perf_counter()
    fn(n)
    return (time.perf_counter() - start) / n * 1e9


if __name__ == "__main__":
    n = 10_000_000
    for fn in (plain_loop, with_call, builtin_sum):
        ns = ns_per_item(fn, n)
        print(f"{fn.__name__:12} {ns:6.1f} ns per item, {ns*n/1e9:5.2f} s for 10M")
