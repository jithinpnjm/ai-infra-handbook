import asyncio
from playwright.async_api import async_playwright
import pathlib

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1100})
        svg_path = pathlib.Path("candidate_reader_map.svg").resolve()
        await page.goto(f"file://{svg_path}")
        
        # Evaluate bboxes
        data = await page.evaluate('''() => {
            const results = [];
            const texts = Array.from(document.querySelectorAll('text'));
            for (const t of texts) {
                const tspans = Array.from(t.querySelectorAll('tspan'));
                if (tspans.length > 0) {
                    for (const ts of tspans) {
                        const bbox = ts.getBBox();
                        results.push({
                            text: ts.textContent.trim(),
                            parentText: t.textContent.trim().replace(/\\s+/g, ' '),
                            x: bbox.x,
                            y: bbox.y,
                            width: bbox.width,
                            height: bbox.height,
                            right: bbox.x + bbox.width,
                            bottom: bbox.y + bbox.height
                        });
                    }
                } else {
                    const bbox = t.getBBox();
                    results.push({
                        text: t.textContent.trim().replace(/\\s+/g, ' '),
                        parentText: t.textContent.trim().replace(/\\s+/g, ' '),
                        x: bbox.x,
                        y: bbox.y,
                        width: bbox.width,
                        height: bbox.height,
                        right: bbox.x + bbox.width,
                        bottom: bbox.y + bbox.height
                    });
                }
            }
            
            const rects = Array.from(document.querySelectorAll('rect')).map(r => {
                const b = r.getBBox();
                return {
                    x: b.x,
                    y: b.y,
                    width: b.width,
                    height: b.height,
                    right: b.x + b.width,
                    bottom: b.y + b.height
                };
            });
            
            return { texts: results, rects: rects };
        }''')
        
        print("=== Bounding Boxes of Rendered Texts ===")
        for i, t in enumerate(data['texts'], 1):
            print(f"{i:2d}. x={t['x']:6.1f}..{t['right']:6.1f} (w={t['width']:5.1f}) | y={t['y']:6.1f}..{t['bottom']:6.1f} (h={t['height']:4.1f}) : '{t['text']}'")
            
        await browser.close()

asyncio.run(main())
