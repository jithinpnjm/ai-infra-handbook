items = [
    "a list stores 8 byte pointers on a 64-bit system to separate objects: a list of one million floats costs about 32 MB before you count the objects",
    'array("f") stores 4 bytes per float, a list stores a float object of about 32 bytes per value',
    "memoryview(bytearray(1024))[100:200] is a zero-copy window for sockets, mmap and NumPy",
    "list.insert(0, x) and list.pop(0) are O(n); deque has appendleft, popleft and maxlen=N ring buffer: deque(maxlen=1000) keeps the last 1000 samples",
    "sort() sorts in place and returns None; sorted() returns a new list; Timsort is stable, O(n log n), O(n) best case on partly ordered data; use key= not a comparison function; tuple comparison is lexicographic",
    "bisect.bisect_left and insort keep a list sorted; heapq.nlargest(5, items) gives top-k without a full sort",
    "x in list is linear: convert to a set when testing membership many times",
    "copy.copy, slicing and list() each make a shallow copy"
]

import textwrap

for i, it in enumerate(items, 1):
    wrapped = textwrap.wrap(it, width=46)
    print(f"Item {i} ({len(wrapped)} lines):")
    for line in wrapped:
        print(f"  [{len(line):2d}] {line}")
