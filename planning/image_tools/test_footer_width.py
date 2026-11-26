#!/usr/bin/env python3
import pathlib
from playwright.sync_api import sync_playwright

footer_text = "All of them are read-only; option names vary by driver and DCGM version, so check the flags on your own system"
bar_text = "Add these to the host checklist when you are on a GPU node"

test_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">
  <text id="tf" x="0" y="50" font-family="sans-serif" font-size="24">{footer_text}</text>
  <text id="tb" x="0" y="100" font-family="sans-serif" font-size="26" font-weight="bold">{bar_text}</text>
</svg>"""

pathlib.Path("test_footer_width.svg").write_text(test_svg)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': 1600, 'height': 1200})
    page.goto('file://' + str(pathlib.Path('test_footer_width.svg').resolve()))
    
    data = page.evaluate('''() => {
        return {
            wf: document.querySelector('#tf').getBBox().width,
            wb: document.querySelector('#tb').getBBox().width,
        };
    }''')
    browser.close()

print(f"Footer text width in Chromium: {data['wf']:.1f} px")
print(f"Bar text width in Chromium: {data['wb']:.1f} px")
