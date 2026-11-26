import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1100})
    page.goto(f"file://{os.path.abspath('test_candidate_dns.svg')}")
    
    overlaps = page.evaluate("""() => {
        const issues = [];
        const texts = Array.from(document.querySelectorAll('text'));
        
        for (let i = 0; i < texts.length; i++) {
            const r1 = texts[i].getBoundingClientRect();
            const t1 = texts[i].textContent.trim().replace(/\\s+/g, ' ');
            for (let j = i + 1; j < texts.length; j++) {
                const r2 = texts[j].getBoundingClientRect();
                const t2 = texts[j].textContent.trim().replace(/\\s+/g, ' ');
                
                const xOverlap = (r1.left < r2.right && r1.right > r2.left);
                const yOverlap = (r1.top < r2.bottom && r1.bottom > r2.top);
                
                if (xOverlap && yOverlap) {
                    issues.push(`Text overlap between '${t1}' and '${t2}'`);
                }
            }
        }
        return issues;
    }""")
    
    print(f"Text-to-text overlaps: {len(overlaps)}")
    for ov in overlaps:
        print(" ", ov)
    assert len(overlaps) == 0, f"Overlaps: {overlaps}"
