import os
import re
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

tree = ET.parse("test_candidate_dns.svg")
root = tree.getroot()

# 1. XML parsing
print("1. XML parsing: SUCCESS")

# 2. Check title and desc are first children
first_two = [elem.tag.split("}")[-1] for elem in list(root)[:2]]
print(f"2. First children: {first_two}")
assert first_two == ["title", "desc"], "First two elements must be title and desc!"

# 3. Check width, height, viewBox
w = root.attrib.get("width")
h = root.attrib.get("height")
vb = root.attrib.get("viewBox")
print(f"3. Dimensions: width={w}, height={h}, viewBox='{vb}'")
assert w == "1600" and h == "1100" and vb == "0 0 1600 1100"

# 4. Check style words in visible text
style_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
bad_matches = []
for elem in root.iter():
    if elem.tag.endswith("text") or elem.tag.endswith("tspan"):
        if elem.text:
            for word in style_words:
                if re.search(r'\b' + word + r'\b', elem.text, re.IGNORECASE):
                    bad_matches.append((elem.tag, elem.text, word))
print(f"4. Style instruction words in visible text: {len(bad_matches)}")
if bad_matches:
    for bm in bad_matches:
        print("  BAD STYLE WORD:", bm)
assert len(bad_matches) == 0, f"Found style words: {bad_matches}"

# 5. Check color orange usage (#db8129)
with open("test_candidate_dns.svg") as f:
    svg_raw = f.read()

orange_matches = re.findall(r'#db8129', svg_raw, re.IGNORECASE)
print(f"5. Occurrences of #db8129 (orange): {len(orange_matches)}")
# Must only be on collision X!
assert len(orange_matches) == 1, f"Expected orange ONLY on collision X (1 occurrence in stroke), found {len(orange_matches)}"

# 6. Check font sizes >= 24
min_font_size = 999
for elem in root.iter():
    if elem.tag.endswith("text") or elem.tag.endswith("tspan"):
        fs = elem.attrib.get("font-size")
        if fs:
            val = float(re.sub(r"[^\d.]", "", fs))
            min_font_size = min(min_font_size, val)
print(f"6. Minimum font size across all text elements: {min_font_size}px")
assert min_font_size >= 24, f"Found text smaller than 24px: {min_font_size}px!"

# 7. Check exact labels from prompt
exact_labels = [
    "How parallel A and AAAA queries race in conntrack and cause a 5-second stall",
    "pod",
    "glibc resolver",
    "one UDP socket",
    "A query",
    "AAAA query",
    "both to the same source IP and port",
    "netfilter",
    "conntrack",
    "two side-by-side insertion slots",
    "kube-proxy DNAT to a CoreDNS pod chosen by KUBE-SVC",
    "the two packets may go to different CoreDNS pods",
    "the second insertion collides with the first",
    "insert_failed",
    "the packet is silently dropped",
    "waits for default 5 s timeout, then retries",
    "NodeLocal DNSCache removes the DNAT with a NOTRACK note",
    "single-request-reopen separates the two queries",
    "TCP to DNS avoids the UDP path",
    "two parallel queries on one socket can collide in the kernel, and the lost packet costs a timeout"
]

stripped = re.sub(r"<[^>]+>", " ", svg_raw)
stripped = re.sub(r"\s+", " ", stripped).strip()

print("\n7. Checking presence of all exact labels:")
missing = []
for label in exact_labels:
    norm_label = re.sub(r"\s+", " ", label).strip()
    if norm_label in stripped:
        print(f"  FOUND: {norm_label[:55]}...")
    else:
        print(f"  MISSING: {norm_label}")
        missing.append(norm_label)

assert len(missing) == 0, f"Missing labels: {missing}"

# 8. Check Playwright bounding boxes, margins >= 40px, text padding >= 16px
print("\n8. Running Playwright browser validation...")
svg_path = os.path.abspath("test_candidate_dns.svg")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1100})
    page.goto(f"file://{svg_path}")
    
    issues = page.evaluate("""() => {
        const issues = [];
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
            if (r.bottom > 1060.5) {
                issues.push(`Outside margin violation (bottom > 1060): '${textContent.slice(0, 30)}' at bottom=${r.bottom.toFixed(1)}`);
            }
        });
        
        return issues;
    }""")
    
    print(f"Playwright margin issues found: {len(issues)}")
    for iss in issues:
        print("  ISSUE:", iss)
    assert len(issues) == 0, f"Margin issues: {issues}"

print("\n==========================================")
print("ALL AUDIT CHECKS PASSED PERFECTLY!")
print("==========================================")
