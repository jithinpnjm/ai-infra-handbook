import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f'file://{os.path.abspath("test_perfect.svg")}')
    
    res = page.evaluate('''() => {
        const dns = document.querySelector('#footer-notes text:first-of-type');
        const dr = dns.getBoundingClientRect();
        const docker = document.querySelector('#footer-notes text:last-of-type');
        const dkr = docker.getBoundingClientRect();
        return {
            dns: { top: dr.top, bottom: dr.bottom, height: dr.height },
            docker: { top: dkr.top, bottom: dkr.bottom, height: dkr.height }
        };
    }''')
    print('Takeaway text rect:', res)
