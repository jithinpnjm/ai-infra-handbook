import xml.etree.ElementTree as ET
import re
import pathlib
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

for t in texts:
    if t['text'] == "Node lifecycle":
        continue
    # Find matching rect
    containing_rects = []
    for r in rects:
        if r['w'] == 1600: continue
        # Center proximity
        rcx = r['x'] + r['w'] / 2
        rcy = r['y'] + r['h'] / 2
        tcx = t['x'] + t['w'] / 2
        tcy = t['y'] + t['h'] / 2
        if abs(rcx - tcx) < r['w']/2 + 10 and abs(rcy - tcy) < r['h']/2 + 10:
            containing_rects.append(r)
            
    if containing_rects:
        r = containing_rects[0]
        pad_left = t['x'] - r['x']
        pad_right = (r['x'] + r['w']) - (t['x'] + t['w'])
        pad_top = t['y'] - r['y']
        pad_bottom = (r['y'] + r['h']) - (t['y'] + t['h'])
        status = "OK" if min(pad_left, pad_right, pad_top, pad_bottom) >= 16 else "FAIL"
        print(f"[{status}] '{t['text'][:32]}...': L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f}")
    else:
        print(f"[NO RECT] '{t['text']}'")
