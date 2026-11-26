import asyncio
from playwright.async_api import async_playwright
import os

boxes = {
    # text_idx: (box_x, box_y, box_w, box_h, name)
    2: (40, 165, 420, 280, "Left box"),
    3: (40, 485, 420, 395, "Second box Fleet"),
    5: (720, 185, 400, 80, "Card 1"),
    6: (1140, 185, 400, 80, "Card 5"),
    7: (720, 280, 400, 85, "Card 2"),
    8: (1140, 280, 400, 85, "Card 3"),
    9: (720, 380, 400, 85, "Card 4"),
    10: (1140, 380, 400, 85, "Card 7"),
    11: (720, 480, 400, 130, "Card 6"),
    12: (1140, 480, 400, 130, "Card 8"),
    13: (720, 625, 820, 150, "Card 9"),
    14: (720, 790, 820, 75, "Card 10"),
    15: (40, 920, 1520, 140, "Footnote"),
    16: (40, 1100, 1520, 60, "Bottom bar")
}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        cwd = os.getcwd()
        svg_url = f'file://{cwd}/test_generated.svg'
        await page.goto(svg_url)
        
        text_elems = await page.query_selector_all('text')
        all_passed = True
        for i, el in enumerate(text_elems, 1):
            if i not in boxes:
                continue
            bx, by, bw, bh, name = boxes[i]
            tb = await el.bounding_box()
            pad_left = tb['x'] - bx
            pad_right = (bx + bw) - (tb['x'] + tb['width'])
            pad_top = tb['y'] - by
            pad_bottom = (by + bh) - (tb['y'] + tb['height'])
            
            min_pad = min(pad_left, pad_right, pad_top, pad_bottom)
            ok = min_pad >= 16.0
            if not ok:
                all_passed = False
            status = "PASS" if ok else "FAIL"
            print(f"[{status}] {name:20s}: L={pad_left:4.1f}, R={pad_right:4.1f}, T={pad_top:4.1f}, B={pad_bottom:4.1f} | min={min_pad:4.1f} px")
            
        await browser.close()
        return all_passed

passed = asyncio.run(main())
print("Result:", passed)
