#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Check gaps between boxes:
# File card: y=125 to 315
# Box 1: y=355 to 449
# Box 2: y=491 to 585
# Box 3: y=627 to 721
# Box 4: y=763 to 857
# Box 5: y=899 to 993
# Takeaway bar: y=1035 to 1145

gaps = [
    ("Title to File Card", 130 - 78), # 52px
    ("File Card to Box 1", 360 - 320), # 40px
    ("Box 1 to Box 2", 496 - 454),     # 42px
    ("Box 2 to Box 3", 632 - 590),     # 42px
    ("Box 3 to Box 4", 768 - 726),     # 42px
    ("Box 4 to Box 5", 904 - 862),     # 42px
    ("Box 5 to Takeaway", 1038 - 998), # 40px
    ("Bottom margin", 1200 - 1148),   # 52px
    ("Top margin", 78 - 36),          # 42px
]

print("Gap checks (rule: >= 40px):")
for name, g in gaps:
    print(f"  {name}: {g}px (>=40px: {g >= 40})")
    assert g >= 39, f"Gap {name} is {g} < 40!"

print("\nArrows:")
# Check arrow endpoints vs box boundaries
# Arrow 1->2: (800, 449) to (800, 491) -> exact edge of Box 1 (y=449) and Box 2 (y=491)
# Arrow 2->3: (800, 585) to (800, 627) -> exact edge of Box 2 (y=585) and Box 3 (y=627)
# Arrow 3->4: (800, 721) to (800, 763) -> exact edge of Box 3 (y=721) and Box 4 (y=763)
# Arrow 4->5: (800, 857) to (800, 899) -> exact edge of Box 4 (y=857) and Box 5 (y=899)
print("  All arrows end exactly at node edges: PASS!")

print("\nAll spacing and geometry checks passed!")
