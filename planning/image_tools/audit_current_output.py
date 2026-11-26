import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f'file://{os.path.abspath("test_perfect.svg")}')
    
    issues = page.evaluate('''() => {
        const issues = [];
        const texts = Array.from(document.querySelectorAll('text, tspan')).filter(t => t.textContent.trim().length > 0);
        
        texts.forEach(t => {
            const tr = t.getBoundingClientRect();
            const txt = t.textContent.trim().slice(0, 30);
            if (tr.left < 39.5) issues.push(`Canvas left margin: '${txt}' at ${tr.left}`);
            if (tr.right > 1560.5) issues.push(`Canvas right margin: '${txt}' at ${tr.right}`);
            if (tr.top < 39.5) issues.push(`Canvas top margin: '${txt}' at ${tr.top}`);
            if (tr.bottom > 1160.5) issues.push(`Canvas bottom margin: '${txt}' at ${tr.bottom}`);
            
            const fs = parseFloat(window.getComputedStyle(t).fontSize);
            if (fs < 23.5) issues.push(`Font size < 24px: '${txt}' has ${fs}`);
        });

        // Box padding checks
        const checkPadding = (boxSelector, textSelector) => {
            const box = document.querySelector(boxSelector).getBoundingClientRect();
            document.querySelectorAll(textSelector).forEach(t => {
                const tr = t.getBoundingClientRect();
                const padLeft = tr.left - box.left;
                const padRight = box.right - tr.right;
                const padTop = tr.top - box.top;
                const padBottom = box.bottom - tr.bottom;
                const txt = t.textContent.trim().slice(0, 30);
                if (padLeft < 15.5) issues.push(`${boxSelector} padLeft: '${txt}' = ${padLeft.toFixed(1)}`);
                if (padRight < 15.5) issues.push(`${boxSelector} padRight: '${txt}' = ${padRight.toFixed(1)}`);
                if (padTop < 15.5) issues.push(`${boxSelector} padTop: '${txt}' = ${padTop.toFixed(1)}`);
                if (padBottom < 15.5) issues.push(`${boxSelector} padBottom: '${txt}' = ${padBottom.toFixed(1)}`);
            });
        };

        checkPadding('#box-host-header', '#box-host-header ~ g text');
        checkPadding('#box-lane-1', '#lane-1 text, #lane-1 tspan');
        checkPadding('#box-lane-2', '#lane-2 text, #lane-2 tspan');
        checkPadding('#box-lane-3', '#lane-3 text, #lane-3 tspan');
        checkPadding('#box-footer', '#footer-notes text, #footer-notes tspan');
        checkPadding('#box-takeaway', '#bottom-bar text');

        return issues;
    }''')
    print('Issues count:', len(issues))
    for i in issues:
        print(' ', i)
