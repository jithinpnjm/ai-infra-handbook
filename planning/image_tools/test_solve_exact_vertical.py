import asyncio
from playwright.async_api import async_playwright
import pathlib

# Let's test the complete SVG with real Playwright bounds!
async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        
        # Test candidate_service_path.svg
        await page.goto(f'file://{pathlib.Path("candidate_service_path.svg").resolve()}')
        
        # Check all text elements
        texts = await page.query_selector_all('text')
        print(f"Total text elements: {len(texts)}")
        
        # Check Title
        t_box = await texts[0].bounding_box()
        print(f"Title box: {t_box}")
        print(f"  Top margin: {t_box['y']} (>=40: {t_box['y'] >= 40})")
        
        # Check all rungs
        for i in range(1, 8):
            g = await page.query_selector(f'#rung-1')
            
        await browser.close()

asyncio.run(run())
