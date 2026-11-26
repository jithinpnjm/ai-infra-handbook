import asyncio
from playwright.async_api import async_playwright

async def measure():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page()
        # Measure sans-serif widths
        tests = [
            "0.0: hit 0.57, p50 0.22, p99 0.99, max/mean 1.22",
            "100 (cache-only): 0.98, 0.16, 4.39, 3.80",
            "round_robin 0.46, 0.50, 2.33, 1.00",
            "cache_bounded 0.95, 0.10, 0.50, 2.13",
            "Table 1 policy: hit rate, p50 s, p99 s, max over mean load",
            "Table 2 bound in seconds of backlog"
        ]
        
        html = '<svg xmlns="http://www.w3.org/2000/svg">'
        for i, t in enumerate(tests):
            html += f'<text id="t{i}" x="0" y="50" font-family="sans-serif" font-size="24">{t}</text>'
        html += '</svg>'
        await page.set_content(html)
        
        for i, t in enumerate(tests):
            w = await page.evaluate(f'document.getElementById("t{i}").getBBox().width')
            print(f"'{t[:35]}...' ({len(t)} chars): {w:.1f}px (rate {w/len(t)/24:.3f})")
            
        await b.close()

asyncio.run(measure())
