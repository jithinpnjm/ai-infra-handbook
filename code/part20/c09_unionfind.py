"""Union-find with path compression and union by size."""


class UnionFind:
    def __init__(self, items=()):
        self.parent, self.size = {}, {}
        self.components = 0
        for x in items:
            self.add(x)

    def add(self, x):
        if x not in self.parent:
            self.parent[x], self.size[x] = x, 1
            self.components += 1

    def find(self, x):
        self.add(x)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:       # path compression, iterative
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        return True

    def groups(self):
        out = {}
        for x in self.parent:
            out.setdefault(self.find(x), set()).add(x)
        return list(out.values())


def failing_clusters(failing_nodes, links):
    """Groups of failing nodes that are connected by links between failing nodes."""
    bad = set(failing_nodes)
    uf = UnionFind(bad)
    for a, b in links:
        if a in bad and b in bad:
            uf.union(a, b)
    return sorted(sorted(g) for g in uf.groups())
