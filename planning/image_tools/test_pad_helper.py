from playwright.sync_api import sync_playwright
import xml.etree.ElementTree as ET
import re

def test_svg_content(svg_str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.set_content(f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>body {{ margin: 0; padding: 0; background: #fff; }}</style>
        </head>
        <body>
          {svg_str}
        </body>
        </html>
        """)

        cards_to_check = [
            ("c1-stack", "c1-stack rect", "c1-stack text"),
            ("c1-request", "c1-request rect", "c1-request text"),
            ("c1-response", "c1-response rect", "c1-response text"),
            ("c1-note", "c1-note rect", "c1-note text"),
            ("c2-stack", "c2-stack rect", "c2-stack text"),
            ("c2-note1", "c2-note1 rect", "c2-note1 text"),
            ("c2-note2-orange", "c2-note2-orange rect", "c2-note2-orange text"),
            ("c3-stack", "c3-stack rect", "c3-stack text"),
            ("c3-note1", "c3-note1 rect", "c3-note1 text"),
            ("c3-note2", "c3-note2 rect", "c3-note2 text"),
            ("c3-note3", "c3-note3 rect", "c3-note3 text"),
            ("c3-note4", "c3-note4 rect", "c3-note4 text"),
            ("strip-redirects", "strip-redirects rect", "strip-redirects text"),
            ("strip-timing", "strip-timing rect", "strip-timing text"),
            ("bar-takeaway", "bar-takeaway rect", "bar-takeaway text"),
        ]

        all_ok = True
        for name, rect_sel, text_sel in cards_to_check:
            rect_bb = page.locator(f"#{rect_sel}").first.bounding_box()
            texts = page.locator(f"#{text_sel}").all()
            for t_idx, t in enumerate(texts):
                t_bb = t.bounding_box()
                pad_l = t_bb['x'] - rect_bb['x']
                pad_r = (rect_bb['x'] + rect_bb['width']) - (t_bb['x'] + t_bb['width'])
                pad_t = t_bb['y'] - rect_bb['y']
                pad_b = (rect_bb['y'] + rect_bb['height']) - (t_bb['y'] + t_bb['height'])
                min_pad = min(pad_l, pad_r, pad_t, pad_b)
                status = "PASS" if min_pad >= 16 else "FAIL"
                if min_pad < 16:
                    all_ok = False
                print(f"[{status}] {name:16s} #{t_idx}: L={pad_l:4.1f}, R={pad_r:4.1f}, T={pad_t:4.1f}, B={pad_b:4.1f} (min={min_pad:4.1f})")

        browser.close()
        return all_ok

print("Optimizer helper ready.")
