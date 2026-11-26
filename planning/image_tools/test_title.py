from playwright.sync_api import sync_playwright

test_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <text id="t1" x="800" y="65" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Three paths from a container: to a neighbour,</text>
  <text id="t2" x="800" y="115" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">to the Internet, and from outside to a published port</text>
  <text id="t2_short" x="800" y="165" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">to the Internet, and to a published port</text>
  <text id="t2_outside" x="800" y="215" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">to the Internet, and outside to a published port</text>
</svg>"""

with open("test_title_width.svg", "w") as f:
    f.write(test_svg)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f"file:///Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook/planning/image_tools/test_title_width.svg")
    for tid in ["t1", "t2", "t2_short", "t2_outside"]:
        box = page.evaluate(f"document.getElementById('{tid}').getBoundingClientRect()")
        print(f"{tid}: width={box['width']:.1f}, left={box['left']:.1f}, right={box['right']:.1f}")
