from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content('''
        <svg xmlns="http://www.w3.org/2000/svg" width="1600" height="400">
            <rect id="card" x="56" y="50" width="708" height="56" fill="white" />
            <text id="txt" font-family="monospace" font-size="24" font-weight="bold">
                <tspan x="180" y="85">~/.ansible.cfg</tspan>
            </text>
        </svg>
    ''')
    cr = page.evaluate('document.getElementById("card").getBoundingClientRect()')
    tr = page.evaluate('document.getElementById("txt").getBoundingClientRect()')
    padT = tr['top'] - cr['top']
    padB = cr['bottom'] - tr['bottom']
    print(f"Card height=56: padTop={padT:.1f}, padBottom={padB:.1f}")
    browser.close()
