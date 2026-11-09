"""H1: LFU cache with O(1) get and put. Ties go to the least recently used key."""
from collections import OrderedDict, defaultdict


class LFUCache:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._val = {}
        self._freq = {}
        self._buckets = defaultdict(OrderedDict)  # freq -> keys, oldest first
        self._min = 0

    def _touch(self, key):
        f = self._freq[key]
        del self._buckets[f][key]
        if not self._buckets[f]:
            del self._buckets[f]
            if self._min == f:
                self._min = f + 1
        self._freq[key] = f + 1
        self._buckets[f + 1][key] = None

    def get(self, key, default=None):
        if key not in self._val:
            return default
        self._touch(key)
        return self._val[key]

    def put(self, key, value):
        if key in self._val:
            self._val[key] = value
            self._touch(key)
            return
        if len(self._val) >= self.capacity:
            victim, _ = self._buckets[self._min].popitem(last=False)
            if not self._buckets[self._min]:
                del self._buckets[self._min]
            del self._val[victim]
            del self._freq[victim]
        self._val[key] = value
        self._freq[key] = 1
        self._buckets[1][key] = None
        self._min = 1

    def __len__(self):
        return len(self._val)
