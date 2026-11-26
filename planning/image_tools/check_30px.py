import re
import asyncio
from playwright.async_api import async_playwright

with open("candidate_reader_map.svg") as f:
    svg = f.read()

svg_test = re.sub(r'font-size="28"', 'font-size="30"', svg)
svg_test = re.sub(r'font-size="26" font-weight="bold" fill="#303a36"', 'font-size="30" font-weight="bold" fill="#303a36"', svg_test)
svg_test = re.sub(r'font-size="25" font-weight="bold" fill="#303a36"', 'font-size="30" font-weight="bold" fill="#303a36"', svg_test)

with open("test_30px.svg", "w") as f:
    f.write(svg_test)

async def check():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1600, "height": 1100})
        await page.goto("file://" + "/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook/planning/image_tools/test_30px.svg")
        data = await page.evaluate('''() => {
            const results = [];
            for (const t of document.querySelectorAll("text")) {
                const b = t.getBBox();
                results.push({text: t.textContent.trim().replace(/\\s+/g, " "), x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, bot: b.y + b.height});
            }
            return results;
        }''')
        for d in data:
            txt = d['text'][:30]
            print(f"{txt:30s} | x={d['x']:5.1f}..{d['r']:5.1f} (w={d['w']:5.1f}) | y={d['y']:5.1f}..{d['bot']:5.1f} (h={d['h']:4.1f})")
        await b.close()

asyncio.run(check())
