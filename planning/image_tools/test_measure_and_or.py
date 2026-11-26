import asyncio, pathlib
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1600, "height": 1150})
        await page.goto("file://" + str(pathlib.Path("candidate_and_or_trap.svg").resolve()))
        data = await page.evaluate("""() => {
            const results = [];
            for (const t of document.querySelectorAll("text")) {
                const b = t.getBBox();
                results.push({
                    text: t.textContent.trim().replace(/\\s+/g, " "),
                    x: b.x, y: b.y, w: b.width, h: b.height,
                    fs: window.getComputedStyle(t).fontSize
                });
            }
            return results;
        }""")
        await b.close()
        for i, r in enumerate(data, 1):
            txt = r["text"][:45]
            fs = r["fs"]
            print(f"{i:2d}. [{fs:5s}] {txt:45s} | x={r['x']:6.1f}, y={r['y']:6.1f}, w={r['w']:5.1f}, h={r['h']:4.1f}")

asyncio.run(check())
