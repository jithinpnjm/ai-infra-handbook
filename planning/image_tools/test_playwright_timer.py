import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1100})
        svg_abs = os.path.abspath("test_timer_triggers.svg")
        await page.goto(f"file://{svg_abs}")
        
        # Take screenshot to verify visually
        await page.screenshot(path="test_timer_triggers.png")
        print("Rendered test_timer_triggers.png successfully!")

        # Check DOM text elements bounding boxes
        texts = await page.query_selector_all("text")
        print(f"Playwright found {len(texts)} text elements.")
        
        # Check overlaps or clipping
        rects = await page.query_selector_all("rect")
        print(f"Playwright found {len(rects)} rect elements.")
        
        await browser.close()

asyncio.run(main())
