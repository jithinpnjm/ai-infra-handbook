import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f'file://{os.path.abspath("test_perfect2.svg")}')
    
    issues = page.evaluate('''() => {
        const issues = [];
        
        // Check each node card in the host header
        const cards = [
            { id: 'host-card', rect: document.querySelector('#box-host-header ~ g:nth-of-type(1) rect'), text: document.querySelector('#box-host-header ~ g:nth-of-type(1) text') },
            { id: 'c1', rect: document.querySelector('#box-host-header ~ g:nth-of-type(2) rect'), text: document.querySelector('#box-host-header ~ g:nth-of-type(2) text') },
            { id: 'br0', rect: document.querySelector('#box-host-header ~ g:nth-of-type(3) rect'), text: document.querySelector('#box-host-header ~ g:nth-of-type(3) text') },
            { id: 'c2', rect: document.querySelector('#box-host-header ~ g:nth-of-type(4) rect'), text: document.querySelector('#box-host-header ~ g:nth-of-type(4) text') },
            { id: 'nic', rect: document.querySelector('#box-host-header ~ g:nth-of-type(5) rect'), text: document.querySelector('#box-host-header ~ g:nth-of-type(5) text') }
        ];

        cards.forEach(c => {
            if (!c.rect || !c.text) {
                issues.push(`Card ${c.id} missing elements`);
                return;
            }
            const br = c.rect.getBoundingClientRect();
            const tr = c.text.getBoundingClientRect();
            const padLeft = tr.left - br.left;
            const padRight = br.right - tr.right;
            const padTop = tr.top - br.top;
            const padBottom = br.bottom - tr.bottom;
            
            // Note: icon is on the left, so padRight is what matters for box edge fit
            if (padRight < 15.5) issues.push(`Card ${c.id} right padding violation: ${padRight.toFixed(1)}`);
            if (padTop < 15.5) issues.push(`Card ${c.id} top padding violation: ${padTop.toFixed(1)}`);
            if (padBottom < 15.5) issues.push(`Card ${c.id} bottom padding violation: ${padBottom.toFixed(1)}`);
        });

        return issues;
    }''')
    print('Card padding issues:', len(issues))
    for i in issues:
        print(' ', i)
