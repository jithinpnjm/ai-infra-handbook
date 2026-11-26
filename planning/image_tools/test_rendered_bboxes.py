import asyncio
from playwright.async_api import async_playwright
import pathlib

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_path = pathlib.Path("candidate_test_node_line.svg").resolve()
        await page.goto(f"file://{svg_path}")
        
        texts = await page.evaluate('''() => {
            const results = [];
            const textNodes = document.querySelectorAll('text');
            for (let t of textNodes) {
                const rect = t.getBoundingClientRect();
                results.push({
                    text: t.textContent.trim().replace(/\\s+/g, ' '),
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    right: rect.right,
                    bottom: rect.bottom
                });
            }
            return results;
        }''')
        
        print(f"Total rendered text elements: {len(texts)}")
        for i, t in enumerate(texts, 1):
            print(f"{i:2d}. x={t['x']:.1f}, w={t['width']:.1f}, r={t['right']:.1f}, y={t['y']:.1f}, h={t['height']:.1f} | '{t['text'][:40]}'")
            
        await browser.close()

asyncio.run(main())
