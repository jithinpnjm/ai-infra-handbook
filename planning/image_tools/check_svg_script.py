from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    cwd = os.getcwd()
    page.goto(f'file://{cwd}/candidate_cfg_order.svg')
    
    issues = page.evaluate('''() => {
        const issues = [];
        const svg = document.querySelector('svg');
        const W = 1600;
        const H = 1200;
        
        // 1. Outside margin of all rendered elements (rects, text, paths)
        const allElements = Array.from(document.querySelectorAll('text, rect, circle, path, polygon, line'));
        for (const el of allElements) {
            if (el.tagName.toLowerCase() === 'rect' && el.getAttribute('width') == '1600' && el.getAttribute('height') == '1200') {
                continue; // background
            }
            const r = el.getBoundingClientRect();
            if (r.top < 38) {
                issues.push(`Outside margin violation (top < 40): ${el.tagName} at top=${r.top.toFixed(1)}, text='${(el.textContent||'').slice(0,30)}'`);
            }
            if (r.bottom > 1162) {
                issues.push(`Outside margin violation (bottom > 1160): ${el.tagName} at bottom=${r.bottom.toFixed(1)}`);
            }
            if (r.left < 38) {
                issues.push(`Outside margin violation (left < 40): ${el.tagName} at left=${r.left.toFixed(1)}`);
            }
            if (r.right > 1562) {
                issues.push(`Outside margin violation (right > 1560): ${el.tagName} at right=${r.right.toFixed(1)}`);
            }
        }
        
        // 2. Font sizes
        const texts = Array.from(document.querySelectorAll('text'));
        for (const t of texts) {
            const fs = parseFloat(window.getComputedStyle(t).fontSize);
            const content = t.textContent.replace(/\\s+/g, ' ').trim();
            if (fs < 24) {
                issues.push(`Font size < 24px: ${fs}px for '${content}'`);
            }
        }
        
        return issues;
    }''')
    
    for iss in set(issues):
        print('ISSUE:', iss)
    if not issues:
        print('No canvas margin or font size issues!')
    browser.close()
