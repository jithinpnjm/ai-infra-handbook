import xml.etree.ElementTree as ET

tree = ET.parse("candidate_experiment.svg")
root = tree.getroot()

# Let's inspect all boxes and text positions
boxes = [
    ("Header card", 40, 85, 1520, 55),
    ("Lane 1", 40, 180, 480, 470),
    ("Lane 2", 560, 180, 480, 470),
    ("Lane 3", 1080, 180, 480, 470),
    ("Side note", 40, 690, 1520, 75),
    ("Strip", 40, 805, 1520, 75),
    ("Footnote", 40, 920, 1520, 85),
    ("Bottom bar", 40, 1045, 1520, 75)
]

print("--- BOX GAPS CHECK ---")
for i in range(len(boxes)):
    name1, x1, y1, w1, h1 = boxes[i]
    print(f"{name1}: y={y1}..{y1+h1} (h={h1})")

print("\nVertical gaps between consecutive sections:")
print("Header to Lanes:", 180 - (85 + 55))
print("Lanes to Side note:", 690 - (180 + 470))
print("Side note to Strip:", 805 - (690 + 75))
print("Strip to Footnote:", 920 - (805 + 75))
print("Footnote to Bottom bar:", 1045 - (920 + 85))
print("Bottom bar to Canvas bottom (1160):", 1160 - (1045 + 75))

print("\nHorizontal gaps between lanes:")
print("Lane 1 to Lane 2:", 560 - (40 + 480))
print("Lane 2 to Lane 3:", 1080 - (560 + 480))
print("Lane 3 to Canvas right (1600):", 1600 - (1080 + 480))
print("Canvas left to Lane 1:", 40)
