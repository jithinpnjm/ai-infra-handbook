from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content('''
        <svg xmlns="http://www.w3.org/2000/svg" width="1600" height="400">
            <text id="card2" font-family="sans-serif" font-size="24">
                <tspan x="186" y="34" font-family="monospace" font-weight="bold">./ansible.cfg </tspan>
                <tspan x="186" y="62" font-family="sans-serif">in the current directory </tspan>
                <tspan x="72" y="92">(honoured only if it is not world-writable: a </tspan>
                <tspan x="72" y="120">folder any user can change cannot be trusted)</tspan>
            </text>
        </svg>
    ''')
    rect = page.evaluate('document.getElementById("card2").getBoundingClientRect()')
    print(f"Top: {rect['top']}, Bottom: {rect['bottom']}, Height: {rect['height']}")
    tspans = page.evaluate('''() => {
        return Array.from(document.querySelectorAll('tspan')).map(t => {
            const r = t.getBoundingClientRect();
            return {text: t.textContent.slice(0, 25), top: r.top, bottom: r.bottom, h: r.height};
        });
    }''')
    for ts in tspans:
        print(f"'{ts['text']}': top={ts['top']}, bottom={ts['bottom']}, h={ts['h']}")
    browser.close()
