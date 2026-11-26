import re
import asyncio
from playwright.async_api import async_playwright
import pathlib

# Let's adjust title_y by +1px for all cards:
# Rung 1: y=136..230. title_y=179, cmd_y=208
# Rung 2: y=270..364. title_y=313, cmd_y=342
# Rung 3: y=404..498. title_y=447, cmd_y=476
# Rung 4: y=538..660. title_y=581, cmd_y=610, tspan_dy=28
# Rung 5: y=701..795. title_y=744, cmd_y=773
# Rung 6: y=836..930. title_y=879, cmd_y=908
# Rung 7: y=971..1065. title_y=1014, cmd_y=1043

svg_text = open("perfect_service_path.svg").read()
svg_text = svg_text.replace('y="178"', 'y="179"')
svg_text = svg_text.replace('y="312"', 'y="313"')
svg_text = svg_text.replace('y="446"', 'y="447"')
svg_text = svg_text.replace('y="580"', 'y="581"')
svg_text = svg_text.replace('y="743"', 'y="744"')
svg_text = svg_text.replace('y="878"', 'y="879"')
svg_text = svg_text.replace('y="1013"', 'y="1014"')

with open("perfect_service_path.svg", "w") as f:
    f.write(svg_text)

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        await page.goto(f'file://{pathlib.Path("perfect_service_path.svg").resolve()}')
        
        checks = [
            ("Rung 1", "#rung-1", 2, 3),
            ("Rung 2", "#rung-2", 2, 3),
            ("Rung 3", "#rung-3", 2, 3),
            ("Rung 4", "#rung-4", 2, 3),
            ("Rung 5", "#rung-5", 2, 3),
            ("Rung 6", "#rung-6", 2, 3),
            ("Rung 7", "#rung-7", 2, 3),
        ]
        
        for name, sel, t_idx, c_idx in checks:
            r_box = await (await page.query_selector(f"{sel} rect")).bounding_box()
            t_box = await (await page.query_selector(f"{sel} text:nth-of-type({t_idx})")).bounding_box()
            c_box = await (await page.query_selector(f"{sel} text:nth-of-type({c_idx})")).bounding_box()
            
            pad_l = min(t_box['x'], c_box['x']) - r_box['x']
            pad_r = (r_box['x'] + r_box['width']) - max(t_box['x'] + t_box['width'], c_box['x'] + c_box['width'])
            pad_t = t_box['y'] - r_box['y']
            pad_b = (r_box['y'] + r_box['height']) - (c_box['y'] + c_box['height'])
            
            print(f"{name:8s} | pad_l={pad_l:5.1f}, pad_r={pad_r:5.1f}, pad_t={pad_t:5.1f}, pad_b={pad_b:5.1f}")
            assert min(pad_l, pad_r, pad_t, pad_b) >= 16.0, f"{name} failed padding >= 16.0!"

        # Small Box:
        sb_r = await (await page.query_selector("#small-box rect")).bounding_box()
        sb_t = await (await page.query_selector("#small-box text")).bounding_box()
        pad_sb_l = sb_t['x'] - sb_r['x']
        pad_sb_r = (sb_r['x'] + sb_r['width']) - (sb_t['x'] + sb_t['width'])
        pad_sb_t = sb_t['y'] - sb_r['y']
        pad_sb_b = (sb_r['y'] + sb_r['height']) - (sb_t['y'] + sb_t['height'])
        print(f"Small Box | pad_l={pad_sb_l:5.1f}, pad_r={pad_sb_r:5.1f}, pad_t={pad_sb_t:5.1f}, pad_b={pad_sb_b:5.1f}")
        assert min(pad_sb_l, pad_sb_r, pad_sb_t, pad_sb_b) >= 16.0

        # Orange Callout:
        oc_r = await (await page.query_selector("#orange-callout rect")).bounding_box()
        oc_t = await (await page.query_selector("#orange-callout text")).bounding_box()
        pad_oc_l = oc_t['x'] - oc_r['x']
        pad_oc_r = (oc_r['x'] + oc_r['width']) - (oc_t['x'] + oc_t['width'])
        pad_oc_t = oc_t['y'] - oc_r['y']
        pad_oc_b = (oc_r['y'] + oc_r['height']) - (oc_t['y'] + oc_t['height'])
        print(f"Callout   | pad_l={pad_oc_l:5.1f}, pad_r={pad_oc_r:5.1f}, pad_t={pad_oc_t:5.1f}, pad_b={pad_oc_b:5.1f}")
        assert min(pad_oc_l, pad_oc_r, pad_oc_t, pad_oc_b) >= 16.0

        await browser.close()
        print("\nALL PLAYWRIGHT PADDING CHECKS PASSED >= 16.0 PX!")

asyncio.run(check())
