import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1100})
        svg_abs = os.path.abspath("test_timer_triggers.svg")
        await page.goto(f"file://{svg_abs}")
        
        # Query all text elements and check their bounding boxes
        texts = await page.query_selector_all("text")
        print(f"Total text elements: {len(texts)}")
        
        for i, t in enumerate(texts, 1):
            box = await t.bounding_box()
            content = await t.text_content()
            content_clean = " ".join(content.split())
            print(f"{i:2d}. x={box['x']:6.1f}, y={box['y']:6.1f}, w={box['width']:6.1f}, h={box['height']:6.1f} | '{content_clean[:40]}'")
            
            # Check canvas margins
            assert box['x'] >= 30, f"Text {i} x={box['x']} < 30"
            assert box['x'] + box['width'] <= 1570, f"Text {i} right edge > 1570"
            assert box['y'] >= 20, f"Text {i} y={box['y']} < 20"
            assert box['y'] + box['height'] <= 1080, f"Text {i} bottom edge > 1080"
            
        print("All text elements are well within canvas boundaries!")
        await browser.close()

asyncio.run(main())
