#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import pathlib

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_url = pathlib.Path("candidate_gpu_checklist.svg").resolve().as_uri()
        await page.goto(svg_url)
        
        # Evaluate bounding boxes of all text elements
        texts = await page.eval_on_selector_all("text", """elements => {
            return elements.map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    text: el.textContent.trim(),
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    right: rect.right,
                    bottom: rect.bottom
                };
            });
        }""")
        
        # Evaluate bounding boxes of all rect elements
        rects = await page.eval_on_selector_all("rect", """elements => {
            return elements.map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    fill: el.getAttribute('fill'),
                    stroke: el.getAttribute('stroke'),
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                };
            });
        }""")

        await browser.close()
        
        print(f"\nRendered bounding box check:")
        # Check that no text overflows 1600x1200 canvas
        for t in texts:
            if t['x'] < 40 or t['right'] > 1560:
                # Title might be outside 40..1560? Let's check
                print(f"Warning: Text '{t['text'][:30]}' x={t['x']:.1f}, right={t['right']:.1f}")
            assert t['x'] >= 0 and t['right'] <= 1600, f"Overflow canvas: {t}"
            assert t['y'] >= 0 and t['bottom'] <= 1200, f"Overflow canvas: {t}"

        print("All rendered texts fit inside 1600x1200!")

asyncio.run(test())
