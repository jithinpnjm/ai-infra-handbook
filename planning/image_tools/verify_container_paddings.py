import xml.etree.ElementTree as ET
import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': 1600, 'height': 1160})
    page.goto('file://' + str(pathlib.Path('candidate_node_lifecycle.svg').resolve()))
    
    # Extract all rects and all texts
    data = page.evaluate('''() => {
        const rects = Array.from(document.querySelectorAll('rect')).map(r => ({
            x: parseFloat(r.getAttribute('x')),
            y: parseFloat(r.getAttribute('y')),
            w: parseFloat(r.getAttribute('width')),
            h: parseFloat(r.getAttribute('height')),
            stroke: r.getAttribute('stroke')
        }));
        const texts = Array.from(document.querySelectorAll('text')).map(t => {
            const b = t.getBBox();
            return {
                text: t.textContent.replace(/\\s+/g, ' ').trim(),
                x: b.x,
                y: b.y,
                w: b.width,
                h: b.height
            };
        });
        return { rects, texts };
    }''')
    browser.close()

rects = data['rects']
texts = data['texts']

print("\n=== Verifying padding for each text inside its container rect ===")
# Title has no container rect, so exclude "Node lifecycle"
for t in texts:
    if t['text'] == "Node lifecycle":
        continue
    # Find the matching rect that contains this text
    containing_rects = []
    for r in rects:
        if r['w'] == 1600: continue
        # Check if text is inside this rect
        if r['x'] <= t['x'] and (r['x'] + r['w']) >= (t['x'] + t['w']) and \
           r['y'] <= t['y'] and (r['y'] + r['h']) >= (t['y'] + t['h']):
            containing_rects.append(r)
            
    assert len(containing_rects) >= 1, f"No container rect found for text: '{t['text']}'"
    r = containing_rects[0]
    pad_left = t['x'] - r['x']
    pad_right = (r['x'] + r['w']) - (t['x'] + t['w'])
    pad_top = t['y'] - r['y']
    pad_bottom = (r['y'] + r['h']) - (t['y'] + t['h'])
    
    print(f"'{t['text'][:35]}...':")
    print(f"   Paddings: Left={pad_left:.1f}px, Right={pad_right:.1f}px, Top={pad_top:.1f}px, Bottom={pad_bottom:.1f}px")
    assert pad_left >= 16, f"pad_left {pad_left:.1f} < 16 for '{t['text']}'"
    assert pad_right >= 16, f"pad_right {pad_right:.1f} < 16 for '{t['text']}'"
    assert pad_top >= 16, f"pad_top {pad_top:.1f} < 16 for '{t['text']}'"
    assert pad_bottom >= 16, f"pad_bottom {pad_bottom:.1f} < 16 for '{t['text']}'"

print("\nALL 20 TEXTS HAVE >= 16px PADDING ON ALL 4 SIDES!")
