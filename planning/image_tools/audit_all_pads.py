import asyncio, pathlib, math
from playwright.async_api import async_playwright

def dist_to_diamond(px, py, cx, cy, rx, ry):
    dx = abs(px - cx)
    dy = abs(py - cy)
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    val = dx/rx + dy/ry
    return (1.0 - val) / scale

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
                    x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, bot: b.y + b.height
                });
            }
            return results;
        }""")
        await b.close()
        
        # Check all rect containers padding:
        # Start (left): rect x=305..485, y=148..222. Text: x=374.7..441.2, y=166..201.
        # Pad top: 166 - 148 = 18px. Pad bot: 222 - 201 = 21px. Pad left: 374.7 - 305 = 69.7px. Pad right: 485 - 441.2 = 43.8px. PASS!
        print("Start left padding:", 166 - 148, 222 - 201)
        
        # End (left): rect x=305..485, y=598..672. Text: x=381.5..434.5, y=616..651.
        # Pad top: 616 - 598 = 18px. Pad bot: 672 - 651 = 21px. PASS!
        print("End left padding:", 616 - 598, 672 - 651)

        # Start (right): rect x=925..1105, y=148..222. Text: x=994.7..1061.2, y=166..201.
        print("Start right padding:", 166 - 148, 222 - 201)

        # End (right): rect x=925..1105, y=678..752. Text: x=1001.5..1054.5, y=696..731.
        print("End right padding:", 696 - 678, 752 - 731)

        # Box b (left): rect x=125..335, y=415..515. Text: x=239.8..260.2, y=446..485.
        print("Box b left padding:", 446 - 415, 515 - 485, 239.8 - 125, 335 - 260.2)

        # Box c (left): rect x=455..665, y=415..515. Text: x=569.8..590.2, y=446..485.
        print("Box c left padding:", 446 - 415, 515 - 485, 569.8 - 455, 665 - 590.2)

        # Box b (right): rect x=915..1115, y=395..475. Text: x=1024.8..1045.2, y=417..456.
        print("Box b right padding:", 417 - 395, 475 - 456, 1024.8 - 915, 1115 - 1045.2)

        # Box c (right): rect x=1270..1530, y=375..545. Text:
        # Title c: x=1350..1370.4, y=387..426
        # Sec: x=1350..1491.9, y=433..517.
        # Top pad: 387 - 375 = 12px < 16px! WAIT!
        print("Box c right top pad:", 387 - 375, "bot pad:", 545 - 517)
        
        # Diamonds:
        # Left diamond: cx=395, cy=320, rx=250, ry=78
        # icon: translate(285, 302), size 36x36 -> x=285..321, y=302..338
        # text: x=340.6..515.4, y=301..336
        pts_left = [(340.6, 301), (515.4, 301), (340.6, 336), (515.4, 336), (285, 302), (321, 302), (285, 338), (321, 338)]
        min_dl = min(dist_to_diamond(px, py, 395, 320, 250, 78) for px, py in pts_left)
        print("Left diamond min pad:", min_dl)

        # Right diamond 1: cx=1015, cy=300, rx=220, ry=60
        # icon: translate(905, 284), size 32x32 -> x=905..937, y=284..316
        # text: x=960.6..1135.4, y=281..316
        pts_r1 = [(960.6, 281), (1135.4, 281), (960.6, 316), (1135.4, 316), (905, 284), (937, 284), (905, 316), (937, 316)]
        min_dr1 = min(dist_to_diamond(px, py, 1015, 300, 220, 60) for px, py in pts_r1)
        print("Right diamond 1 min pad:", min_dr1)

        # Right diamond 2: cx=1015, cy=570, rx=220, ry=70
        # icon: translate(895, 554), size 32x32 -> x=895..927, y=554..586
        # text: x=950.1..1145.8, y=551..586
        pts_r2 = [(950.1, 551), (1145.8, 551), (950.1, 586), (1145.8, 586), (895, 554), (927, 554), (895, 586), (927, 586)]
        min_dr2 = min(dist_to_diamond(px, py, 1015, 570, 220, 70) for px, py in pts_r2)
        print("Right diamond 2 min pad:", min_dr2)

asyncio.run(check())
