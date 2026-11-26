import asyncio
from playwright.async_api import async_playwright
import pathlib

# Test card height 96px with baseline_title = by + 44, baseline_cmd = by + 74
svg_test = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <rect id="card" x="175" y="134" width="975" height="96" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <text id="title" x="325" y="178" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Pod</text>
  <text id="cmd" x="325" y="208" font-family="monospace" font-size="24" fill="#303a36">call the pod IP and pod port directly from another pod</text>
</svg>'''

with open("test_96.svg", "w") as f:
    f.write(svg_test)

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        await page.goto(f'file://{pathlib.Path("test_96.svg").resolve()}')
        
        c = await (await page.query_selector('#card')).bounding_box()
        t = await (await page.query_selector('#title')).bounding_box()
        m = await (await page.query_selector('#cmd')).bounding_box()
        
        pad_t = t['y'] - c['y']
        pad_b = (c['y'] + c['height']) - (m['y'] + m['height'])
        line_gap = m['y'] - (t['y'] + t['height'])
        
        print(f"Card: {c}")
        print(f"Title: {t}")
        print(f"Cmd: {m}")
        print(f"pad_t = {pad_t:.1f}px (>=16: {pad_t >= 16.0})")
        print(f"pad_b = {pad_b:.1f}px (>=16: {pad_b >= 16.0})")
        print(f"line_gap = {line_gap:.1f}px (>=0: {line_gap >= 0.0})")
        assert pad_t >= 16.0 and pad_b >= 16.0 and line_gap >= 0.0
        print("PERFECT PASS IN CHROMIUM!")
        
        await browser.close()

asyncio.run(check())
