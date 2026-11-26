import asyncio
from playwright.async_api import async_playwright
import pathlib

svg_test = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" width="1600" height="1100">
  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>
  <rect width="1600" height="1100" fill="#f5f8f5" />
  
  <!-- Test diamond with icon and text -->
  <g id="test-dia" transform="translate(410, 310)">
    <!-- Diamond cx=0, cy=0, w=380, h=160 -->
    <polygon points="0,-80 190,0 0,80 -190,0" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Icon centered above text: cy=-28 -->
    <g transform="translate(-20, -52)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="20" cy="20" r="16" />
      <path d="M 16 14 C 16 10, 24 10, 24 16 C 24 20, 20 20, 20 24" />
      <circle cx="20" cy="29" r="1.5" fill="#207448" />
    </g>
    <!-- Text centered below icon: y=42 -->
    <text x="0" y="42" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">a succeeds?</text>
  </g>
</svg>'''

pathlib.Path("test_dia_render.svg").write_text(svg_test)

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1100})
        await page.goto(f"file://{pathlib.Path('test_dia_render.svg').resolve()}")
        data = await page.evaluate('''() => {
            const dia = document.getElementById('test-dia');
            const pb = dia.querySelector('polygon').getBBox();
            const tb = dia.querySelector('text').getBBox();
            const ib = dia.querySelector('g').getBBox();
            return {
                poly: { x: pb.x, y: pb.y, width: pb.width, height: pb.height },
                text: { x: tb.x, y: tb.y, width: tb.width, height: tb.height },
                icon: { x: ib.x, y: ib.y, width: ib.width, height: ib.height }
            };
        }''')
        print("Diamond data:", data)
        # Check text bounds inside diamond
        # Diamond equation: |x|/190 + |y|/80 <= 1
        corners = [
            (data['text']['x'], data['text']['y']),
            (data['text']['x'] + data['text']['width'], data['text']['y']),
            (data['text']['x'], data['text']['y'] + data['text']['height']),
            (data['text']['x'] + data['text']['width'], data['text']['y'] + data['text']['height']),
        ]
        print("Text corners relative to center:")
        for x, y in corners:
            dist = abs(x)/190 + abs(y)/80
            print(f"  ({x:.1f}, {y:.1f}) -> dist={dist:.3f}")
        
        # Check clearance between icon and text
        icon_bottom = data['icon']['y'] + data['icon']['height']
        text_top = data['text']['y']
        gap = text_top - icon_bottom
        print(f"Gap between icon and text: {gap:.1f}px")

asyncio.run(check())
