import asyncio
from playwright.async_api import async_playwright
import pathlib

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_path = pathlib.Path("candidate_final.svg").resolve()
        await page.goto(f"file://{svg_path}")
        
        # Evaluate bboxes
        data = await page.evaluate('''() => {
            const getBox = id => {
                const el = document.getElementById(id);
                return el.querySelector('rect, polygon').getBBox();
            };
            
            const getText = id => {
                const el = document.getElementById(id);
                const t = el.querySelector('text:last-of-type');
                return t.getBBox();
            };
            
            const checks = [
                { id: 'stage-1', name: 'Stage 1' },
                { id: 'stage-2', name: 'Stage 2' },
                { id: 'task-1', name: 'Task 1' },
                { id: 'task-2', name: 'Task 2' },
                { id: 'task-3', name: 'Task 3' },
                { id: 'task-4', name: 'Task 4' },
                { id: 'stage-3', name: 'Stage 3' },
                { id: 'stage-4', name: 'Stage 4' },
                { id: 'stage-5', name: 'Stage 5' }
            ];
            
            return checks.map(c => {
                const b = getBox(c.id);
                const t = getText(c.id);
                return {
                    name: c.name,
                    pad_left: t.x - b.x,
                    pad_right: (b.x + b.width) - (t.x + t.width),
                    pad_top: t.y - b.y,
                    pad_bottom: (b.y + b.height) - (t.y + t.height)
                };
            });
        }''')
        
        print("=== Bounding Box Paddings (must all be >= 16px) ===")
        all_pass = True
        for c in data:
            min_pad = min(c['pad_left'], c['pad_right'], c['pad_top'], c['pad_bottom'])
            ok = min_pad >= 16.0
            if not ok:
                all_pass = False
            print(f"[{'PASS' if ok else 'FAIL'}] {c['name']:8s}: L={c['pad_left']:5.1f}, R={c['pad_right']:5.1f}, T={c['pad_top']:5.1f}, B={c['pad_bottom']:5.1f} (min={min_pad:5.1f})")
            
        await browser.close()
        assert all_pass, "Some box paddings < 16px!"
        print("\nALL BOX PADDINGS >= 16px! (PASS)")

asyncio.run(main())
