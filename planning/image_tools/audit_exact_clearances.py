import asyncio, pathlib
from playwright.async_api import async_playwright

async def audit():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1600, "height": 1150})
        await page.goto("file://" + str(pathlib.Path("candidate_and_or_trap.svg").resolve()))
        data = await page.evaluate("""() => {
            const issues = [];
            
            // Check text padding inside rect containers
            const rects = Array.from(document.querySelectorAll("rect")).map(r => {
                const b = r.getBBox();
                return { id: r.getAttribute("id") || r.parentElement.getAttribute("id") || "", x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, bot: b.y + b.height };
            });
            
            // Check each text element
            const texts = Array.from(document.querySelectorAll("text")).map(t => {
                const b = t.getBBox();
                return {
                    text: t.textContent.trim().replace(/\\s+/g, " "),
                    x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, bot: b.y + b.height
                };
            });
            
            return { rects, texts };
        }""")
        await b.close()
        
        print("Auditing clearances...")
        # Check guards inside guard rects
        # Guard 1: text x=155, w=420.1 -> right=575.1. Rect w=1450, x=75..1525. Pad left = 80px, pad right = 949.9px. Pad top/bot: rect y=720..784 (h=64), text y=738..767.2 (h=29.2), pad top=18px, pad bot=16.8px! PASS >= 16px!
        for t in data["texts"]:
            print(f"Text '{t['text'][:30]}': x={t['x']:.1f}..{t['r']:.1f}, y={t['y']:.1f}..{t['bot']:.1f}")

asyncio.run(audit())
