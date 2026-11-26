import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1100})
    page.goto(f"file://{os.path.abspath('test_candidate_dns.svg')}")
    
    collisions = page.evaluate("""() => {
        const issues = [];
        const texts = Array.from(document.querySelectorAll('text'));
        const lines = Array.from(document.querySelectorAll('line, path'));
        
        texts.forEach(t => {
            const tr = t.getBoundingClientRect();
            const txt = t.textContent.trim().replace(/\\s+/g, ' ');
            
            lines.forEach(l => {
                // Ignore lines inside icons (inside <g transform=...>)
                if (l.closest('g[transform]')) return;
                
                const lr = l.getBoundingClientRect();
                
                const xOverlap = (tr.left < lr.right && tr.right > lr.left);
                const yOverlap = (tr.top < lr.bottom && tr.bottom > lr.top);
                
                if (xOverlap && yOverlap) {
                    issues.push(`Line/path intersects text '${txt}'! Text: [${tr.left.toFixed(1)}, ${tr.top.toFixed(1)}, ${tr.right.toFixed(1)}, ${tr.bottom.toFixed(1)}], Line: [${lr.left.toFixed(1)}, ${lr.top.toFixed(1)}, ${lr.right.toFixed(1)}, ${lr.bottom.toFixed(1)}]`);
                }
            });
        });
        
        return issues;
    }""")
    
    print(f"Line/path text collisions: {len(collisions)}")
    for c in collisions:
        print(" ", c)
    assert len(collisions) == 0, f"Collisions: {collisions}"
