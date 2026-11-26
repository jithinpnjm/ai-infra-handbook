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
        page = await b.new_page(viewport={"width": 1600, "height": 1160})
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
        
        print("Checking padding on all nodes and boxes:")
        
        # 1. Start Left: rect x=305..485, y=148..218
        # text x=374.7..441.2, y=164..199
        pad_top = 164.0 - 148
        pad_bot = 218 - 199.0
        print(f"Start Left: pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f} ({'PASS' if pad_top>=16 and pad_bot>=16 else 'FAIL'})")
        
        # 2. End Left: rect x=305..485, y=714..784
        # text x=381.5..434.5, y=730..765
        pad_top = 730.0 - 714
        pad_bot = 784 - 765.0
        print(f"End Left: pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f} ({'PASS' if pad_top>=16 and pad_bot>=16 else 'FAIL'})")

        # 3. Start Right: rect x=935..1115, y=148..218
        # text x=1004.7..1071.2, y=164..199
        pad_top = 164.0 - 148
        pad_bot = 218 - 199.0
        print(f"Start Right: pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f} ({'PASS' if pad_top>=16 and pad_bot>=16 else 'FAIL'})")

        # 4. End Right: rect x=935..1115, y=714..784
        # text x=1011.5..1064.5, y=730..765
        pad_top = 730.0 - 714
        pad_bot = 784 - 765.0
        print(f"End Right: pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f} ({'PASS' if pad_top>=16 and pad_bot>=16 else 'FAIL'})")

        # 5. Box b (Left): rect x=105..315, y=440..550
        # text x=224.8..245.2, y=476..515
        pad_top = 476.0 - 440
        pad_bot = 550 - 515.0
        print(f"Box b Left: pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f} ({'PASS' if pad_top>=16 and pad_bot>=16 else 'FAIL'})")

        # 6. Box c (Left): rect x=475..685, y=440..550
        # text x=594.8..615.2, y=476..515
        pad_top = 476.0 - 440
        pad_bot = 550 - 515.0
        print(f"Box c Left: pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f} ({'PASS' if pad_top>=16 and pad_bot>=16 else 'FAIL'})")

        # 7. Box b (Right): rect x=925..1125, y=424..494
        # text x=1034.8..1055.2, y=440..479
        pad_top = 440.0 - 424
        pad_bot = 494 - 479.0
        print(f"Box b Right: pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f} ({'PASS' if pad_top>=16 and pad_bot>=16 else 'FAIL'})")

        # 8. Box c (Right): rect x=1280..1535, y=390..570
        # title c: x=1355..1375.4, y=404..443
        # sec text: x=1355..1496.9, y=452..536
        pad_top = 404.0 - 390
        pad_bot = 570 - 536.0
        pad_right = 1535 - 1496.9
        pad_icon = 1355 - (1298 + 48) # icon x=1298..1346
        print(f"Box c Right: pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f}, pad_right={pad_right:.1f}, pad_icon={pad_icon:.1f}")

        # 9. Left Diamond: cx=395, cy=320, rx=250, ry=72
        # icon: translate(285, 302), size 36x36 -> x=285..321, y=302..338
        # text: x=340.6..515.4, y=301..336
        pts_left = [(340.6, 301), (515.4, 301), (340.6, 336), (515.4, 336), (285, 302), (321, 302), (285, 338), (321, 338)]
        min_dl = min(dist_to_diamond(px, py, 395, 320, 250, 72) for px, py in pts_left)
        print(f"Left diamond: min_dist={min_dl:.1f}px ({'PASS' if min_dl>=16 else 'FAIL'})")

        # 10. Right Diamond 1: cx=1025, cy=320, rx=230, ry=72
        # icon: translate(915, 304), size 32x32 -> x=915..947, y=304..336
        # text: x=970.6..1145.4, y=301..336
        pts_r1 = [(970.6, 301), (1145.4, 301), (970.6, 336), (1145.4, 336), (915, 304), (947, 304), (915, 336), (947, 336)]
        min_dr1 = min(dist_to_diamond(px, py, 1025, 320, 230, 72) for px, py in pts_r1)
        print(f"Right diamond 1: min_dist={min_dr1:.1f}px ({'PASS' if min_dr1>=16 else 'FAIL'})")

        # 11. Right Diamond 2: cx=1025, cy=604, rx=230, ry=78
        # icon: translate(900, 588), size 32x32 -> x=900..932, y=588..620
        # text: x=955.1..1150.8, y=585..620
        pts_r2 = [(955.1, 585), (1150.8, 585), (955.1, 620), (1150.8, 620), (900, 588), (932, 588), (900, 620), (932, 620)]
        min_dr2 = min(dist_to_diamond(px, py, 1025, 604, 230, 78) for px, py in pts_r2)
        print(f"Right diamond 2: min_dist={min_dr2:.1f}px ({'PASS' if min_dr2>=16 else 'FAIL'})")

        # 12. Guards padding
        # Each guard rect: height 48, y in [837, 885], [891, 939], [945, 993], [999, 1047]
        # Text y in [848, 877.2], [902, 931.2], [956, 985.2], [1010, 1039.0]
        # Top pads: 848 - 837 = 11px < 16px!
        print("Guard top pads:", 848 - 837, 902 - 891, 956 - 945, 1010 - 999)

asyncio.run(check())
