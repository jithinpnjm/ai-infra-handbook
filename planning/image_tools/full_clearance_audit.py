import asyncio
from playwright.async_api import async_playwright
import xml.etree.ElementTree as ET
import re, pathlib

async def audit():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1600, "height": 1200})
        await page.goto("file://" + str(pathlib.Path("test_adjusted.svg").resolve()))
        data = await page.evaluate('''() => {
            const results = [];
            for (const t of document.querySelectorAll("text")) {
                const b = t.getBBox();
                results.push({
                    text: t.textContent.trim().replace(/\\s+/g, " "),
                    x: b.x, y: b.y, w: b.width, h: b.height,
                    r: b.x + b.width, bot: b.y + b.height
                });
            }
            return results;
        }''')
        await b.close()
        return data

results = asyncio.run(audit())

cards = [
    ("Title", None, results[0]),
    ("Subtitle Pill", (450, 72, 700, 64), results[1]),
    ("Setup Box", (50, 176, 1500, 94), results[2]),
    ("Table 1 Header", (70, 326, 685, 106), results[3]),
    ("T1 Row 1", (70, 438, 685, 110), results[4]),
    ("T1 Row 2", (70, 560, 685, 110), results[5]),
    ("T1 Row 3", (70, 682, 685, 110), results[6]),
    ("T1 Row 4", (70, 804, 685, 110), results[7]),
    ("Table 2 Header", (845, 326, 685, 106), results[8]),
    ("T2 Row 1", (845, 438, 685, 96), results[9]),
    ("T2 Row 2", (845, 540, 685, 84), results[10]),
    ("T2 Row 3", (845, 630, 685, 84), results[11]),
    ("T2 Row 4", (845, 720, 685, 84), results[12]),
    ("T2 Row 5", (845, 810, 685, 102), results[13]),
    ("Takeaway Bar", (50, 975, 1500, 175), results[14])
]

print("=== CHECKING REAL CHROMIUM PADDINGS >= 16.0px ===")
all_pass = True
for name, rect, res in cards:
    if rect is None:
        continue
    rx, ry, rw, rh = rect
    bx, by, bw, bh = res["x"], res["y"], res["w"], res["h"]
    r_right = rx + rw
    r_bottom = ry + rh
    b_right = bx + bw
    b_bottom = by + bh
    
    pad_left = bx - rx
    pad_right = r_right - b_right
    pad_top = by - ry
    pad_bottom = r_bottom - b_bottom
    
    ok = (pad_left >= 16.0 and pad_right >= 16.0 and pad_top >= 16.0 and pad_bottom >= 16.0)
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"[{status}] {name:15s} | L={pad_left:5.1f}, R={pad_right:5.1f}, T={pad_top:5.1f}, B={pad_bottom:5.1f}")

assert all_pass, "Some padding failed!"
print("\nALL 14 CARDS HAVE REAL CHROMIUM PADDINGS >= 16.0px (PASS)")
