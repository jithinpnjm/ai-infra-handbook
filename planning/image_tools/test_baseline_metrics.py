from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content('''
        <svg xmlns="http://www.w3.org/2000/svg" width="1600" height="200">
            <text id="t1" x="100" y="50" font-family="sans-serif" font-size="24">Test single line</text>
        </svg>
    ''')
    r = page.evaluate('document.getElementById("t1").getBoundingClientRect()')
    print(f"y=50, fs=24: top={r['top']}, bottom={r['bottom']}, height={r['height']}")
    print(f"ascender = 50 - top = {50 - r['top']}")
    print(f"descender = bottom - 50 = {r['bottom'] - 50}")
    browser.close()
