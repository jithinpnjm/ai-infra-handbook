import math

# Let's test if 6 boxes can fit horizontally across 1600
# Canvas width = 1600.
# Margins = 40px left, 40px right -> usable width = 1520px.
# 5 arrows between the 6 boxes.
# If arrow length = 20px, 5 * 20 = 100px.
# Total width for 6 boxes = 1420px.
# Average width per box = 1420 / 6 = 236.6px.

# But boxes can have different widths!
# Let's check the labels for each stage:
stages = [
    (1, "shell fork and execve"),
    (2, "kernel checks the file and picks a format handler"),
    (3, "ELF loader maps LOAD segments, builds the stack"),
    (4, "PT_INTERP: kernel maps ld.so, execution starts in the dynamic linker"),
    (5, "ld.so loads DT_NEEDED libraries, relocates, runs constructors"),
    (6, "_start, __libc_start_main, main")
]

# In each stage box, we need:
# - Number circle 1..6 (r=24 -> diameter 48)
# - Icon (outline icon ~56px)
# - Label text (>= 24px, or >= 30px bold for node title)

print("Checking character lengths of stage labels:")
for num, text in stages:
    words = text.split()
    max_w = max(len(w) for w in words)
    print(f"Stage {num}: total len={len(text)}, max word len={max_w} ('{max([w for w in words if len(w)==max_w])}')")
