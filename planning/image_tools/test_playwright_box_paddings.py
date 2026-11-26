import os
from playwright.sync_api import sync_playwright

svg_path = os.path.abspath("service_path_candidate.svg")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f"file://{svg_path}")

    results = page.evaluate("""() => {
        const issues = [];
        const rects = Array.from(document.querySelectorAll('rect'));
        const texts = Array.from(document.querySelectorAll('text'));

        // Check each rung card
        const boxes = [
            { name: "Small Box", selector: 'rect[x="1190"]' },
            { name: "Rung 1", selector: 'rect[x="160"][y="140"]' },
            { name: "Rung 2", selector: 'rect[x="160"][y="274"]' },
            { name: "Rung 3", selector: 'rect[x="160"][y="408"]' },
            { name: "Rung 4", selector: 'rect[x="160"][y="542"]' },
            { name: "Orange Callout", selector: 'rect[x="980"]' },
            { name: "Rung 5", selector: 'rect[x="160"][y="704"]' },
            { name: "Rung 6", selector: 'rect[x="160"][y="838"]' },
            { name: "Rung 7", selector: 'rect[x="160"][y="972"]' },
            { name: "Takeaway", selector: 'rect[x="40"][y="1104"]' }
        ];

        boxes.forEach(b => {
            const el = document.querySelector(b.selector);
            if (!el) {
                issues.push(`Box not found: ${b.name}`);
                return;
            }
            const r = el.getBoundingClientRect();
            
            // Find all texts whose center falls inside this box
            const inside = texts.filter(t => {
                const tr = t.getBoundingClientRect();
                const cx = (tr.left + tr.right) / 2;
                const cy = (tr.top + tr.bottom) / 2;
                return cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom;
            });

            inside.forEach(t => {
                // If it has tspans, check tspans
                const tspans = Array.from(t.querySelectorAll('tspan'));
                const checkEls = tspans.length > 0 ? tspans : [t];
                
                checkEls.forEach(item => {
                    const ir = item.getBoundingClientRect();
                    const padL = ir.left - r.left;
                    const padR = r.right - ir.right;
                    const padT = ir.top - r.top;
                    const padB = r.bottom - ir.bottom;

                    const txt = item.textContent.trim().slice(0, 30);
                    if (padL < 15.5) issues.push(`${b.name} Left pad < 16: '${txt}' (${padL.toFixed(1)}px)`);
                    if (padR < 15.5) issues.push(`${b.name} Right pad < 16: '${txt}' (${padR.toFixed(1)}px)`);
                    if (padT < 15.5) issues.push(`${b.name} Top pad < 16: '${txt}' (${padT.toFixed(1)}px)`);
                    if (padB < 15.5) issues.push(`${b.name} Bottom pad < 16: '${txt}' (${padB.toFixed(1)}px)`);
                });
            });
        });

        return issues;
    }""")

    print(f"Playwright Box Padding Issues: {len(results)}")
    for iss in results:
        print(" ", iss)
    assert len(results) == 0, "Some box paddings failed!"
    print("ALL BOX PADDINGS >= 16px IN CHROMIUM!")
