#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def audit(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    t0 = children[0].tag.split('}')[-1]
    t1 = children[1].tag.split('}')[-1]
    print(f"1. Children: <{t0}>, <{t1}>")
    assert t0 == 'title', f"Child 0 must be <title>, got <{t0}>"
    assert t1 == 'desc', f"Child 1 must be <desc>, got <{t1}>"

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"Expected width 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

    # 3. Font-size >= 24 on all text and tspans
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        fs = elem.attrib.get('font-size')
        assert fs is not None, f"Missing font-size on text '{full_text}'"
        size = float(fs)
        assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
        text_elements.append((full_text, size))

    print(f"3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")

    # 4. Expected labels
    expected_labels = [
        "Building a private CA by hand: the seven steps and why each is there",
        "Make the CA key and self-signed root: openssl req -x509 ... -subj /CN=Lab Root CA -addext basicConstraints=critical,CA:TRUE -addext keyUsage=critical,keyCertSign,cRLSign -keyout ca.key -out ca.pem (10 years)",
        "Make the server key and CSR: openssl req -newkey ec ... -subj /CN=api.lab.internal -keyout srv.key -out srv.csr; a CSR carries only the public key and the requested names, the application form you send to the CA, never the secret",
        "Write the extension file srv.ext: subjectAltName=DNS:api.lab.internal,DNS:*.lab.internal,IP:10.0.0.5; extendedKeyUsage=serverAuth; basicConstraints=CA:FALSE",
        "Sign: openssl x509 -req -in srv.csr -CA ca.pem -CAkey ca.key -CAcreateserial -days 90 -extfile srv.ext -out srv.pem",
        "Verify: openssl verify -CAfile ca.pem srv.pem",
        "Trust the CA on the client (update-ca-certificates)",
        "Serve it with nginx: ssl_certificate, ssl_certificate_key, ssl_protocols TLSv1.2 TLSv1.3, http2 on",
        "Real use",
        "prefer step-ca or Vault PKI; keep the root offline and issue from intermediates; name constraints, short lifetimes, automated rotation; distribute the root to all trust stores through configuration management; keys generated on the server or in an HSM, TPM or KMS, never emailed, mode 0600, one machine per key; a client certificate is built the same way with extendedKeyUsage=clientAuth",
        "Let's Encrypt, DigiCert, Google Trust Services check control of the domain (DV) with a DNS or HTTP challenge; OV and EV add organisation checks; ACME (RFC 8555) automates renewal through certbot, acme.sh, Caddy, cert-manager; Let's Encrypt lasts 90 days; CT logs every public certificate; CAA records restrict which CAs may issue",
        "Building one by hand once is the best way to understand what the tools do for you"
    ]
    step_numbers = {"1", "2", "3", "4", "5", "6", "7"}

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
            print(f"   [FAIL] count={cnt}: '{exp}'")
        else:
            print(f"   [PASS] count=1: '{exp[:55]}...'")

    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"

    for num in step_numbers:
        cnt = found_texts.count(num)
        assert cnt == 1, f"Step number '{num}' count {cnt} != 1"
    print("   All step numbers 1-7 present in number circles. (PASS)")

    # 6. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n6. No forbidden words found! (PASS)")

    # 7. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    assert len(orange_matches) == 1, f"Orange count {len(orange_matches)} != 1"
    print("   PASS: Orange used exactly once.")

    # 8. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n8. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
    print("   PASS: Zero arrows.")

    print("\n==================== ALL CHECKS PASSED PERFECTLY! ====================")

if __name__ == "__main__":
    import subprocess
    subprocess.run(["python3", "build_full_svg.py"], check=True)
    audit("candidate_private_ca.svg")
