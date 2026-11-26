import subprocess
import json
import pathlib

svg_file = pathlib.Path("test_candidate_burst.svg").resolve()

# We can render an HTML page with the SVG in headless Chrome and extract exact getBBox() values
html_content = f"""<!DOCTYPE html>
<html>
<head><style>body {{ margin: 0; background: white; }}</style></head>
<body>
{svg_file.read_text()}
<script>
window.onload = () => {{
    const svg = document.querySelector('svg');
    const texts = Array.from(svg.querySelectorAll('text')).map(t => {{
        const b = t.getBBox();
        const tspans = Array.from(t.querySelectorAll('tspan')).map(ts => {{
            const tb = ts.getBBox();
            return {{ text: ts.textContent, x: tb.x, y: tb.y, w: tb.width, h: tb.height }};
        }});
        return {{
            id: t.id,
            text: t.textContent.replace(/\\s+/g, ' ').trim(),
            fs: window.getComputedStyle(t).fontSize,
            x: b.x,
            y: b.y,
            w: b.width,
            h: b.height,
            tspans
        }};
    }});

    const rects = Array.from(svg.querySelectorAll('rect')).map(r => {{
        const b = r.getBBox();
        return {{
            x: b.x,
            y: b.y,
            w: b.width,
            h: b.height,
            fill: r.getAttribute('fill'),
            stroke: r.getAttribute('stroke')
        }};
    }});

    const icons = Array.from(svg.querySelectorAll('g[transform]')).map(g => {{
        const b = g.getBBox();
        return {{ x: b.x, y: b.y, w: b.width, h: b.height }};
    }});

    document.body.setAttribute('data-results', JSON.stringify({{ texts, rects, icons }}));
}};
</script>
</body>
</html>
"""

html_path = pathlib.Path("/tmp/measure_burst.html")
html_path.write_text(html_content)

# Run chrome headless with --dump-dom or print to console
chrome_cmd = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--run-all-compositor-stages-before-draw',
    '--virtual-time-budget=2000',
    '--dump-dom',
    f'file://{html_path}'
]
res = subprocess.run(chrome_cmd, capture_output=True, text=True)

import re
m = re.search(r'data-results="([^"]+)"', res.stdout)
if not m:
    print("Failed to capture data-results")
    import sys; sys.exit(1)

import html
raw_json = html.unescape(m.group(1))
data = json.loads(raw_json)

print("=== MEASURED TEXT ELEMENTS ===")
for i, t in enumerate(data['texts'], 1):
    print(f"\n{i}. [{t['fs']}] '{t['text'][:50]}...'")
    print(f"   BBox: x={t['x']:.1f}, y={t['y']:.1f}, w={t['w']:.1f}, h={t['h']:.1f}")
    for ts in t['tspans']:
        print(f"      tspan: x={ts['x']:.1f}, y={ts['y']:.1f}, w={ts['w']:.1f}, h={ts['h']:.1f} | '{ts['text'][:30]}...'")

print("\n=== PADDING CHECKS (>= 16px to containing rects) ===")
for t in data['texts']:
    if "The 16-request burst" in t['text']:
        continue # Title
    # find containing rect (excluding the full canvas 1600x1060)
    matching = []
    for r in data['rects']:
        if r['w'] >= 1590: continue
        # does r contain t?
        pad_left = t['x'] - r['x']
        pad_right = (r['x'] + r['w']) - (t['x'] + t['w'])
        pad_top = t['y'] - r['y']
        pad_bottom = (r['y'] + r['h']) - (t['y'] + t['h'])
        if pad_left >= 0 and pad_right >= 0 and pad_top >= 0 and pad_bottom >= 0:
            matching.append((r, pad_left, pad_right, pad_top, pad_bottom))
    if not matching:
        print(f"FAIL: No containing rect found for '{t['text'][:40]}...'")
    else:
        # pick smallest rect
        matching.sort(key=lambda x: x[0]['w'] * x[0]['h'])
        r, pl, pr, pt, pb = matching[0]
        min_pad = min(pl, pr, pt, pb)
        status = "PASS" if min_pad >= 16 else "FAIL"
        print(f"[{status}] '{t['text'][:35]}...' -> pads: L={pl:.1f}, R={pr:.1f}, T={pt:.1f}, B={pb:.1f} (min={min_pad:.1f})")
        assert min_pad >= 16, f"Padding too small ({min_pad:.1f} < 16) for '{t['text']}'"

print("\nALL CONTAINER PADDING CHECKS PASSED (>= 16px)!")
