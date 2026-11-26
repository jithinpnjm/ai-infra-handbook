import pathlib
from playwright.sync_api import sync_playwright

svg_path = pathlib.Path("test_candidate.svg").resolve()

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1150})
    page.goto(f"file://{svg_path}")
    
    # Check all text elements bounding boxes against their parent/associated rects
    eval_script = """
    () => {
        const results = [];
        const texts = Array.from(document.querySelectorAll('text'));
        
        texts.forEach((t, idx) => {
            const tbox = t.getBoundingClientRect();
            // Find enclosing or nearest rect
            let g = t.closest('g');
            let rect = g ? g.querySelector('rect') : null;
            if (!rect) {
                // Check if it's title
                results.push({
                    text: t.textContent.trim().substring(0, 30),
                    fontSize: parseFloat(window.getComputedStyle(t).fontSize),
                    boxPadL: tbox.left,
                    boxPadR: 1600 - tbox.right,
                    boxPadT: tbox.top,
                    boxPadB: 1150 - tbox.bottom,
                    tbox: {x: tbox.left, y: tbox.top, w: tbox.width, h: tbox.height}
                });
            } else {
                const rbox = rect.getBoundingClientRect();
                results.push({
                    id: g.id || 'rect',
                    text: t.textContent.trim().replace(/\\s+/g, ' ').substring(0, 40),
                    fontSize: parseFloat(window.getComputedStyle(t).fontSize),
                    padL: tbox.left - rbox.left,
                    padR: rbox.right - tbox.right,
                    padT: tbox.top - rbox.top,
                    padB: rbox.bottom - tbox.bottom,
                    tbox: {x: tbox.left, y: tbox.top, w: tbox.width, h: tbox.height},
                    rbox: {x: rbox.left, y: rbox.top, w: rbox.width, h: rbox.height}
                });
            }
        });
        return results;
    }
    """
    res = page.evaluate(eval_script)
    print("=== PLAYWRIGHT BOUNDING BOX AUDIT ===")
    all_ok = True
    for item in res:
        padL = item.get('padL', item.get('boxPadL'))
        padR = item.get('padR', item.get('boxPadR'))
        padT = item.get('padT', item.get('boxPadT'))
        padB = item.get('padB', item.get('boxPadB'))
        text = item['text']
        fs = item['fontSize']
        
        ok_h = padL >= 16.0 and padR >= 16.0
        ok_v = padT >= 10.0 and padB >= 10.0
        ok = ok_h and ok_v
        if not ok: all_ok = False
        print(f"[{'OK' if ok else 'WARN'}] fs={fs:.0f}px | L={padL:5.1f} R={padR:5.1f} T={padT:5.1f} B={padB:5.1f} | '{text}'")

    print(f"\nAll paddings >= 16px horizontal and clean vertical? {all_ok}")
    browser.close()
