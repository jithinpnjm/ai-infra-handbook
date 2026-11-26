#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import pathlib

async def render():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_path = pathlib.Path("candidate_gpu_checklist.svg").resolve()
        await page.goto(f"file://{svg_path}")
        await page.screenshot(path="candidate_gpu_checklist.png")
        await browser.close()
        print("Rendered to candidate_gpu_checklist.png")

asyncio.run(render())
