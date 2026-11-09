"""H7: online clusters of failed hosts (union-find with size and path compression)."""


class FailureClusters:
    def __init__(self):
        self._parent = {}
        self._size = {}
        self._largest = 0
        self._count = 0

    def _find(self, x):
        root = x
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[x] != root:  # compress the path
            self._parent[x], x = root, self._parent[x]
        return root

    def add(self, x):
        if x not in self._parent:
            self._parent[x] = x
            self._size[x] = 1
            self._count += 1
            self._largest = max(self._largest, 1)

    def link(self, a, b):
        """Mark a and b failed and in the same cluster. Return True if two clusters merged."""
        self.add(a)
        self.add(b)
        ra, rb = self._find(a), self._find(b)
        if ra == rb:
            return False
        if self._size[ra] < self._size[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        self._size[ra] += self._size[rb]
        self._count -= 1
        self._largest = max(self._largest, self._size[ra])
        return True

    def size_of(self, x):
        return self._size[self._find(x)] if x in self._parent else 0

    @property
    def clusters(self):
        return self._count

    @property
    def largest(self):
        return self._largest
