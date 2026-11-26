#!/usr/bin/env python3
import pathlib
from playwright.sync_api import sync_playwright

test_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">
  <text id="t1" x="0" y="50" font-family="sans-serif" font-size="24">all GPUs present, driver and CUDA versions, memory,</text>
  <text id="t2" x="0" y="100" font-family="sans-serif" font-size="24">processes, power draw versus cap, temperature,</text>
  <text id="t3" x="0" y="150" font-family="sans-serif" font-size="24">throttle reasons (nvidia-smi -q -d PERFORMANCE)</text>
</svg>"""

pathlib.Path("test_actual_widths.svg").write_text(test_svg)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': 1600, 'height': 1200})
    page.goto('file://' + str(pathlib.Path('test_actual_widths.svg').resolve()))
    
    data = page.evaluate('''() => {
        return {
            w1: document.querySelector('#t1').getBBox().width,
            w2: document.querySelector('#t2').getBBox().width,
            w3: document.querySelector('#t3').getBBox().width,
        };
    }''')
    browser.close()

print(f"Actual widths in Chromium:")
print(f"w1: {data['w1']:.1f} px")
print(f"w2: {data['w2']:.1f} px")
print(f"w3: {data['w3']:.1f} px")
