import os
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1100})
    page.goto(f"file://{os.path.abspath('test_candidate_dns.svg')}")
    
    overlaps = page.evaluate("""() => {
        const issues = [];
        const texts = Array.from(document.querySelectorAll('text'));
        const rects = Array.from(document.querySelectorAll('rect'));
        const lines = Array.from(document.querySelectorAll('line, path'));
        
        // Check text against rect edges:
        // A text is either ENTIRELY inside a rect (with padding >= 16),
        // or ENTIRELY outside a rect (clearance >= 10).
        // It should NEVER intersect a rect border!
        texts.forEach(t => {
            const tr = t.getBoundingClientRect();
            const txt = t.textContent.trim().replace(/\\s+/g, ' ');
            
            rects.forEach(r => {
                const rr = r.getBoundingClientRect();
                // Check if text intersects the border of rect r
                // i.e., partially inside and partially outside
                const xOverlap = (tr.left < rr.right && tr.right > rr.left);
                const yOverlap = (tr.top < rr.bottom && tr.bottom > rr.top);
                
                if (xOverlap && yOverlap) {
                    const fullyInside = (tr.left >= rr.left && tr.right <= rr.right && tr.top >= rr.top && tr.bottom <= rr.bottom);
                    if (!fullyInside) {
                        issues.push(`Text '${txt}' crosses border of rect at [${rr.left}, ${rr.top}, ${rr.right}, ${rr.bottom}]: text is at [${tr.left.toFixed(1)}, ${tr.top.toFixed(1)}, ${tr.right.toFixed(1)}, ${tr.bottom.toFixed(1)}]`);
                    }
                }
            });
        });
        
        return issues;
    }""")
    
    print(f"Border crossings found: {len(overlaps)}")
    for ov in overlaps:
        print(" ", ov)
