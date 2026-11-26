import os
import re
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

svg_path = os.path.abspath("service_path_candidate.svg")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f"file://{svg_path}")

    # 1. XML check
    with open(svg_path) as f:
        content = f.read()
    root = ET.fromstring(content)

    c0 = root[0].tag.split('}')[-1]
    c1 = root[1].tag.split('}')[-1]
    print(f"1. First children: <{c0}>, <{c1}>")
    assert c0 == 'title' and c1 == 'desc', "First children must be <title> and <desc>"

    # 2. Check forbidden words
    forbidden = ["monospace", "bold", "orange", "grey", "arrow"]
    all_texts = [el.text for el in root.iter() if el.text and el.tag.split('}')[-1] in ('text', 'tspan')]
    for text in all_texts:
        for f_word in forbidden:
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            assert f_word not in words, f"Forbidden word '{f_word}' in text: '{text}'"
    print("2. Forbidden words check passed!")

    # 3. Check exact expected labels
    expected_labels = [
        "When a Service fails, confirm in order",
        "read top to bottom",
        "the first failing rung is where to look",
        "Pod",
        "call the pod IP and pod port directly from another pod",
        "Service",
        "the Service exists, otherwise lookup fails with Name or service not known",
        "DNS",
        "short, namespaced and full names resolve",
        "Endpoints",
        "kubectl get endpointslices -l kubernetes.io/service-name=hostnames",
        "ENDPOINTS shows none means the Service selector does not match pod labels",
        "Ports",
        "Service port listed, targetPort correct, named port matched",
        "kube-proxy rules",
        "iptables-save grep hostnames, or ipvsadm -ln",
        "Conntrack",
        "table usage, since iptables Service load balancing depends on connection tracking",
        "Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack"
    ]

    def norm(s):
        return " ".join(s.split())

    dom_texts = page.evaluate("Array.from(document.querySelectorAll('text')).map(e => e.textContent)")
    svg_raw_text = norm(" ".join(dom_texts))

    print(f"\n3. Checking {len(expected_labels)} expected labels:")
    for label in expected_labels:
        nl = norm(label)
        in_dom = nl in svg_raw_text
        print(f"   [{'OK' if in_dom else 'MISSING'}] '{nl[:50]}...'")
        assert in_dom, f"Missing label: {label}"
    print("All expected labels present!")

    # 4. Measure text bounding boxes and checks
    eval_results = page.evaluate("""() => {
        const issues = [];
        const texts = Array.from(document.querySelectorAll('text, tspan'));

        texts.forEach(el => {
            const r = el.getBoundingClientRect();
            const txt = el.textContent.trim();
            if (!txt) return;

            // Check canvas margins (left >= 40, right <= 1560, top >= 40, bottom <= 1160)
            if (r.left < 39.0) {
                issues.push(`Left margin violation (< 40): '${txt.slice(0, 30)}' at ${r.left.toFixed(1)}`);
            }
            if (r.right > 1561.0) {
                issues.push(`Right margin violation (> 1560): '${txt.slice(0, 30)}' at ${r.right.toFixed(1)}`);
            }
            if (r.top < 39.0) {
                issues.push(`Top margin violation (< 40): '${txt.slice(0, 30)}' at ${r.top.toFixed(1)}`);
            }
            if (r.bottom > 1161.0) {
                issues.push(`Bottom margin violation (> 1160): '${txt.slice(0, 30)}' at ${r.bottom.toFixed(1)}`);
            }
        });

        // Font sizes >= 24px
        const allTextEls = Array.from(document.querySelectorAll('text'));
        allTextEls.forEach(el => {
            const fs = parseFloat(window.getComputedStyle(el).fontSize);
            if (fs < 23.5) {
                issues.push(`Font size violation (< 24px): '${el.textContent.slice(0, 30)}' is ${fs}px`);
            }
        });

        return issues;
    }""")

    print(f"\n4. Canvas margin & font-size issues: {len(eval_results)}")
    for issue in eval_results:
        print("  ", issue)
    assert len(eval_results) == 0, f"Found {len(eval_results)} issues"

    # 5. Check arrow count
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    total_arrows = len(lines_with_marker) + len(paths_with_marker)
    print(f"\n5. Arrow count: {total_arrows} (expected: 1)")
    assert total_arrows == 1, f"Expected 1 arrow, got {total_arrows}"

    # 6. Check orange count
    orange_matches = re.findall(r'#db8129', content, re.IGNORECASE)
    print(f"6. Orange (#db8129) count: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # Save a screenshot to inspect
    page.screenshot(path="service_path_render.png")
    print("\nSUCCESS: All audit checks passed perfectly! Screenshot saved to service_path_render.png")
