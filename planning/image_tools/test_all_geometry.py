import re

boxes = {
    "Block 1 Outer": (40, 140, 740, 216),
    "Block 1 Inner 1": (128, 150, 632, 94),
    "Block 1 Inner 2": (128, 252, 632, 94),
    "Block 2 Outer": (820, 140, 740, 216),
    "Block 2 Inner": (908, 148, 632, 198),
    "Rules Strip": (40, 396, 1520, 84),
    "Placement Strip": (40, 520, 1520, 118),
    "Walrus Use": (40, 678, 740, 120),
    "Matrix Examples": (40, 838, 740, 228),
    "Rules of Thumb": (820, 678, 740, 388),
    "Bottom Bar": (40, 1106, 1520, 64)
}

# Check gaps between major rows:
# Row 1 ends at 356
# Row 2 starts at 396 -> gap = 40
# Row 2 ends at 480
# Row 3 starts at 520 -> gap = 40
# Row 3 ends at 638
# Row 4 starts at 678 -> gap = 40
# Row 4 ends at 1066
# Bottom bar starts at 1106 -> gap = 40
# Bottom bar ends at 1170
# Canvas height = 1200 -> bottom margin = 30 px (or 1200 - 1160 = 40 px if we adjust slightly!)

for b, (x, y, w, h) in boxes.items():
    print(f"{b:18s}: x={x:4d}, y={y:4d}, w={w:4d}, h={h:4d}, right={x+w:4d}, bottom={y+h:4d}")

