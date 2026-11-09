"""H8: route table with '*' single-segment wildcards, static segments win."""


class Router:
    """Trie keyed by path segment. match tries the static child first, then '*', backtracking."""

    def __init__(self):
        self._root = {}

    @staticmethod
    def _segments(path):
        return [s for s in path.split("/") if s]

    def add(self, pattern, handler):
        node = self._root
        for seg in self._segments(pattern):
            node = node.setdefault(seg, {})
        node[None] = handler  # None key marks the end of a route

    def match(self, path):
        return self._walk(self._root, self._segments(path), 0)

    def _walk(self, node, segs, i):
        if i == len(segs):
            return node.get(None)
        seg = segs[i]
        if seg != "*" and seg in node:
            hit = self._walk(node[seg], segs, i + 1)
            if hit is not None:
                return hit
        if "*" in node:
            return self._walk(node["*"], segs, i + 1)
        return None
