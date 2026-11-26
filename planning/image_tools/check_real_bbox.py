import xml.etree.ElementTree as ET
import pathlib
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': 1600, 'height': 1200})
    page.goto('file://' + str(pathlib.Path('test_candidate_api_batches.svg').resolve()))
    
    # Extract all rects and all texts
    data = page.evaluate('''() => {
        const rects = Array.from(document.querySelectorAll('rect')).map(r => ({
            id: r.parentElement.id || '',
            x: parseFloat(r.getAttribute('x')),
            y: parseFloat(r.getAttribute('y')),
            w: parseFloat(r.getAttribute('width')),
            h: parseFloat(r.getAttribute('height')),
            fill: r.getAttribute('fill'),
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

print(f"Total texts: {len(texts)}, Total rects: {len(rects)}")

for t in texts:
    if "Paginated API into batches" in t['text']:
        continue
    if "items arrive one at a time" in t['text']:
        continue # arrow label
    
    # Find matching containing rect
    # A rect contains t if t is inside r
    matched_rect = None
    min_area = 1e9
    for r in rects:
        if r['w'] >= 1600: continue
        # Check if t is approximately inside r
        if (r['x'] <= t['x'] + 5 and 
            r['y'] <= t['y'] + 5 and 
            r['x'] + r['w'] >= t['x'] + t['w'] - 5 and 
            r['y'] + r['h'] >= t['y'] + t['h'] - 5):
            area = r['w'] * r['h']
            if area < min_area:
                min_area = area
                matched_rect = r
            
    if matched_rect:
        r = matched_rect
        pad_left = t['x'] - r['x']
        pad_right = (r['x'] + r['w']) - (t['x'] + t['w'])
        pad_top = t['y'] - r['y']
        pad_bottom = (r['y'] + r['h']) - (t['y'] + t['h'])
        min_pad = min(pad_left, pad_right, pad_top, pad_bottom)
        status = "OK" if min_pad >= 16 else f"FAIL ({min_pad:.1f}px)"
        print(f"[{status:12}] '{t['text'][:35]:35}': L={pad_left:5.1f}, R={pad_right:5.1f}, T={pad_top:5.1f}, B={pad_bottom:5.1f}")
    else:
        print(f"[NO RECT    ] '{t['text']}'")
