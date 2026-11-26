"""Measure exact title width and bounding box."""
from playwright.sync_api import sync_playwright

html = '''
<!DOCTYPE html>
<html>
<body>
<svg width="1600" height="200" xmlns="http://www.w3.org/2000/svg">
  <text id="t1" x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Typical operator reconcile structure</text>
  <text id="t_left" x="60" y="65" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Typical operator reconcile structure</text>
</svg>
</body>
</html>
'''

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html)
    b1 = page.locator("#t1").bounding_box()
    b2 = page.locator("#t_left").bounding_box()
    print("Centered Title bbox:", b1)
    print("Left-aligned Title bbox:", b2)
    browser.close()
