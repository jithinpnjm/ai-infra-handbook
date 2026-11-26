import re
import xml.etree.ElementTree as ET

with open("output.svg") as f:
    svg_content = f.read()

root = ET.fromstring(svg_content)

# Check all style definitions and inline font-sizes
font_sizes = re.findall(r'font-size:\s*(\d+)px', svg_content)
font_sizes += re.findall(r'font-size="(\d+)"', svg_content)
font_sizes = [int(s) for s in font_sizes]
print("All found font sizes:", set(font_sizes))

for s in font_sizes:
    assert s >= 24, f"Font size {s}px is smaller than 24px!"

print("Font size audit PASSED! Minimum font size is", min(font_sizes), "px.")
