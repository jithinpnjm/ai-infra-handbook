"""M9: smallest-name-first dependency order, or a report of what is stuck in a cycle."""
import heapq


class CycleError(ValueError):
    def __init__(self, stuck):
        super().__init__("cycle among: " + ", ".join(sorted(stuck)))
        self.stuck = set(stuck)


def lexi_toposort(deps):
    """deps maps a service to the services it needs first. O((V+E) log V).

    Services that only appear as a dependency are included.
    """
    nodes = set(deps)
    for needs in deps.values():
        nodes.update(needs)
    indegree = {n: 0 for n in nodes}
    dependents = {n: [] for n in nodes}
    for svc, needs in deps.items():
        for d in set(needs):
            indegree[svc] += 1
            dependents[d].append(svc)
    ready = [n for n, d in indegree.items() if d == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        n = heapq.heappop(ready)
        order.append(n)
        for m in dependents[n]:
            indegree[m] -= 1
            if indegree[m] == 0:
                heapq.heappush(ready, m)
    if len(order) != len(nodes):
        raise CycleError(nodes - set(order))
    return order
