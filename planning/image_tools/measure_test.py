import subprocess, json, re

html = f'''<!DOCTYPE html>
<html>
<body>
<div id="container">
{open("test_candidate.svg").read()}
</div>
<script>
  const svg = document.querySelector('svg');
  const texts = Array.from(svg.querySelectorAll('text'));
  const results = texts.map(t => {{
    const bbox = t.getBBox();
    return {{
      text: t.textContent.replace(/\\s+/g, ' ').trim(),
      x: bbox.x,
      y: bbox.y,
      width: bbox.width,
      height: bbox.height
    }};
  }});
  console.log("JSON_OUTPUT:" + JSON.stringify(results));
</script>
</body>
</html>'''

open('/tmp/test_bboxes.html', 'w').write(html)
out = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new', '--disable-gpu', '--dump-dom',
    'file:///tmp/test_bboxes.html'
], capture_output=True, text=True)

# Also let's run Chrome with console output or node / python
