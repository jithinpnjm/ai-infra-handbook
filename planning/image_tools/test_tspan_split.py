import xml.etree.ElementTree as ET
import re

svg_snippet = """<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="28" font-family="sans-serif"><tspan x="100" dy="0">4 threads: </tspan><tspan x="100" dy="34" font-family="monospace" font-size="24">ThreadPoolExecutor(</tspan><tspan x="100" dy="30" font-family="monospace" font-size="24">max_workers=4)</tspan></text>
  <text font-size="28" font-family="sans-serif"><tspan x="600" dy="0">4 processes: </tspan><tspan x="600" dy="34" font-family="monospace" font-size="24">ProcessPoolExecutor(</tspan><tspan x="600" dy="30" font-family="monospace" font-size="24">max_workers=4)</tspan></text>
</svg>"""

root = ET.fromstring(svg_snippet)
for t in root.iter("{http://www.w3.org/2000/svg}text"):
    full_text = re.sub(r'\s+', ' ', "".join(t.itertext()).strip())
    print(f"Extracted: '{full_text}'")
    assert full_text in [
        "4 threads: ThreadPoolExecutor(max_workers=4)",
        "4 processes: ProcessPoolExecutor(max_workers=4)"
    ]
print("Assertion passed!")
