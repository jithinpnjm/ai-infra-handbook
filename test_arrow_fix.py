import xml.etree.ElementTree as ET

# Test standard marker
svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M 2 2 L 8 5 L 2 8 Z" fill="#207448" />
    </marker>
  </defs>
  <!-- Downward line -->
  <line x1="100" y1="50" x2="100" y2="350" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />
  <!-- Upward line -->
  <line x1="300" y1="350" x2="300" y2="50" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" />
</svg>"""

with open("test_arrow.svg", "w") as f:
    f.write(svg)

import subprocess
cmd = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "--headless",
    "--disable-gpu",
    "--screenshot=test_arrow.png",
    "--window-size=400,400",
    "test_arrow.svg"
]
subprocess.run(cmd, capture_output=True)
print("Arrow test generated.")
