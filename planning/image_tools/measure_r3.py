from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content('''
        <svg xmlns="http://www.w3.org/2000/svg" width="1600" height="200">
            <text id="r3" x="136" y="94" font-family="sans-serif" font-size="24">editing /etc/ansible changes behaviour between laptops and CI and is invisible to Git</text>
        </svg>
    ''')
    r = page.evaluate('document.getElementById("r3").getBoundingClientRect()')
    print(f"y=94: top={r['top']}, bottom={r['bottom']}, height={r['height']}")
    browser.close()
