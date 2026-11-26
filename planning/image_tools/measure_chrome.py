import subprocess
import json

# HTML to measure SVG text bounding box in Chrome
html = """<!DOCTYPE html>
<html>
<body>
<svg width="1600" height="1000">
  <text id="t1" font-family="sans-serif" font-size="24" font-weight="bold">Worker 1</text>
  <text id="t2" font-family="sans-serif" font-size="24" font-weight="bold">(4 + 3)</text>
  <text id="t3" font-family="sans-serif" font-size="30" font-weight="bold">Hypothetical inference pod</text>
  <text id="t4" font-family="sans-serif" font-size="24">Pinned staging buffers</text>
  <text id="t5" font-family="sans-serif" font-size="25" font-weight="bold">OOM kill expected:</text>
  <text id="t6" font-family="sans-serif" font-size="25" font-weight="bold">28.0 GiB cannot</text>
  <text id="t7" font-family="sans-serif" font-size="25" font-weight="bold">be reclaimed,</text>
  <text id="t8" font-family="sans-serif" font-size="25" font-weight="bold">limit is lower</text>
  <text id="t9" font-family="sans-serif" font-size="30" font-weight="bold">Fits, but page cache will be reclaimed constantly</text>
  <text id="t10" font-family="monospace" font-size="26" font-weight="bold">unreclaimable = workers x (pinned + runtime)</text>
  <text id="t11" font-family="sans-serif" font-size="26" font-weight="bold">Page cache is left out of the sum.</text>
</svg>
<script>
  const results = {};
  for (let i = 1; i <= 11; i++) {
    const el = document.getElementById('t' + i);
    const bb = el.getBBox();
    results['t' + i] = { text: el.textContent, width: bb.width, height: bb.height };
  }
  console.log('RESULTS:' + JSON.stringify(results));
</script>
</body>
</html>"""

open("/tmp/measure.html", "w").write(html)
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--dump-dom',
    '--virtual-time-budget=1000',
    'file:///tmp/measure.html'
], capture_output=True, text=True)

# Also run with node if available or extract
import re
print("Done measuring setup.")
