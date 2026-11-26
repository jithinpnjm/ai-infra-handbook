#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def measure():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1100})
        await page.goto(f"file://{__import__('os').path.abspath('test_bgp_attrs.svg')}")
        
        # Check all rects and their contained texts
        results = await page.evaluate('''() => {
            const rects = Array.from(document.querySelectorAll('rect')).map(r => {
                const b = r.getBoundingClientRect();
                return {
                    id: r.parentElement.id || r.id,
                    x: b.x, y: b.y, width: b.width, height: b.height,
                    right: b.right, bottom: b.bottom,
                    fill: r.getAttribute('fill')
                };
            });
            const texts = Array.from(document.querySelectorAll('text')).map(t => {
                const b = t.getBoundingClientRect();
                return {
                    text: t.textContent.trim().replace(/\\s+/g, ' '),
                    x: b.x, y: b.y, width: b.width, height: b.height,
                    right: b.right, bottom: b.bottom
                };
            });
            return { rects, texts };
        }''')
        
        print("TEXT MEASUREMENTS:")
        for t in results['texts']:
            print(f"Text: '{t['text'][:30]}...' -> x={t['x']:.1f}, right={t['right']:.1f}, y={t['y']:.1f}, bottom={t['bottom']:.1f}, width={t['width']:.1f}")
            # check canvas margin >= 40
            assert t['x'] >= 40, f"Left margin violated: {t['x']}"
            assert t['right'] <= 1560, f"Right margin violated: {t['right']}"

        await browser.close()
        print("ALL TEXT IS WITHIN MARGINS (40 to 1560)!")

if __name__ == "__main__":
    asyncio.run(measure())
