import asyncio
from playwright.async_api import async_playwright

async def measure():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1600, "height": 1100})
        await page.goto("file:///Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook/planning/image_tools/test_candidate_le.svg")
        data = await page.evaluate('''() => {
            const results = [];
            for (const t of document.querySelectorAll("text")) {
                const b = t.getBBox();
                results.push({
                    text: t.textContent.trim().replace(/\\s+/g, " "),
                    x: Math.round(b.x),
                    y: Math.round(b.y),
                    w: Math.round(b.width),
                    h: Math.round(b.height),
                    r: Math.round(b.x + b.width),
                    bot: Math.round(b.y + b.height)
                });
            }
            return results;
        }''')
        print(f"Total measured text elements: {len(data)}")
        for i, d in enumerate(data, 1):
            txt = d['text'][:35]
            print(f"{i:2d}. {txt:35s} | x={d['x']:4d}..{d['r']:4d} (w={d['w']:4d}) | y={d['y']:4d}..{d['bot']:4d} (h={d['h']:3d})")
        await page.screenshot(path="render_test_le.png")
        await b.close()

asyncio.run(measure())
