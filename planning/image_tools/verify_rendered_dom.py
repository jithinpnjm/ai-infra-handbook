import asyncio
from playwright.async_api import async_playwright
import os

async def verify():
    svg_path = os.path.abspath("candidate_blocking_loop_fix.svg")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        await page.goto(f"file://{svg_path}")
        
        texts = await page.evaluate('''() => {
            const elements = Array.from(document.querySelectorAll('text'));
            return elements.map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    text: el.textContent.trim().replace(/\\s+/g, ' '),
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    right: rect.right,
                    bottom: rect.bottom
                };
            });
        }''')
        
        print(f"Total rendered text elements: {len(texts)}")
        for i, t in enumerate(texts, 1):
            print(f"{i:2d}. [{t['width']:6.1f}x{t['height']:4.1f} at ({t['x']:6.1f}, {t['y']:6.1f})] right={t['right']:6.1f} : '{t['text'][:40]}...'")
            assert t['x'] >= 40, f"Text overflows left: {t}"
            assert t['right'] <= 1560, f"Text overflows right ({t['right']} > 1560): {t}"
            assert t['bottom'] <= 1180, f"Text overflows bottom: {t}"
            
        await browser.close()
    print("\nALL RENDERED TEXT BOUNDING BOXES WITHIN CANVAS BOUNDS (PASS)!")

asyncio.run(verify())
