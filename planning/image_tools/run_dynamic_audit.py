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
            const texts = [];
            for (const t of document.querySelectorAll("text")) {
                const b = t.getBBox();
                texts.push({
                    text: t.textContent.trim().replace(/\\s+/g, " "),
                    x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, bot: b.y + b.height
                });
            }
            const rects = [];
            for (const r of document.querySelectorAll("rect")) {
                const b = r.getBBox();
                rects.push({
                    x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, bot: b.y + b.height
                });
            }
            return { texts, rects };
        }""")
        await b.close()
        
        # Match each text with its containing box
        print("--- Checking All Text Elements Against Containers ---")
        for t in data["texts"]:
            # Find smallest containing or surrounding rect
            containing = [r for r in data["rects"] if r['x'] <= t['x'] and r['r'] >= t['r'] and r['y'] <= t['y'] and r['bot'] >= t['bot']]
            if containing:
                # pick smallest by area
                c = min(containing, key=lambda r: r['w'] * r['h'])
                pad_l = t['x'] - c['x']
                pad_r = c['r'] - t['r']
                pad_t = t['y'] - c['y']
                pad_b = c['bot'] - t['bot']
                min_pad = min(pad_l, pad_r, pad_t, pad_b)
                status = "PASS" if min_pad >= 16.0 else f"FAIL (min={min_pad:.1f}px)"
                print(f"Text '{t['text'][:35]:35s}': L={pad_l:4.1f}, R={pad_r:4.1f}, T={pad_t:4.1f}, B={pad_b:4.1f} -> {status}")
            else:
                # Might be inside diamond or an arrow label
                print(f"Text '{t['text'][:35]:35s}': not in rect (diamond or arrow label)")

        # Specifically check diamonds:
        # Left diamond: cx=395, cy=320, rx=250, ry=72
        # Text: "a succeeds?" (left)
        t_left_a = [t for t in data["texts"] if t["text"] == "a succeeds?"][0]
        pts_la = [(t_left_a['x'], t_left_a['y']), (t_left_a['r'], t_left_a['y']), (t_left_a['x'], t_left_a['bot']), (t_left_a['r'], t_left_a['bot']),
                  (285, 302), (321, 302), (285, 338), (321, 338)]
        d_la = min(dist_to_diamond(px, py, 395, 320, 250, 72) for px, py in pts_la)
        print(f"\nLeft Diamond: min_dist = {d_la:.2f}px ({'PASS' if d_la>=16 else 'FAIL'})")

        # Right diamond 1: cx=1025, cy=320, rx=240, ry=80
        t_r1 = [t for t in data["texts"] if t["text"] == "a succeeds?"][1]
        pts_r1 = [(t_r1['x'], t_r1['y']), (t_r1['r'], t_r1['y']), (t_r1['x'], t_r1['bot']), (t_r1['r'], t_r1['bot']),
                  (910, 304), (942, 304), (910, 336), (942, 336)]
        d_r1 = min(dist_to_diamond(px, py, 1025, 320, 240, 80) for px, py in pts_r1)
        print(f"Right Diamond 1: min_dist = {d_r1:.2f}px ({'PASS' if d_r1>=16 else 'FAIL'})")

        # Right diamond 2: cx=1025, cy=604, rx=240, ry=86
        t_r2 = [t for t in data["texts"] if t["text"] == "b succeeded?"][0]
        pts_r2 = [(t_r2['x'], t_r2['y']), (t_r2['r'], t_r2['y']), (t_r2['x'], t_r2['bot']), (t_r2['r'], t_r2['bot']),
                  (895, 588), (927, 588), (895, 620), (927, 620)]
        d_r2 = min(dist_to_diamond(px, py, 1025, 604, 240, 86) for px, py in pts_r2)
        print(f"Right Diamond 2: min_dist = {d_r2:.2f}px ({'PASS' if d_r2>=16 else 'FAIL'})")

        # Also check box c (right) clearance to warning icon
        # icon: translate(1288, 442), size 48x42 -> x in [1288, 1336]
        # title c and secondary text start at 1360
        gap_icon_text = 1360 - 1336
        print(f"Box c right: gap between icon and text = {gap_icon_text:.1f}px ({'PASS' if gap_icon_text>=16 else 'FAIL'})")

asyncio.run(check())
