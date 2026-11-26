expected_labels = [
    "Sequence types on two axes, and what a list really costs",
    "container (holds references to objects stored elsewhere)",
    "flat (values of one type side by side in memory)",
    "mutable",
    "immutable",
    "list, collections.deque",
    "tuple",
    "bytearray, array.array",
    "str, bytes",
    "Costs",
    "a list stores 8 byte pointers on a 64-bit system to separate objects: a list of one million floats costs about 32 MB before you count the objects",
    'array("f") stores 4 bytes per float, a list stores a float object of about 32 bytes per value',
    "memoryview(bytearray(1024))[100:200] is a zero-copy window for sockets, mmap and NumPy",
    "list.insert(0, x) and list.pop(0) are O(n); deque has appendleft, popleft and maxlen=N ring buffer: deque(maxlen=1000) keeps the last 1000 samples",
    "sort() sorts in place and returns None; sorted() returns a new list; Timsort is stable, O(n log n), O(n) best case on partly ordered data; use key= not a comparison function; tuple comparison is lexicographic",
    "bisect.bisect_left and insort keep a list sorted; heapq.nlargest(5, items) gives top-k without a full sort",
    "x in list is linear: convert to a set when testing membership many times",
    "copy.copy, slicing and list() each make a shallow copy",
    "The choice of sequence type affects both memory and speed"
]

print("Expected labels count:", len(expected_labels))
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. '{l}'")
