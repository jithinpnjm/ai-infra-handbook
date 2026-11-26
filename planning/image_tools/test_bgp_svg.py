#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def check_svg(svg_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        await page.goto(f"file://{svg_path}")
        
        # Check title
        title = await page.title()
        print(f"Page title: {title}")
        
        # Check all text elements
        texts = await page.evaluate('''() => {
            const elements = Array.from(document.querySelectorAll('text, tspan'));
            return elements.map(el => {
                const rect = el.getBoundingClientRect();
                const computed = window.getComputedStyle(el);
                return {
                    tag: el.tagName,
                    text: el.textContent,
                    fontSize: parseFloat(computed.fontSize),
                    fontFamily: computed.fontFamily,
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    right: rect.right,
                    bottom: rect.bottom
                };
            });
        }''')
        
        print(f"Total text/tspan elements: {len(texts)}")
        font_errors = [t for t in texts if t['fontSize'] < 23.9]
        if font_errors:
            print(f"FONT ERRORS (< 24px): {font_errors}")
        else:
            print("SUCCESS: All font sizes >= 24px")
            
        bounds_errors = [t for t in texts if t['right'] > 1560 or t['x'] < 40]
        if bounds_errors:
            print(f"BOUNDS ERRORS: {bounds_errors}")
        else:
            print("SUCCESS: All text within 40px margins (40 to 1560)")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_svg("/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook/docs/part-02-networking/img/n15-attrs.svg"))
