import asyncio
import pathlib
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1080})
        svg_url = pathlib.Path("test_queue_candidate.svg").resolve().as_uri()
        await page.goto(svg_url)
        
        screenshot_path = "/private/var/folders/5k/hkmswyf95w5b0y7_xc87ddf80000gn/T/opencode/test_queue.png"
        await page.screenshot(path=screenshot_path)
        print("Screenshot saved to", screenshot_path)
        
        texts = await page.eval_on_selector_all("text", """elements => {
            return elements.map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    text: el.textContent.trim().replace(/\\s+/g, " "),
                    x: rect.x,
                    y: rect.y,
                    right: rect.right,
                    bottom: rect.bottom,
                    width: rect.width,
                    height: rect.height
                };
            });
        }""")
        
        print(f"Playwright found {len(texts)} rendered text elements:")
        for t in texts:
            txt = t["text"][:40]
            x = t["x"]
            r = t["right"]
            w = t["width"]
            print(f"   text: '{txt}' -> x={x:.1f}, right={r:.1f}, width={w:.1f}")
            assert x >= 40, f"Left margin violated: {t['text']} ({x} < 40)"
            assert r <= 1560, f"Right margin violated: {t['text']} ({r} > 1560)"
        
        await browser.close()
        print("ALL PLAYWRIGHT MARGIN CHECKS PASSED!")

asyncio.run(check())
