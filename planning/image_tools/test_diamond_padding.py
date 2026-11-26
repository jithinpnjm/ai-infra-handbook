import asyncio
from playwright.async_api import async_playwright
import pathlib

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_path = pathlib.Path("candidate_final.svg").resolve()
        await page.goto(f"file://{svg_path}")
        
        data = await page.evaluate('''() => {
            const diaEl = document.getElementById('red-diamond');
            const poly = diaEl.querySelector('polygon');
            const t = diaEl.querySelector('text');
            const icon = diaEl.querySelector('g');
            
            const pb = poly.getBBox();
            const tb = t.getBBox();
            const ib = icon.getBBox();
            
            // Check tspans
            const tspans = Array.from(t.querySelectorAll('tspan')).map(tsp => {
                const b = tsp.getBBox();
                return {
                    text: tsp.textContent,
                    x: b.x,
                    y: b.y,
                    width: b.width,
                    height: b.height,
                    center_y: b.y + b.height / 2
                };
            });
            
            return {
                poly: { cx: pb.x + pb.width/2, cy: pb.y + pb.height/2, w: pb.width, h: pb.height },
                text: { x: tb.x, y: tb.y, w: tb.width, h: tb.height },
                icon: { x: ib.x, y: ib.y, w: ib.width, h: ib.height },
                tspans: tspans
            };
        }''')
        
        print("=== Diamond Geometry Check ===")
        poly = data['poly']
        print(f"Polygon center: ({poly['cx']}, {poly['cy']}), size: {poly['w']}x{poly['h']}")
        print(f"Icon: y in [{data['icon']['y']}..{data['icon']['y'] + data['icon']['h']}]")
        print(f"Text: y in [{data['text']['y']}..{data['text']['y'] + data['text']['h']}]")
        
        # Check that icon bottom < text top
        icon_bottom = data['icon']['y'] + data['icon']['h']
        text_top = data['text']['y']
        print(f"Gap between icon and text: {text_top - icon_bottom:.1f}px")
        assert text_top > icon_bottom, "Icon overlaps text!"
        
        # For each tspan, calculate distance to diamond boundary
        # Diamond equation: abs(x - cx)/(w/2) + abs(y - cy)/(h/2) <= 1
        for tsp in data['tspans']:
            cy = tsp['center_y']
            dy = abs(cy - poly['cy'])
            half_w_at_y = (poly['w'] / 2) * (1 - dy / (poly['h'] / 2))
            half_tw = tsp['width'] / 2
            pad = half_w_at_y - half_tw
            print(f"Tspan '{tsp['text']}': half_w_avail={half_w_at_y:.1f}, half_tw={half_tw:.1f}, pad={pad:.1f}px")
            assert pad >= 16.0, f"Diamond padding < 16px for '{tsp['text']}'"
            
        print("Diamond validation completely passed! (PASS)")
        await browser.close()

asyncio.run(main())
