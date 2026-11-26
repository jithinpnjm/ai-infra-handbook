import asyncio
from playwright.async_api import async_playwright
import os

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        await page.goto(f"file://{os.path.abspath('output.svg')}")
        
        details = await page.evaluate("""() => {
            const items = [];
            const textEls = document.querySelectorAll('text');
            for (const el of textEls) {
                const bbox = el.getBBox();
                // find enclosing rect or g
                items.push({
                    text: el.textContent.trim().replace(/\\s+/g, ' '),
                    x: bbox.x,
                    y: bbox.y,
                    w: bbox.width,
                    h: bbox.height,
                    right: bbox.x + bbox.width,
                    bottom: bbox.y + bbox.height
                });
            }
            return items;
        }""")
        
        for item in details:
            print(f"[{item['text'][:30]:30s}] x={item['x']:6.1f}, w={item['w']:5.1f}, right={item['right']:6.1f}, y={item['y']:6.1f}, h={item['h']:5.1f}")
        
        await browser.close()

asyncio.run(check())
