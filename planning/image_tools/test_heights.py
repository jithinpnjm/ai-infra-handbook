cost_items = [
    # Item 1: 3 lines
    ("Cost 1", [
        "a list stores 8 byte pointers on a 64-bit system",
        "to separate objects: a list of one million floats",
        "costs about 32 MB before you count the objects"
    ], False),
    # Item 2: 3 lines (ORANGE)
    ("Cost 2", [
        'array("f") stores 4 bytes per float,',
        'a list stores a float object of',
        'about 32 bytes per value'
    ], True),
    # Item 3: 2 lines
    ("Cost 3", [
        "memoryview(bytearray(1024))[100:200] is a",
        "zero-copy window for sockets, mmap and NumPy"
    ], False),
    # Item 4: 4 lines
    ("Cost 4", [
        "list.insert(0, x) and list.pop(0) are O(n);",
        "deque has appendleft, popleft and",
        "maxlen=N ring buffer: deque(maxlen=1000)",
        "keeps the last 1000 samples"
    ], False),
    # Item 5: 5 lines
    ("Cost 5", [
        "sort() sorts in place and returns None;",
        "sorted() returns a new list; Timsort is stable,",
        "O(n log n), O(n) best case on partly ordered data;",
        "use key= not a comparison function;",
        "tuple comparison is lexicographic"
    ], False),
    # Item 6: 3 lines
    ("Cost 6", [
        "bisect.bisect_left and insort keep a list sorted;",
        "heapq.nlargest(5, items) gives top-k",
        "without a full sort"
    ], False),
    # Item 7: 2 lines
    ("Cost 7", [
        "x in list is linear: convert to a set",
        "when testing membership many times"
    ], False),
    # Item 8: 2 lines
    ("Cost 8", [
        "copy.copy, slicing and list()",
        "each make a shallow copy"
    ], False)
]

# Total lines: 3 + 3 + 2 + 4 + 5 + 3 + 2 + 2 = 24 lines!
# Let's check card heights with font 24px and line spacing:
# If font = 24px, dy = 28px.
# text height for N lines = 24 + (N-1)*28.
# top padding = 18px, bottom padding = 18px.
# Total card height = 24 + (N-1)*28 + 36 = 60 + (N-1)*28.
# N=2: 60 + 28 = 88px. (text_h=52, v_pad = (88-52)/2 = 18px >= 16px)
# N=3: 60 + 56 = 116px. (text_h=80, v_pad = (116-80)/2 = 18px >= 16px)
# N=4: 60 + 84 = 144px. (text_h=108, v_pad = (144-108)/2 = 18px >= 16px)
# N=5: 60 + 112 = 172px. (text_h=136, v_pad = (172-136)/2 = 18px >= 16px)

total_ch = 116 + 116 + 88 + 144 + 172 + 116 + 88 + 88
print("Total card heights:", total_ch)
# 928 px!
# With 7 gaps of 8px = 56px.
# Total = 984 px!
# Panel starts at y=95. Header at y=115..155 (takes 60px).
# Cards can start at y = 175!
# 175 + 984 = 1159!
# But bottom bar is at y=1120!
# We need cards to finish by y = 1105!
# So we need total height from y=170 to y=1100 = 930 px!
# 930 - 56 (gaps) = 874 px for cards!
