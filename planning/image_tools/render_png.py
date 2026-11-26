import os
from playwright.sync_api import sync_playwright

with open("test_candidate_dns.svg") as f:
    svg_data = f.read()

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1100})
    page.set_content(f"""<!DOCTYPE html>
<html>
<head><style>body {{ margin: 0; padding: 0; background: #f5f8f5; }}</style></head>
<body>{svg_data}</body>
</html>""")
    page.locator("svg").screenshot(path="test_candidate_dns.png")
    print("Saved test_candidate_dns.png successfully!")
