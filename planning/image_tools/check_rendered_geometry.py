import pathlib
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': 1600, 'height': 1200})
    svg_path = pathlib.Path('test_collections_output.svg').resolve()
    page.goto(f'file://{svg_path}')
    
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
        const rectElements = Array.from(document.querySelectorAll('rect')).map(r => ({
            id: r.parentElement.id || '',
            x: parseFloat(r.getAttribute('x') || 0),
            y: parseFloat(r.getAttribute('y') || 0),
            w: parseFloat(r.getAttribute('width') || 0),
            h: parseFloat(r.getAttribute('height') || 0),
            fill: r.getAttribute('fill'),
            stroke: r.getAttribute('stroke')
        }));
        return { textElements, rectElements };
    }''')
    browser.close()

texts = data['textElements']
rects = data['rectElements']

print(f"Total rendered text elements: {len(texts)}")
for i, t in enumerate(texts, 1):
    print(f"{i:2d}. x={t['x']:.1f}, y={t['y']:.1f}, w={t['w']:.1f}, h={t['h']:.1f}, right={t['right']:.1f}, bottom={t['bottom']:.1f}")
    print(f"    Text: '{t['text']}'")

# Check that every text is inside [0, 1600] and [0, 1200] with margin >= 16px
for t in texts:
    assert t['x'] >= 16, f"Left overflow: {t}"
    assert t['right'] <= 1600 - 16, f"Right overflow: {t}"
    assert t['y'] >= 16, f"Top overflow: {t}"
    assert t['bottom'] <= 1200 - 16, f"Bottom overflow: {t}"

print("\nALL TEXTS FIT WITHIN CANVAS WITH PADDING >= 16PX!")
