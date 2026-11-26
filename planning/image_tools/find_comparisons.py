#!/usr/bin/env python3
# Let's inspect how other side-by-side / two column SVGs are structured in this repo.
import glob
import re

svg_files = glob.glob("*.svg")
print(f"Total SVGs: {len(svg_files)}")

for f in svg_files:
    with open(f, 'r') as fp:
        content = fp.read()
        if "side by side" in content or "comparison" in content.lower() or "versus" in content.lower():
            m = re.search(r'viewBox="0 0 1600 (\d+)"', content)
            h = m.group(1) if m else "unknown"
            t = re.search(r'<title>(.*?)</title>', content)
            title = t.group(1) if t else "no title"
            print(f"{f} (H={h}): {title}")
