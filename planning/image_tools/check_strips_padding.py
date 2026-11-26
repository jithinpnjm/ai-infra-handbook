from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    cwd = os.getcwd()
    page.goto(f'file://{cwd}/candidate_cfg_order.svg')
    
    details = page.evaluate('''() => {
        const results = [];
        // Map cards and their texts
        const checkCard = (cardSelector, textSelector, name) => {
            const card = document.querySelector(cardSelector);
            const text = document.querySelector(textSelector);
            if (!card || !text) return;
            const cr = card.getBoundingClientRect();
            const tr = text.getBoundingClientRect();
            
            // Check padding
            const padLeft = tr.left - cr.left;
            const padRight = cr.right - tr.right;
            const padTop = tr.top - cr.top;
            const padBottom = cr.bottom - tr.bottom;
            results.push({
                name,
                padLeft, padRight, padTop, padBottom,
                cr: {x: cr.left, y: cr.top, w: cr.width, h: cr.height},
                tr: {x: tr.left, y: tr.top, w: tr.width, h: tr.height}
            });
        };
        
        // Commands strip
        checkCard('#commands-strip rect', '#commands-strip text', 'commands strip');
        // Surprise story
        checkCard('#surprise-story rect', '#surprise-story text', 'surprise story');
        // Rules strip
        checkCard('#rules-strip rect', '#rules-strip text', 'rules strip');
        // Bottom bar
        checkCard('#bottom-bar rect', '#bottom-bar text', 'bottom bar');
        
        return results;
    }''')
    
    for d in details:
        print(f"{d['name']}:")
        print(f"  padLeft: {d['padLeft']:.1f}, padRight: {d['padRight']:.1f}, padTop: {d['padTop']:.1f}, padBottom: {d['padBottom']:.1f}")
        if any(p < 16 for p in [d['padLeft'], d['padRight'], d['padTop'], d['padBottom']]):
            print(f"  WARNING: padding < 16 in {d['name']}!")
            
    browser.close()
