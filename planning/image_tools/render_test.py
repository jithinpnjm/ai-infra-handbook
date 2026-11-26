import asyncio
from playwright.async_api import async_playwright
import pathlib

async def render():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_path = pathlib.Path("test_candidate_gpu_starvation.svg").resolve()
        await page.goto(f"file://{svg_path}")
        await page.screenshot(path="test_candidate_gpu_starvation.png")
        await browser.close()
        print("Rendered PNG successfully!")

asyncio.run(render())
