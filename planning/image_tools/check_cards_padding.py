from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    cwd = os.getcwd()
    page.goto(f'file://{cwd}/candidate_cfg_order.svg')
    
    details = page.evaluate('''() => {
        const results = [];
        
        // Find all cards inside ladder 1 and ladder 2
        const checkCard = (ladderId) => {
            const ladder = document.getElementById(ladderId);
            const cards = Array.from(ladder.querySelectorAll('rect')).slice(1); // skip outer container rect
            // texts inside each card
            const texts = Array.from(ladder.querySelectorAll('text')).filter(t => {
                // skip header text
                return t.textContent.trim() !== '1' && t.textContent.trim() !== '2' && 
                       t.textContent.trim() !== '3' && t.textContent.trim() !== '4' &&
                       !t.textContent.includes('Which file is read') && !t.textContent.includes('Which value wins');
            });
            
            for (let i = 0; i < cards.length; i++) {
                const c = cards[i];
                const t = texts[i];
                if (!c || !t) continue;
                const cr = c.getBoundingClientRect();
                const tr = t.getBoundingClientRect();
                results.push({
                    name: `${ladderId} card ${i+1}`,
                    text: t.textContent.replace(/\\s+/g, ' ').trim().slice(0, 30),
                    padLeft: tr.left - cr.left,
                    padRight: cr.right - tr.right,
                    padTop: tr.top - cr.top,
                    padBottom: cr.bottom - tr.bottom,
                });
            }
        };
        
        checkCard('ladder-1');
        checkCard('ladder-2');
        
        return results;
    }''')
    
    for d in details:
        print(f"{d['name']} ({d['text']}):")
        print(f"  padLeft: {d['padLeft']:.1f}, padRight: {d['padRight']:.1f}, padTop: {d['padTop']:.1f}, padBottom: {d['padBottom']:.1f}")
        if any(p < 16 for p in [d['padLeft'], d['padRight'], d['padTop'], d['padBottom']]):
            print(f"  WARNING: padding < 16 in {d['name']}!")
            
    browser.close()
