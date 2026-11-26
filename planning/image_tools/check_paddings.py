import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f'file://{os.path.abspath("test_perfect2.svg")}')
    
    padding_issues = page.evaluate('''() => {
        const issues = [];
        const checkPadding = (containerId, selector) => {
            const box = document.querySelector(containerId).getBoundingClientRect();
            const texts = document.querySelectorAll(selector);
            texts.forEach(t => {
                const tr = t.getBoundingClientRect();
                const padLeft = tr.left - box.left;
                const padRight = box.right - tr.right;
                const padTop = tr.top - box.top;
                const padBottom = box.bottom - tr.bottom;
                const txt = t.textContent.trim().slice(0, 25);
                
                if (padLeft < 15.5) issues.push(`${containerId} left padding violation: '${txt}' has padLeft ${padLeft.toFixed(1)}`);
                if (padRight < 15.5) issues.push(`${containerId} right padding violation: '${txt}' has padRight ${padRight.toFixed(1)}`);
                if (padTop < 15.5) issues.push(`${containerId} top padding violation: '${txt}' has padTop ${padTop.toFixed(1)}`);
                if (padBottom < 15.5) issues.push(`${containerId} bottom padding violation: '${txt}' has padBottom ${padBottom.toFixed(1)}`);
            });
        };

        checkPadding('#box-lane-1', '#lane-1 text, #lane-1 tspan');
        checkPadding('#box-lane-2', '#lane-2 text, #lane-2 tspan');
        checkPadding('#box-lane-3', '#lane-3 text, #lane-3 tspan');
        checkPadding('#box-footer', '#footer-notes text, #footer-notes tspan');
        checkPadding('#box-takeaway', '#bottom-bar text');

        return issues;
    }''')
    print('Padding issues count:', len(padding_issues))
    for pi in padding_issues:
        print('  Issue:', pi)
