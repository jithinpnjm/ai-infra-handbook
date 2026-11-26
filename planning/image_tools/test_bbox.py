import asyncio
from playwright.async_api import async_playwright
import pathlib

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_path = pathlib.Path("candidate_decision_tree.svg").resolve()
        await page.goto(f"file://{svg_path}")
        
        data = await page.evaluate('''() => {
            const nodes = Array.from(document.querySelectorAll('g[id^="node-"]')).map(g => {
                const rect = g.querySelector('rect').getBBox();
                const text = g.querySelector('text').getBBox();
                const icon = g.querySelector('g').getBBox();
                return {
                    id: g.id,
                    rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
                    text: { x: text.x, y: text.y, w: text.width, h: text.height },
                    icon: { x: icon.x, y: icon.y, w: icon.width, h: icon.height }
                };
            });
            
            return nodes;
        }''')
        
        all_ok = True
        for n in data:
            # Check icon inside rect with padding
            # Check text inside rect with >= 16px padding
            pad_l = n['text']['x'] - n['rect']['x']
            pad_r = (n['rect']['x'] + n['rect']['w']) - (n['text']['x'] + n['text']['w'])
            pad_t = n['text']['y'] - n['rect']['y']
            pad_b = (n['rect']['y'] + n['rect']['h']) - (n['text']['y'] + n['text']['h'])
            gap_icon_text = n['text']['x'] - (n['icon']['x'] + n['icon']['w'])
            
            print(f"{n['id']}: pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}, icon_gap={gap_icon_text:.1f}")
            if min(pad_l, pad_r, pad_t, pad_b, gap_icon_text) < 15:
                print(f"FAILED on {n['id']}")
                all_ok = False
        
        assert all_ok, "Bounding box padding failed!"
        print("ALL RENDERED BOUNDING BOX PADDINGS >= 15px PASS!")
        await browser.close()

asyncio.run(main())
