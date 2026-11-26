import os
from playwright.sync_api import sync_playwright

svg_path = os.path.abspath("test_service_python.svg")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f"file://{svg_path}")
    
    # Check all text elements bounding boxes
    issues = page.evaluate("""() => {
        const issues = [];
        const svg = document.querySelector('svg');
        const texts = Array.from(document.querySelectorAll('text'));
        
        // 1. Outside margin violations
        texts.forEach((el, idx) => {
            const r = el.getBoundingClientRect();
            const textContent = el.textContent.trim();
            if (r.left < 39.5) {
                issues.push(`Outside margin violation (left < 40): '${textContent.slice(0, 30)}' at left=${r.left.toFixed(1)}`);
            }
            if (r.right > 1560.5) {
                issues.push(`Outside margin violation (right > 1560): '${textContent.slice(0, 30)}' at right=${r.right.toFixed(1)}`);
            }
            if (r.top < 39.5) {
                issues.push(`Outside margin violation (top < 40): '${textContent.slice(0, 30)}' at top=${r.top.toFixed(1)}`);
            }
            if (r.bottom > 1160.5) {
                issues.push(`Outside margin violation (bottom > 1160): '${textContent.slice(0, 30)}' at bottom=${r.bottom.toFixed(1)}`);
            }
        });
        
        // 2. Rect padding checks
        // For each rect that has text inside it:
        const checkCard = (cardSel, textSel, name) => {
            const card = document.querySelector(cardSel);
            const text = document.querySelector(textSel);
            if (!card || !text) return;
            const cr = card.getBoundingClientRect();
            const tr = text.getBoundingClientRect();
            
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            
            if (padL < 15.5) issues.push(`${name} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`${name} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`${name} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`${name} bottom padding ${padB.toFixed(1)} < 16`);
        };
        
        checkCard('#fix-box rect', '#fix-box text', 'Fix box');
        checkCard('#rules-strip rect', '#rules-strip text', 'Rules strip');
        checkCard('#bottom-bar rect', '#bottom-bar text', 'Bottom bar');
        
        // Check lane cards
        const laneShellCards = Array.from(document.querySelectorAll('#lane-shell rect[width="704"]'));
        const laneShellTexts = Array.from(document.querySelectorAll('#lane-shell text')).filter(t => !t.textContent.includes('Your shell'));
        laneShellTexts.forEach((t, i) => {
            const c = laneShellCards[i];
            const cr = c.getBoundingClientRect();
            const tr = t.getBoundingClientRect();
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            if (padL < 15.5) issues.push(`Lane Shell Card ${i+1} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`Lane Shell Card ${i+1} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`Lane Shell Card ${i+1} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`Lane Shell Card ${i+1} bottom padding ${padB.toFixed(1)} < 16`);
        });

        const laneDaemonCards = Array.from(document.querySelectorAll('#lane-daemon rect[width="704"]'));
        const laneDaemonTexts = Array.from(document.querySelectorAll('#lane-daemon text')).filter(t => !t.textContent.includes('cron, systemd or CI'));
        laneDaemonTexts.forEach((t, i) => {
            const c = laneDaemonCards[i];
            const cr = c.getBoundingClientRect();
            const tr = t.getBoundingClientRect();
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            if (padL < 15.5) issues.push(`Lane Daemon Card ${i+1} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`Lane Daemon Card ${i+1} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`Lane Daemon Card ${i+1} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`Lane Daemon Card ${i+1} bottom padding ${padB.toFixed(1)} < 16`);
        });

        // Check Checks cards
        const checksCards = Array.from(document.querySelectorAll('#checks-strip rect[width="540"], #checks-strip rect[width="844"]'));
        const checksTexts = Array.from(document.querySelectorAll('#checks-strip text'));
        checksTexts.forEach((t, i) => {
            const c = checksCards[i];
            const cr = c.getBoundingClientRect();
            const tr = t.getBoundingClientRect();
            const padL = tr.left - cr.left;
            const padR = cr.right - tr.right;
            const padT = tr.top - cr.top;
            const padB = cr.bottom - tr.bottom;
            if (padL < 15.5) issues.push(`Checks Card ${i+1} left padding ${padL.toFixed(1)} < 16`);
            if (padR < 15.5) issues.push(`Checks Card ${i+1} right padding ${padR.toFixed(1)} < 16`);
            if (padT < 15.5) issues.push(`Checks Card ${i+1} top padding ${padT.toFixed(1)} < 16`);
            if (padB < 15.5) issues.push(`Checks Card ${i+1} bottom padding ${padB.toFixed(1)} < 16`);
        });

        return issues;
    }""")
    
    print(f"Browser Audit Issues ({len(issues)}):")
    for iss in issues:
        print("  -", iss)
    if not issues:
        print("[PASS] Chromium rendered with ZERO issues!")
    browser.close()
