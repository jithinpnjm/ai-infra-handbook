#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import os

async def check():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1600, "height": 1180})
        svg_abs = os.path.abspath("flamegraph_perfect.svg")
        await page.goto("file://" + svg_abs)
        
        # Check text bboxes against their containers
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
        
        print("=== TEXT BOUNDING BOXES ===")
        for d in data:
            print(f"{d['text'][:40]:40s} | x={d['x']:6.1f}..{d['r']:6.1f} (w={d['w']:5.1f}) | y={d['y']:6.1f}..{d['bot']:6.1f} (h={d['h']:4.1f})")
            
        await b.close()

asyncio.run(check())
