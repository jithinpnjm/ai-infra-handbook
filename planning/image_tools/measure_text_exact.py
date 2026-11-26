from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content('''
        <svg xmlns="http://www.w3.org/2000/svg" width="1600" height="400">
            <text id="t1" font-family="sans-serif" font-size="24">
                <tspan x="136" y="40">ansible-config dump --only-changed shows only what you changed; </tspan>
                <tspan x="136" y="68">ansible-config list shows every setting with its default; </tspan>
                <tspan x="136" y="96">ansible --version shows the config file in use</tspan>
            </text>
        </svg>
    ''')
    rect = page.evaluate('document.getElementById("t1").getBoundingClientRect()')
    print(f"Top: {rect['top']}, Bottom: {rect['bottom']}, Height: {rect['height']}")
    tspans = page.evaluate('''() => {
        return Array.from(document.querySelectorAll('tspan')).map(t => {
            const r = t.getBoundingClientRect();
            return {top: r.top, bottom: r.bottom, height: r.height};
        });
    }''')
    for i, ts in enumerate(tspans):
        print(f"Tspan {i+1}: top={ts['top']}, bottom={ts['bottom']}, h={ts['height']}")
    browser.close()
