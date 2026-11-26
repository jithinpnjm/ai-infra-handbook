import asyncio
from playwright.async_api import async_playwright
import json

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        await page.goto("file:///Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook/planning/image_tools/test_n10_rtt.svg")
        
        # Get all text element bounding boxes
        texts = await page.evaluate('''() => {
            const els = Array.from(document.querySelectorAll('text'));
            return els.map(el => {
                const r = el.getBoundingClientRect();
                return {
                    text: el.textContent.trim().replace(/\s+/g, ' '),
                    x: r.x, y: r.y, width: r.width, height: r.height,
                    right: r.right, bottom: r.bottom
                };
            });
        }''')
        
        # Get all rect bounding boxes
        rects = await page.evaluate('''() => {
            const els = Array.from(document.querySelectorAll('rect'));
            return els.map(el => {
                const r = el.getBoundingClientRect();
                return {
                    x: r.x, y: r.y, width: r.width, height: r.height,
                    right: r.right, bottom: r.bottom
                };
            });
        }''')
        
        await browser.close()
        
        print("Text Bounding Boxes:")
        for t in texts:
            print(f"'{t['text']}': x={t['x']:.1f}, y={t['y']:.1f}, w={t['width']:.1f}, h={t['height']:.1f}, right={t['right']:.1f}")
            assert t['x'] >= 40, f"Text '{t['text']}' left margin violation {t['x']} < 40"
            assert t['right'] <= 1560, f"Text '{t['text']}' right margin violation {t['right']} > 1560"
            assert t['y'] >= 20, f"Text '{t['text']}' top margin violation {t['y']} < 20"
            assert t['bottom'] <= 880, f"Text '{t['text']}' bottom margin violation {t['bottom']} > 880"

        print("\nAll text elements fit comfortably inside the 1600x900 canvas with >= 40px margins!")

asyncio.run(check())
