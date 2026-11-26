import asyncio
from playwright.async_api import async_playwright
import pathlib

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_path = pathlib.Path("candidate_test_node_line.svg").resolve()
        await page.goto(f"file://{svg_path}")
        await page.screenshot(path="candidate_node_line.png")
        await browser.close()
        print("Rendered to candidate_node_line.png successfully")

asyncio.run(main())
