import subprocess
import json
import xml.etree.ElementTree as ET

svg_text = open("candidate_expand_contract.svg").read()

html = f"""<!DOCTYPE html>
<html>
<body>
{svg_text}
<pre id="out"></pre>
<script>
  const results = [];
  const texts = document.querySelectorAll('text');
  texts.forEach((el, idx) => {{
    const bb = el.getBBox();
    results.push({{
      idx: idx + 1,
      text: el.textContent.replace(/\\s+/g, ' ').trim(),
      x: bb.x,
      y: bb.y,
      width: bb.width,
      height: bb.height,
      right: bb.x + bb.width,
      bottom: bb.y + bb.height
    }});
  }});
  document.getElementById('out').textContent = JSON.stringify(results, null, 2);
</script>
</body>
</html>"""

open("/tmp/measure_svg.html", "w").write(html)
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--dump-dom',
    'file:///tmp/measure_svg.html'
], capture_output=True, text=True)

import re
m = re.search(r'<pre id="out">(.*?)</pre>', res.stdout, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print(f"Measured {len(data)} text elements:")
    for item in data:
        print(f" {item['idx']}. '{item['text'][:45]}' -> x={item['x']:.1f}, y={item['y']:.1f}, w={item['width']:.1f}, h={item['height']:.1f}, r={item['right']:.1f}, b={item['bottom']:.1f}")
else:
    print("Could not find output in DOM dump")
