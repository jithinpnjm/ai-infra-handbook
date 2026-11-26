from playwright.sync_api import sync_playwright

html = """
<!DOCTYPE html>
<html>
<body>
<svg width="1600" height="200" xmlns="http://www.w3.org/2000/svg">
  <text id="t1" x="800" y="50" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="800" dy="0">Redirects 301, 302, 307, 308 trigger a new request, maybe a new connection: curl -L; proxies, CDNs </tspan>
    <tspan x="800" dy="32">and load balancers may terminate TLS, rewrite headers such as X-Forwarded-For, cache and retry</tspan>
  </text>
</svg>
</body>
</html>
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(html)
    b1 = page.locator("#t1").bounding_box()
    print("bbox of redirects on 2 lines:", b1)
    browser.close()
