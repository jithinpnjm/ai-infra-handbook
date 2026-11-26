from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content('''
        <svg xmlns="http://www.w3.org/2000/svg" width="1600" height="200">
            <text id="t1" font-family="sans-serif" font-size="24">a folder any user can change cannot be trusted)</text>
            <text id="t2" font-family="sans-serif" font-size="24">(honoured only if it is not world-writable: a folder any user can change cannot be trusted)</text>
        </svg>
    ''')
    w1 = page.evaluate('document.getElementById("t1").getBoundingClientRect().width')
    w2 = page.evaluate('document.getElementById("t2").getBoundingClientRect().width')
    print(f"w1: {w1:.1f} px")
    print(f"w2: {w2:.1f} px")
    browser.close()
