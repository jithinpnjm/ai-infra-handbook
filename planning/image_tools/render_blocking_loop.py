import asyncio
from playwright.async_api import async_playwright
import os

async def render():
    svg_path = os.path.abspath("candidate_blocking_loop_fix.svg")
    png_path = os.path.abspath("render_blocking_loop.png")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        await page.goto(f"file://{svg_path}")
        await page.screenshot(path=png_path)
        await browser.close()
    print("Rendered to render_blocking_loop.png successfully!")

asyncio.run(render())
