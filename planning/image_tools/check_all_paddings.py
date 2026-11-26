import os
import re
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

svg_path = os.path.abspath("test_full_candidate.svg")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f"file://{svg_path}")
    
    # Check all elements
    eval_results = page.evaluate("""() => {
        const issues = [];
        
        // 1. Text elements bounds vs canvas
        const texts = Array.from(document.querySelectorAll('text, tspan'));
        texts.forEach(el => {
            const r = el.getBoundingClientRect();
            const txt = el.textContent.trim();
            if (!txt) return;
            
            if (r.left < 39.5) {
                issues.push(`Left margin violation (< 40): '${txt.slice(0, 30)}' left=${r.left.toFixed(1)}`);
            }
            if (r.right > 1560.5) {
                issues.push(`Right margin violation (> 1560): '${txt.slice(0, 30)}' right=${r.right.toFixed(1)}`);
            }
            if (r.top < 39.5) {
                issues.push(`Top margin violation (< 40): '${txt.slice(0, 30)}' top=${r.top.toFixed(1)}`);
            }
            if (r.bottom > 1160.5) {
                issues.push(`Bottom margin violation (> 1160): '${txt.slice(0, 30)}' bottom=${r.bottom.toFixed(1)}`);
            }
        });
        
        // 2. Check font size
        const allTextEls = Array.from(document.querySelectorAll('text'));
        allTextEls.forEach(el => {
            const fs = parseFloat(window.getComputedStyle(el).fontSize);
            if (fs < 23.5) {
                issues.push(`Font size violation (< 24px): '${el.textContent.slice(0, 30)}' is ${fs}px`);
            }
        });

        // 3. Rects and text inside rects
        // Map of rect id to text selectors inside it
        const checks = [
            { rect: '#box-lane-1', text: '#lane-1 text' },
            { rect: '#box-lane-2', text: '#lane-2 text' },
            { rect: '#box-lane-3', text: '#lane-3 text' },
            { rect: '#box-footer', text: '#footer-notes text' },
            { rect: '#box-takeaway', text: '#bottom-bar text' }
        ];

        checks.forEach(c => {
            const rEl = document.querySelector(c.rect);
            const tEls = Array.from(document.querySelectorAll(c.text));
            if (!rEl) return;
            const rb = rEl.getBoundingClientRect();
            tEls.forEach(t => {
                const tb = t.getBoundingClientRect();
                const pl = tb.left - rb.left;
                const pr = rb.right - tb.right;
                const pt = tb.top - rb.top;
                const pb = rb.bottom - tb.bottom;
                if (pl < 15.5) issues.push(`${c.rect} padding left violation: ${pl.toFixed(1)} < 16 for '${t.textContent.slice(0,20)}'`);
                if (pr < 15.5) issues.push(`${c.rect} padding right violation: ${pr.toFixed(1)} < 16 for '${t.textContent.slice(0,20)}'`);
                if (pt < 15.5) issues.push(`${c.rect} padding top violation: ${pt.toFixed(1)} < 16 for '${t.textContent.slice(0,20)}'`);
                if (pb < 15.5) issues.push(`${c.rect} padding bottom violation: ${pb.toFixed(1)} < 16 for '${t.textContent.slice(0,20)}'`);
            });
        });

        return issues;
    }""")
    
    for iss in eval_results:
        print("ISSUE:", iss)
    print(f"Total issues: {len(eval_results)}")
