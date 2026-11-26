from playwright.sync_api import sync_playwright

html = """
<!DOCTYPE html>
<html>
<body>
<svg width="1600" height="200" xmlns="http://www.w3.org/2000/svg">
  <text id="t1" x="800" y="60" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">TTFB = time_starttransfer = DNS + connect + TLS + server think time + one RTT; time_total adds the body transfer</text>
</svg>
</body>
</html>
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html)
    b1 = page.locator("#t1").bounding_box()
    print("bbox of timing strip on 1 line:", b1)
    browser.close()
