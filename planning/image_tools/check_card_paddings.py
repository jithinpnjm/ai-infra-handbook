import pathlib
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': 1600, 'height': 1200})
    svg_path = pathlib.Path('test_collections_output.svg').resolve()
    page.goto(f'file://{svg_path}')
    
    # We want to check padding between each text element and its immediate card rect
    data = page.evaluate('''() => {
        const textElements = Array.from(document.querySelectorAll('text')).map(t => {
            const b = t.getBBox();
            return {
                text: t.textContent.replace(/\\s+/g, ' ').trim(),
                x: b.x,
                y: b.y,
                w: b.width,
                h: b.height,
                right: b.x + b.width,
                bottom: b.y + b.height
            };
        });
        const rectElements = Array.from(document.querySelectorAll('rect')).map(r => {
            const b = r.getBBox();
            return {
                x: b.x,
                y: b.y,
                w: b.width,
                h: b.height,
                right: b.x + b.width,
                bottom: b.y + b.height,
                fill: r.getAttribute('fill')
            };
        });
        return { textElements, rectElements };
    }''')
    browser.close()

texts = data['textElements']
rects = data['rectElements']

print("=== Padding Analysis ===")
for t in texts:
    # find all rects that contain this text's center
    tcx = t['x'] + t['w'] / 2
    tcy = t['y'] + t['h'] / 2
    
    containers = []
    for r in rects:
        if r['w'] >= 1590 and r['h'] >= 1190:
            continue # background
        if r['x'] <= t['x'] and r['right'] >= t['right'] and r['y'] <= t['y'] and r['bottom'] >= t['bottom']:
            containers.append(r)
    
    # sort containers by area ascending to find closest enclosing box
    containers.sort(key=lambda r: r['w'] * r['h'])
    
    if containers:
        c = containers[0]
        pad_left = t['x'] - c['x']
        pad_right = c['right'] - t['right']
        pad_top = t['y'] - c['y']
        pad_bottom = c['bottom'] - t['bottom']
        min_pad = min(pad_left, pad_right, pad_top, pad_bottom)
        print(f"Text: '{t['text'][:35]}...'")
        print(f"   Paddings: left={pad_left:.1f}, right={pad_right:.1f}, top={pad_top:.1f}, bottom={pad_bottom:.1f} (min={min_pad:.1f})")
        if min_pad < 14:
            print(f"   WARNING: min padding {min_pad:.1f} < 14px!")
    else:
        print(f"Text outside explicit rect: '{t['text'][:35]}...' (x={t['x']:.1f}, y={t['y']:.1f})")
