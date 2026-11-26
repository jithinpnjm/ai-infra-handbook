# Let's inspect how other SVG files in this repo do cards with sub-boxes or bars.
import glob
import re

svg_files = glob.glob("*.svg")
print(f"Found {len(svg_files)} svg files.")

for f in svg_files[:15]:
    content = open(f).read()
    # Check if there are rects and text
    rects = re.findall(r'<rect[^>]+>', content)
    texts = re.findall(r'<text[^>]+>', content)
    print(f"{f}: {len(rects)} rects, {len(texts)} texts")
