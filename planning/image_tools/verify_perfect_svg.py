from playwright.sync_api import sync_playwright
import os

p_tuned = {
    't_y1': 84,
    't_y2': 130,
    
    'lad_y': 172,
    'lad_h': 446, # 172..618
    
    # Ladder 1 Cards
    'c1_y': 260,
    'c1_h': 60,
    'c1_ty': 38,
    
    'c2_y': 326,
    'c2_h': 150,
    'c2_ty1': 38,
    'c2_ty2': 65,
    'c2_ty3': 97,
    'c2_ty4': 125,
    
    'c3_y': 482,
    'c3_h': 60,
    'c3_ty': 38,
    
    'c4_y': 548,
    'c4_h': 60,
    'c4_ty': 38,
    
    # Ladder 2 Cards
    'l2_h': 82,
    'l2_ty': 51,
    'l2_c1_y': 260,
    'l2_c2_y': 348,
    'l2_c3_y': 436,
    'l2_c4_y': 524,
    
    # Strips
    'cmd_y': 658, # gap = 658 - 618 = 40
    'cmd_h': 116,
    'cmd_ty1': 38,
    'cmd_ty2': 66,
    'cmd_ty3': 94,
    
    'surp_y': 814, # gap = 814 - 774 = 40
    'surp_h': 88,
    'surp_ty1': 38,
    'surp_ty2': 66,
    
    'rules_y': 942, # gap = 942 - 902 = 40
    'rules_h': 116,
    'rules_ty1': 38,
    'rules_ty2': 66,
    'rules_ty3': 94,
    
    'bar_y': 1098, # gap = 1098 - 1058 = 40
    'bar_h': 60,
    'bar_ty': 38, # bottom = 1098 + 60 = 1158 -> bottom margin = 42px >= 40px!
}

from test_perfect_coordinates import generate_svg

svg_str = generate_svg(p_tuned)
with open('candidate_cfg_order.svg', 'w') as f:
    f.write(svg_str)

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    cwd = os.getcwd()
    page.goto(f'file://{cwd}/candidate_cfg_order.svg')
    page.screenshot(path='candidate_final_audit.png')
    
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
    
    print("=== PLAYWRIGHT VERIFICATION RESULTS ===")
    if not results:
        print("PERFECT: 0 ISSUES! ALL CHECKS PASSED WITH FLYING COLORS!")
    else:
        for iss in results:
            print("ISSUE:", iss)
    browser.close()
