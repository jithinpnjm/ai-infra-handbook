#!/usr/bin/env python3

b4_lines = [
    ("Inode C: type, ", 24, False),       # 15 chars = 216 px
    ("permissions, ", 24, False),         # 13 chars = 187.2 px
    ("owner, size, ", 24, False),         # 13 chars = 187.2 px
    ("times, ", 24, False),               #  7 chars = 100.8 px
    ("link count, ", 24, False),          # 12 chars = 172.8 px
    ("pointers to ", 24, False),          # 12 chars = 172.8 px
    ("data blocks", 24, False)            # 11 chars = 158.4 px
]

full = "".join(t for t, fs, m in b4_lines).strip()
expected = "Inode C: type, permissions, owner, size, times, link count, pointers to data blocks"
print("full:    ", repr(full))
print("expected:", repr(expected))
assert full == expected

for t, fs, is_mono in b4_lines:
    w = len(t) * fs * (0.62 if is_mono else 0.6)
    pad = (260 - w) / 2
    print(f"pad={pad:.1f}px (w={w:.1f}px) | '{t}'")
    assert pad >= 16.0

print("Box 4 PASSES ALL 7 LINES WITH >= 22px PADDING!")
