"""P4: plan a dependency-ordered rollout in waves, and see what a failure blocks.

deps maps a service to the services that must be rolled out before it.
A wave is a set of services that can go out at the same time.
"""
import heapq


class CycleError(ValueError):
    def __init__(self, cycle):
        super().__init__("dependency cycle: " + " -> ".join(cycle))
        self.cycle = cycle


def _graph(deps):
    nodes = set(deps)
    for needs in deps.values():
        nodes.update(needs)
    needs = {n: set(deps.get(n, ())) for n in nodes}
    users = {n: set() for n in nodes}
    for n, ds in needs.items():
        for d in ds:
            users[d].add(n)
    return nodes, needs, users


def find_cycle(deps):
    """Return one cycle as a list [a, b, ..., a], or None. Iterative DFS, O(V+E)."""
    nodes, needs, _ = _graph(deps)
    state = {}  # absent = new, 1 = on the current path, 2 = done
    for root in sorted(nodes):
        if root in state:
            continue
        path = [root]
        iters = {root: iter(sorted(needs[root]))}
        state[root] = 1
        while path:
            n = path[-1]
            nxt = next(iters[n], None)
            if nxt is None:
                state[n] = 2
                path.pop()
            elif state.get(nxt) == 1:
                return path[path.index(nxt):] + [nxt]
            elif nxt not in state:
                state[nxt] = 1
                path.append(nxt)
                iters[nxt] = iter(sorted(needs[nxt]))
    return None


def plan_waves(deps, max_parallel=None):
    """Return a list of waves. Raise CycleError if the graph has a cycle.

    With max_parallel=None each wave is everything that is ready, so the number of
    waves is the longest dependency chain. With a cap, services whose dependants
    form the longest chain go first. That greedy rule is a heuristic: the cap
    makes optimal scheduling hard in general.
    """
    cycle = find_cycle(deps)
    if cycle:
        raise CycleError(cycle)
    nodes, needs, users = _graph(deps)
    # height = length of the longest chain of dependants above a service
    height = {}
    for n in _reverse_topo(nodes, needs, users):
        height[n] = 1 + max((height[u] for u in users[n]), default=0)
    remaining = {n: len(needs[n]) for n in nodes}
    ready = [(-height[n], n) for n, c in remaining.items() if c == 0]
    heapq.heapify(ready)
    waves = []
    while ready:
        take = len(ready) if max_parallel is None else min(max_parallel, len(ready))
        wave = [heapq.heappop(ready)[1] for _ in range(take)]
        waves.append(sorted(wave))
        for n in wave:
            for u in users[n]:
                remaining[u] -= 1
                if remaining[u] == 0:
                    heapq.heappush(ready, (-height[u], u))
    return waves


def _reverse_topo(nodes, needs, users):
    left = {n: len(users[n]) for n in nodes}
    stack = [n for n, c in left.items() if c == 0]
    while stack:
        n = stack.pop()
        yield n
        for d in needs[n]:
            left[d] -= 1
            if left[d] == 0:
                stack.append(d)


def blocked_by(deps, failed):
    """Every service that cannot roll out because it needs a failed one, directly or not."""
    _, _, users = _graph(deps)
    blocked, stack = set(), list(failed)
    while stack:
        n = stack.pop()
        for u in users.get(n, ()):
            if u not in blocked:
                blocked.add(u)
                stack.append(u)
    return blocked - set(failed)
