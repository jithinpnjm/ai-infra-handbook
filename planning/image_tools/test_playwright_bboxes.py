import os
import re
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

def test_playwright_strict(svg_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1600, 'height': 1100})
        page.goto(f"file://{os.path.abspath(svg_path)}")
        
        results = page.evaluate("""() => {
            const issues = [];
            const svg = document.querySelector('svg');
            const texts = Array.from(document.querySelectorAll('text'));
            
            // 1. Outside margin violations (40px)
            texts.forEach((el) => {
                const r = el.getBoundingClientRect();
                const textContent = el.textContent.trim().replace(/\\s+/g, ' ');
                if (r.left < 39.5) {
                    issues.push(`Outside margin left < 40: '${textContent.slice(0, 30)}' (left=${r.left.toFixed(1)})`);
                }
                if (r.right > 1560.5) {
                    issues.push(`Outside margin right > 1560: '${textContent.slice(0, 30)}' (right=${r.right.toFixed(1)})`);
                }
                if (r.top < 39.5) {
                    issues.push(`Outside margin top < 40: '${textContent.slice(0, 30)}' (top=${r.top.toFixed(1)})`);
                }
                if (r.bottom > 1060.5) {
                    issues.push(`Outside margin bottom > 1060: '${textContent.slice(0, 30)}' (bottom=${r.bottom.toFixed(1)})`);
                }
            });

            // 2. Rect padding checks
            // For every rect with an id, find texts that are visually inside it and verify padding >= 15.5px
            const rects = Array.from(document.querySelectorAll('rect[id]'));
            rects.forEach(rect => {
                const cr = rect.getBoundingClientRect();
                const id = rect.getAttribute('id');
                // find texts whose center is inside cr
                texts.forEach(text => {
                    const tr = text.getBoundingClientRect();
                    const centerX = (tr.left + tr.right) / 2;
                    const centerY = (tr.top + tr.bottom) / 2;
                    
                    if (centerX >= cr.left && centerX <= cr.right && centerY >= cr.top && centerY <= cr.bottom) {
                        // This text belongs inside this rect (or one of its children)
                        // If it's directly inside (not in a child rect)
                        // Check if text exceeds rect bounds
                        const padL = tr.left - cr.left;
                        const padR = cr.right - tr.right;
                        const padT = tr.top - cr.top;
                        const padB = cr.bottom - tr.bottom;
                        const txt = text.textContent.trim().replace(/\\s+/g, ' ').slice(0, 25);
                        
                        if (padL < 15.5) issues.push(`Pad left < 16 in #${id}: '${txt}' (padL=${padL.toFixed(1)})`);
                        if (padR < 15.5) issues.push(`Pad right < 16 in #${id}: '${txt}' (padR=${padR.toFixed(1)})`);
                        if (padT < 15.5) issues.push(`Pad top < 16 in #${id}: '${txt}' (padT=${padT.toFixed(1)})`);
                        if (padB < 15.5) issues.push(`Pad bottom < 16 in #${id}: '${txt}' (padB=${padB.toFixed(1)})`);
                    }
                });
            });

            return issues;
        }""")
        return results

issues = test_playwright_strict("test_candidate_dns.svg")
print(f"Total issues found: {len(issues)}")
for iss in issues:
    print(" ", iss)
