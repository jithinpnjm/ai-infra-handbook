"""Dependency graphs: topological order, cycle detection, BFS shortest path."""
from collections import deque


def topo_order(deps):
    """deps maps node -> list of nodes it depends on (they must come first).

    Kahn's algorithm. Returns (order, cycle_nodes). cycle_nodes is empty when the
    graph is acyclic. Otherwise it holds every node that is on a cycle or blocked by one.
    Ties are broken alphabetically so the order is deterministic.
    """
    nodes = set(deps)
    for ds in deps.values():
        nodes.update(ds)
    indeg = {n: 0 for n in nodes}
    dependents = {n: [] for n in nodes}
    for n, ds in deps.items():
        for d in set(ds):
            indeg[n] += 1
            dependents[d].append(n)
    ready = sorted(n for n in nodes if indeg[n] == 0)
    queue, order = deque(ready), []
    while queue:
        n = queue.popleft()
        order.append(n)
        newly = []
        for m in dependents[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                newly.append(m)
        queue.extend(sorted(newly))
    stuck = sorted(nodes - set(order))
    return order, stuck


def find_cycle(deps):
    """Return one cycle as a list [a, b, ..., a] following dependency edges, or None. DFS colours."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {}
    stack_path = []

    def visit(n):
        colour[n] = GREY
        stack_path.append(n)
        for d in sorted(set(deps.get(n, ()))):
            c = colour.get(d, WHITE)
            if c == GREY:
                return stack_path[stack_path.index(d):] + [d]
            if c == WHITE:
                found = visit(d)
                if found:
                    return found
        stack_path.pop()
        colour[n] = BLACK
        return None

    for n in sorted(deps):
        if colour.get(n, WHITE) == WHITE:
            found = visit(n)
            if found:
                return found
    return None


def shortest_path(graph, src, dst):
    """BFS on an unweighted graph. Return the node list or None. Mark nodes when enqueued."""
    if src == dst:
        return [src]
    parent = {src: None}
    queue = deque([src])
    while queue:
        n = queue.popleft()
        for m in graph.get(n, ()):
            if m not in parent:
                parent[m] = n
                if m == dst:
                    path = [m]
                    while parent[path[-1]] is not None:
                        path.append(parent[path[-1]])
                    return path[::-1]
                queue.append(m)
    return None


def reachable(graph, src):
    """Iterative DFS. Recursion would hit Python's limit on a long chain of services."""
    seen, stack = {src}, [src]
    while stack:
        n = stack.pop()
        for m in graph.get(n, ()):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    return seen


def blast_radius(deps, failed):
    """Services that transitively depend on `failed`."""
    rev = {}
    for n, ds in deps.items():
        for d in ds:
            rev.setdefault(d, []).append(n)
    return reachable(rev, failed) - {failed}
