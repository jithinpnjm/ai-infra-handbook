#!/usr/bin/env python3
import pathlib
from playwright.sync_api import sync_playwright

test_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">
  <rect x="0" y="0" width="1600" height="1200" fill="#f5f8f5"/>
  <rect id="r11" x="40" y="145" width="1520" height="102" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text id="t11" x="650" y="177" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="650" dy="0">all GPUs present, driver and CUDA versions, memory, </tspan>
    <tspan x="650" dy="23">processes, power draw versus cap, temperature, </tspan>
    <tspan x="650" dy="23">throttle reasons (nvidia-smi -q -d PERFORMANCE)</tspan>
  </text>
</svg>"""

pathlib.Path("test_pad_measure.svg").write_text(test_svg)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': 1600, 'height': 1200})
    page.goto('file://' + str(pathlib.Path('test_pad_measure.svg').resolve()))
    
    data = page.evaluate('''() => {
        const rBox = document.querySelector('#r11').getBBox();
        const tBox = document.querySelector('#t11').getBBox();
        return {
            r: { x: rBox.x, y: rBox.y, width: rBox.width, height: rBox.height },
            t: { x: tBox.x, y: tBox.y, width: tBox.width, height: tBox.height }
        };
    }''')
    browser.close()

r = data['r']
t = data['t']
print(f"Rect bbox: x={r['x']}, y={r['y']}, w={r['width']}, h={r['height']}")
print(f"Text bbox: x={t['x']}, y={t['y']}, w={t['width']}, h={t['height']}")

pad_left = t['x'] - r['x']
pad_right = (r['x'] + r['width']) - (t['x'] + t['width'])
pad_top = t['y'] - r['y']
pad_bottom = (r['y'] + r['height']) - (t['y'] + t['height'])

print(f"Paddings: L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f}")
print(f"Min padding: {min(pad_left, pad_right, pad_top, pad_bottom):.1f}")
