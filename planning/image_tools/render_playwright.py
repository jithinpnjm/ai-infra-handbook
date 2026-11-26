import asyncio
from playwright.async_api import async_playwright
import pathlib

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_path = pathlib.Path("test_timeline.svg").resolve()
        await page.goto(f"file://{svg_path}")
        await page.screenshot(path="full_render.png")
        await browser.close()
        print("Rendered full_render.png at 1600x1200")

asyncio.run(main())
