import os
import re
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

svg_path = os.path.abspath("test_full_candidate.svg")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})
    page.goto(f"file://{svg_path}")
    
    # 1. XML check
    with open(svg_path) as f:
        content = f.read()
    root = ET.fromstring(content)
    
    # First children:
    c0 = root[0].tag.split('}')[-1]
    c1 = root[1].tag.split('}')[-1]
    print(f"First children: <{c0}>, <{c1}>")
    assert c0 == 'title' and c1 == 'desc', "First children must be <title> and <desc>"
    
    # 2. Check forbidden words
    forbidden = ["monospace", "bold", "orange", "grey", "arrow"]
    all_texts = [el.text for el in root.iter() if el.text and el.tag.split('}')[-1] in ('text', 'tspan')]
    joined = " ".join(all_texts)
    for text in all_texts:
        for f_word in forbidden:
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            assert f_word not in words, f"Forbidden word '{f_word}' in text: '{text}'"
    print("Forbidden words check passed!")
    
    # 3. Check exact expected labels
    expected_labels = [
        "br0 (10.10.0.1/24)",
        "c1 (10.10.0.11)",
        "c2 (10.10.0.12)",
        "uplink NIC",
        "host",
        "c1 to c2 on the same bridge",
        "c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame to c2's veth and eth0",
        "br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic; Kubernetes requires it so kube-proxy rules apply",
        "c1 to the Internet",
        "default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed by conntrack and delivered back through the bridge; the outside world only talks to the host",
        "sysctl -w net.ipv4.ip_forward=1",
        "iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE",
        "iptables -I FORWARD -i br0 -j ACCEPT",
        "iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
        "host:8080 to c1:80",
        "iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.10.0.11:80",
        "iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 8080 -j DNAT ... for local clients",
        "DNS inside: mkdir /etc/netns/c1 and write nameserver 1.1.1.1 to /etc/netns/c1/resolv.conf",
        "almost literally what the default bridge network does: docker0, a veth per container, an IPAM address from a private pool, a default route via the bridge, masquerade, DNAT for published ports, a bind-mounted /etc/resolv.conf",
        "A container is only a namespace plus a cable"
    ]
    
    # Clean text helper
    def norm(s):
        return " ".join(s.split())
        
    # Also check SVG text
    svg_raw_text = norm(" ".join(page.evaluate("Array.from(document.querySelectorAll('text')).map(e => e.textContent)")))
    
    for label in expected_labels:
        nl = norm(label)
        in_dom = nl in svg_raw_text
        print(f"Label '{nl[:35]}...': {in_dom}")
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
    
    for iss in eval_results:
        print("ISSUE:", iss)
    assert len(eval_results) == 0, f"Found {len(eval_results)} issues!"
    print("Bounding box and font size checks passed completely!")
    
    # 5. Let's take a screenshot for visual confirmation
    page.screenshot(path="test_candidate.png")
    print("Screenshot saved to test_candidate.png")
