from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    cwd = os.getcwd()
    page.goto(f'file://{cwd}/candidate_cfg_order.svg')
    page.screenshot(path='candidate_render_new.png')
    
    # Run comprehensive checks
    results = page.evaluate('''() => {
        const issues = [];
        const W = 1600;
        const H = 1200;
        
        // 1. Outside margin of all rendered elements (rects, text, paths)
        const allElements = Array.from(document.querySelectorAll('text, rect, circle, path, polygon, line'));
        for (const el of allElements) {
            if (el.tagName.toLowerCase() === 'rect' && el.getAttribute('width') == '1600' && el.getAttribute('height') == '1200') {
                continue; // background
            }
            const r = el.getBoundingClientRect();
            if (r.top < 39.5) {
                issues.push(`Outside margin violation (top < 40): ${el.tagName} at top=${r.top.toFixed(1)}, text='${(el.textContent||'').slice(0,30)}'`);
            }
            if (r.bottom > 1160.5) {
                issues.push(`Outside margin violation (bottom > 1160): ${el.tagName} at bottom=${r.bottom.toFixed(1)}`);
            }
            if (r.left < 39.5) {
                issues.push(`Outside margin violation (left < 40): ${el.tagName} at left=${r.left.toFixed(1)}`);
            }
            if (r.right > 1560.5) {
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
        
        // 3. Card and box paddings
        const checkPadding = (boxSel, textSel, name) => {
            const box = document.querySelector(boxSel);
            const text = document.querySelector(textSel);
            if (!box || !text) {
                issues.push(`Missing element for ${name}`);
                return;
            }
            const br = box.getBoundingClientRect();
            const tr = text.getBoundingClientRect();
            
            const padL = tr.left - br.left;
            const padR = br.right - tr.right;
            const padT = tr.top - br.top;
            const padB = br.bottom - tr.bottom;
            
            if (padL < 15.5) issues.push(`${name} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`${name} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`${name} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`${name} bottom padding ${padB.toFixed(1)} < 16`);
        };
        
        checkPadding('#commands-strip rect', '#commands-strip text', 'Commands strip');
        checkPadding('#surprise-story rect', '#surprise-story text', 'Surprise story');
        checkPadding('#rules-strip rect', '#rules-strip text', 'Rules strip');
        checkPadding('#bottom-bar rect', '#bottom-bar text', 'Bottom bar');
        
        // Check cards in ladder 1 (cards have width="708")
        const l1Cards = Array.from(document.querySelectorAll('#ladder-1 rect[width="708"]'));
        const l1Texts = Array.from(document.querySelectorAll('#ladder-1 text')).filter(t => !t.textContent.includes('Which file is read') && !['1','2','3','4'].includes(t.textContent.trim()));
        for (let i = 0; i < l1Texts.length; i++) {
            const card = l1Cards[i];
            const txt = l1Texts[i];
            const cr = card.getBoundingClientRect();
            const tr = txt.getBoundingClientRect();
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            if (padL < 15.5) issues.push(`Ladder 1 card ${i+1} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`Ladder 1 card ${i+1} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`Ladder 1 card ${i+1} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`Ladder 1 card ${i+1} bottom padding ${padB.toFixed(1)} < 16`);
        }
        
        // Check cards in ladder 2 (cards have width="708")
        const l2Cards = Array.from(document.querySelectorAll('#ladder-2 rect[width="708"]'));
        const l2Texts = Array.from(document.querySelectorAll('#ladder-2 text')).filter(t => !t.textContent.includes('Which value wins') && !['1','2','3','4'].includes(t.textContent.trim()));
        for (let i = 0; i < l2Texts.length; i++) {
            const card = l2Cards[i];
            const txt = l2Texts[i];
            const cr = card.getBoundingClientRect();
            const tr = txt.getBoundingClientRect();
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            if (padL < 15.5) issues.push(`Ladder 2 card ${i+1} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`Ladder 2 card ${i+1} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`Ladder 2 card ${i+1} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`Ladder 2 card ${i+1} bottom padding ${padB.toFixed(1)} < 16`);
        }
        
        return issues;
    }''')
    
    print("=== PLAYWRIGHT BROWSER VALIDATION ===")
    if not results:
        print("PERFECT: 0 issues found! All margins, paddings, and font sizes strictly passed!")
    else:
        for iss in results:
            print("ISSUE:", iss)
    browser.close()
