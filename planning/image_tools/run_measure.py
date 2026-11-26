import subprocess
import json
import os

js_script = """
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1020 } });
  await page.goto('file://' + process.cwd() + '/test_final.svg');

  const results = await page.evaluate(() => {
    const textEls = Array.from(document.querySelectorAll('text'));
    return textEls.map(el => {
      const bbox = el.getBBox();
      const tspans = Array.from(el.querySelectorAll('tspan')).map(t => {
        return {
          text: t.textContent,
          bbox: t.getBBox()
        };
      });
      return {
        text: el.textContent.replace(/\\s+/g, ' ').trim(),
        bbox: { x: bbox.x, y: bbox.y, width: bbox.width, height: bbox.height },
        tspans: tspans
      };
    });
  });

  console.log(JSON.stringify(results, null, 2));
  await browser.close();
})();
"""

with open("measure.js", "w") as f:
    f.write(js_script)

res = subprocess.run(["node", "measure.js"], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)
