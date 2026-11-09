"""M12: consistent hash ring with virtual nodes."""
import bisect
import hashlib


def _h(text):
    return int(hashlib.md5(text.encode()).hexdigest()[:16], 16)


class HashRing:
    """get is O(log(N*vnodes)). add/remove rebuild the sorted point list: O(N*vnodes log)."""

    def __init__(self, nodes=(), vnodes=100):
        self.vnodes = vnodes
        self._nodes = set()
        self._points = []
        self._owner = {}
        for n in nodes:
            self.add(n)

    def add(self, node):
        if node in self._nodes:
            return
        self._nodes.add(node)
        for i in range(self.vnodes):
            self._owner[_h(f"{node}#{i}")] = node
        self._points = sorted(self._owner)

    def remove(self, node):
        if node not in self._nodes:
            return
        self._nodes.discard(node)
        self._owner = {p: n for p, n in self._owner.items() if n != node}
        self._points = sorted(self._owner)

    def get(self, key):
        if not self._points:
            return None
        i = bisect.bisect_right(self._points, _h(key)) % len(self._points)
        return self._owner[self._points[i]]
