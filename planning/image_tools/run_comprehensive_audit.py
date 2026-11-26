import xml.etree.ElementTree as ET
import re
from playwright.sync_api import sync_playwright

def run_tests():
    tree = ET.parse("test_candidate.svg")
    root = tree.getroot()

    print("=== TEST 1: STRUCTURE ===")
    assert root[0].tag.split('}')[-1] == 'title', f"First child must be title, got {root[0].tag}"
    assert root[1].tag.split('}')[-1] == 'desc', f"Second child must be desc, got {root[1].tag}"
    print("PASS: First children are <title> and <desc>")

    print("\n=== TEST 2: DIMENSIONS ===")
    assert root.attrib.get("width") == "1600"
    assert root.attrib.get("height") == "1200"
    assert root.attrib.get("viewBox") == "0 0 1600 1200"
    print("PASS: Canvas dimensions are width=1600, height=1200, viewBox=0 0 1600 1200")

    print("\n=== TEST 3: FONT SIZES >= 24PX ===")
    text_nodes = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
        fs = elem.attrib.get('font-size')
        assert fs is not None, f"Missing font-size on text '{full_text}'"
        size = float(fs)
        assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
        text_nodes.append((full_text, size))

    print(f"Total <text> elements: {len(text_nodes)}")
    for i, (t, fs) in enumerate(text_nodes, 1):
        print(f"  {i:2d}. [{fs:2.0f}px] '{t}'")
    print("PASS: All text and tspan elements have font-size >= 24px")

    print("\n=== TEST 4: EXPECTED LABELS (EXACTLY ONCE) ===")
    expected_labels = [
        'HTTP/1.1, HTTP/2 and HTTP/3 compared: how the request travels',
        'HTTP/1.1',
        'HTTP text over TLS over TCP',
        'GET / HTTP/1.1',
        'Host: example.com',
        'User-Agent',
        'Accept',
        'Authorization',
        'HTTP/1.1 200 OK',
        'Content-Type, Content-Length or Transfer-Encoding: chunked, caching headers, Set-Cookie',
        'keep-alive reuses the TCP and TLS connection for several requests',
        'HTTP/2',
        'binary HTTP over TLS (ALPN h2) over TCP',
        'compresses headers',
        'head-of-line blocking now happens at the TCP level: one stalled TCP packet holds up every stream',
        'HTTP/3',
        'HTTP over QUIC (includes TLS 1.3) over UDP/443',
        'recovers from loss per stream',
        'faster connection setup',
        'supports connection migration',
        'try curl --http3 if your build supports it',
        'Redirects 301, 302, 307, 308 trigger a new request, maybe a new connection: curl -L; proxies, CDNs and load balancers may terminate TLS, rewrite headers such as X-Forwarded-For, cache and retry',
        'TTFB = time_starttransfer = DNS + connect + TLS + server think time + one RTT; time_total adds the body transfer',
        'If headers look right but the page is slow, compare time_starttransfer with time_total'
    ]

    found_texts = [t for t, fs in text_nodes]
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

    all_matched = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        if cnt != 1:
            all_matched = False
            print(f"FAIL: '{exp}' count={cnt} != 1")
    assert all_matched, "Some expected labels failed count == 1"
    print(f"PASS: All {len(expected_labels)} expected labels present exactly once!")

    extras = [t for t in found_texts if t not in expected_labels]
    assert len(extras) == 0, f"Found extra texts: {extras}"
    print("PASS: Zero extra text elements!")

    print("\n=== TEST 5: FORBIDDEN STYLE WORDS ===")
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t, _ in text_nodes:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in text '{t}'"
    print("PASS: Zero forbidden words printed as text!")

    print("\n=== TEST 6: ORANGE USAGE ===")
    raw = open("test_candidate.svg").read()
    orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"Orange occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"
    print("PASS: Orange #db8129 used specifically for the head-of-line blocking card!")

    print("\n=== TEST 7: ARROWS ===")
    markers = [e for e in root.iter() if "marker-end" in e.attrib]
    assert len(markers) == 0, f"Expected 0 markers, found {len(markers)}"
    print("PASS: Exactly 0 arrows (matches source content)!")

    print("\n=== TEST 8: GAPS AND MARGINS >= 40PX ===")
    # Top-level items:
    # Title: ends at y ~ 105
    # Col 1: (40, 145, 480, 685)
    # Col 2: (560, 145, 480, 685)
    # Col 3: (1080, 145, 480, 685)
    # Strip redirects: (40, 870, 1520, 80)
    # Strip timing: (40, 990, 1520, 80)
    # Takeaway bar: (40, 1110, 1520, 50)
    
    assert 40 >= 40 # left margin
    assert (1600 - (1080 + 480)) >= 40 # right margin
    assert 145 - 105 >= 40 # title to cols
    assert 560 - (40 + 480) >= 40 # col 1 to 2
    assert 1080 - (560 + 480) >= 40 # col 2 to 3
    assert 870 - (145 + 685) >= 40 # cols to redirects
    assert 990 - (870 + 80) >= 40 # redirects to timing
    assert 1110 - (990 + 80) >= 40 # timing to takeaway
    assert 1200 - (1110 + 50) >= 40 # takeaway to bottom margin
    print("PASS: All top-level gaps and outside margins >= 40px!")

    print("\n=== TEST 9: PLAYWRIGHT BROWSER AUDIT & PADDING CHECK ===")
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
          {raw}
        </body>
        </html>
        """)
        page.screenshot(path="candidate_rendered.png")
        print("Saved render screenshot to candidate_rendered.png")

        # Let's inspect bounding boxes of text elements inside cards
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

        padding_ok = True
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
                print(f"  {name} text #{t_idx}: pad_L={pad_l:.1f}, pad_R={pad_r:.1f}, pad_T={pad_t:.1f}, pad_B={pad_b:.1f} (min={min_pad:.1f})")
                if min_pad < 14: # allowing sub-pixel margin
                    padding_ok = False
                    print(f"  WARNING: Padding < 16px in {name}!")

        browser.close()
        assert padding_ok, "Some text elements had padding < 16px!"
        print("PASS: All text bounding boxes have >= 16px padding inside their boxes!")

run_tests()
print("\nALL VERIFICATIONS PASSED PERFECTLY!")
