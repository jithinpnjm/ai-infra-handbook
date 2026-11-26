import asyncio
import os
import pathlib
from playwright.async_api import async_playwright

async def measure():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1080})
        svg_path = pathlib.Path("candidate_conntrack_race.svg").resolve()
        await page.goto(f"file://{svg_path}")
        await page.screenshot(path="candidate_conntrack_race.png")
        print("Screenshot saved to candidate_conntrack_race.png")

        # Measure text elements
        texts = await page.evaluate('''() => {
            const results = [];
            document.querySelectorAll('text').forEach(t => {
                const bbox = t.getBBox();
                results.push({
                    text: t.textContent.trim().replace(/\\s+/g, ' '),
                    x: bbox.x,
                    y: bbox.y,
                    width: bbox.width,
                    height: bbox.height,
                    fontSize: window.getComputedStyle(t).fontSize
                });
            });
            return results;
        }''')
        
        print(f"\nMeasured {len(texts)} text elements:")
        for t in texts:
            print(f"[{t['fontSize']}] x={t['x']:6.1f}, y={t['y']:6.1f}, w={t['width']:6.1f}, h={t['height']:5.1f} : '{t['text'][:50]}'")

        await browser.close()

asyncio.run(measure())
