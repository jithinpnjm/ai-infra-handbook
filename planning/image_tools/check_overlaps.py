import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f'file://{os.path.abspath("test_perfect2.svg")}')
    
    overlaps = page.evaluate('''() => {
        const issues = [];
        const texts = Array.from(document.querySelectorAll('text, tspan')).filter(t => t.textContent.trim().length > 0);
        const arrows = Array.from(document.querySelectorAll('line[marker-end]'));
        const iconGroups = Array.from(document.querySelectorAll('g[stroke="#207448"], g[stroke="#db8129"]'));
        
        // Check text vs arrows
        texts.forEach(t => {
            const tr = t.getBoundingClientRect();
            arrows.forEach(a => {
                const x1 = parseFloat(a.getAttribute('x1'));
                const y1 = parseFloat(a.getAttribute('y1'));
                const x2 = parseFloat(a.getAttribute('x2'));
                const y2 = parseFloat(a.getAttribute('y2'));
                const minX = Math.min(x1, x2);
                const maxX = Math.max(x1, x2);
                const minY = Math.min(y1, y2) - 8;
                const maxY = Math.max(y1, y2) + 8;
                
                // intersection check
                if (!(tr.right < minX || tr.left > maxX || tr.bottom < minY || tr.top > maxY)) {
                    issues.push(`Text '${t.textContent.trim().slice(0, 25)}' overlaps arrow from (${x1},${y1}) to (${x2},${y2})`);
                }
            });

            // Check text vs icons (except number circle text inside circle)
            if (t.textContent.trim() === '1' || t.textContent.trim() === '2' || t.textContent.trim() === '3') return;
            iconGroups.forEach(ig => {
                const ir = ig.getBoundingClientRect();
                if (!(tr.right < ir.left || tr.left > ir.right || tr.bottom < ir.top || tr.top > ir.bottom)) {
                    issues.push(`Text '${t.textContent.trim().slice(0, 25)}' overlaps icon at (${ir.left.toFixed(1)}, ${ir.top.toFixed(1)})`);
                }
            });
        });
        
        // Check text inside containing boxes
        const boxes = [
            { id: 'box-host', el: document.querySelector('#box-host') },
            { id: 'box-lane-1', el: document.querySelector('#box-lane-1') },
            { id: 'box-lane-2', el: document.querySelector('#box-lane-2') },
            { id: 'box-lane-3', el: document.querySelector('#box-lane-3') },
            { id: 'box-footer', el: document.querySelector('#box-footer') },
            { id: 'box-takeaway', el: document.querySelector('#box-takeaway') }
        ];

        return issues;
    }''')
    print('Overlaps count:', len(overlaps))
    for o in overlaps:
        print('  Overlap:', o)
