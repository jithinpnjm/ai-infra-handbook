"""LRU cache two ways: OrderedDict, and a hash map plus a doubly linked list."""
from collections import OrderedDict


class LRUOrdered:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.d = OrderedDict()

    def get(self, key, default=None):
        if key not in self.d:
            return default
        self.d.move_to_end(key)          # most recent goes to the right end
        return self.d[key]

    def put(self, key, value):
        if key in self.d:
            self.d.move_to_end(key)
        self.d[key] = value
        if len(self.d) > self.capacity:
            self.d.popitem(last=False)   # evict from the left: least recently used

    def keys_oldest_first(self):
        return list(self.d)


class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key, self.value, self.prev, self.next = key, value, None, None


class LRUList:
    """Head side is most recent, tail side is least recent. Sentinels remove edge cases."""

    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.map = {}
        self.head, self.tail = _Node(), _Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, n):
        n.prev.next, n.next.prev = n.next, n.prev

    def _push_front(self, n):
        n.next, n.prev = self.head.next, self.head
        self.head.next.prev = n
        self.head.next = n

    def get(self, key, default=None):
        n = self.map.get(key)
        if n is None:
            return default
        self._unlink(n)
        self._push_front(n)
        return n.value

    def put(self, key, value):
        n = self.map.get(key)
        if n is not None:
            n.value = value
            self._unlink(n)
            self._push_front(n)
            return
        if len(self.map) >= self.capacity:
            lru = self.tail.prev
            self._unlink(lru)
            del self.map[lru.key]       # the node must remember its key for this line
        n = _Node(key, value)
        self.map[key] = n
        self._push_front(n)

    def keys_oldest_first(self):
        out, n = [], self.tail.prev
        while n is not self.head:
            out.append(n.key)
            n = n.prev
        return out
