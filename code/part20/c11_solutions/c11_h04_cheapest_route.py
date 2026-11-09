"""H4: cheapest route using at most k intermediate hops."""


def cheapest_route(n, edges, src, dst, k):
    """Nodes are 0..n-1, edges are (u, v, cost) with cost >= 0. Return cost or -1.

    Bellman-Ford limited to k+1 edges: O(k * E) time, O(n) space. Each round reads
    the previous round's costs only, so a round never uses two new edges.
    """
    INF = float("inf")
    best = [INF] * n
    best[src] = 0
    for _ in range(k + 1):
        nxt = best[:]
        for u, v, c in edges:
            if best[u] + c < nxt[v]:
                nxt[v] = best[u] + c
        best = nxt
    return best[dst] if best[dst] != INF else -1
