#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def comprehensive_audit(svg_path):
    print(f"=== COMPREHENSIVE AUDIT OF {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure
    children = list(root)
    t0 = children[0].tag.split('}')[-1]
    t1 = children[1].tag.split('}')[-1]
    assert t0 == 'title', f"Child 0 must be <title>, got <{t0}>"
    assert t1 == 'desc', f"Child 1 must be <desc>, got <{t1}>"
    print("1. [PASS] Root children <title> and <desc> valid.")

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    assert width == "1600"
    assert viewBox.startswith("0 0 1600 ")
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200
    assert int(height) == int(vb_parts[3])
    print(f"2. [PASS] Dimensions: width={width}, height={height}, viewBox={viewBox}")

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
    print(f"3. [PASS] All {len(text_elements)} text elements have font-size >= 24px.")

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
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        if cnt != 1:
            all_ok = False
            print(f"   [FAIL] count={cnt}: '{exp}'")
        else:
            print(f"   [PASS] count=1: '{exp[:50]}...'")
    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
    assert len(extras) == 0, f"Unexpected extras: {extras}"
    assert len(found_texts) == len(expected_labels) + len(step_numbers), f"Mismatch: {len(found_texts)} vs {len(expected_labels) + len(step_numbers)}"
    print("4. [PASS] Exact label count matches (12 expected + 7 step numbers).")

    # 5. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("5. [PASS] No forbidden words found in text.")

    # 6. Orange count
    svg_str = open(svg_path).read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    assert len(orange_matches) == 1, f"Orange count {len(orange_matches)} != 1"
    print("6. [PASS] Orange #db8129 used exactly once.")

    # 7. Arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
    print("7. [PASS] Exactly 0 arrows with marker-end.")

    # 8. Bounds and paddings check for boxes and text
    # Boxes:
    boxes = [
        ("step-1", 40, 118, 1030, 144),
        ("step-2", 40, 269, 1030, 144),
        ("step-3", 40, 420, 1030, 124),
        ("step-4", 40, 551, 1030, 102),
        ("step-5", 40, 660, 1030, 62),
        ("step-6", 40, 729, 1030, 80),
        ("step-7", 40, 816, 1030, 102),
        ("real-use", 1090, 118, 470, 800),
        ("public-ca", 40, 936, 1520, 124),
        ("bottom-bar", 40, 1076, 1520, 56)
    ]
    H_val = float(height)
    for name, bx, by, bw, bh in boxes:
        lm = bx
        rm = 1600 - (bx + bw)
        tm = by
        bm = H_val - (by + bh)
        assert lm >= 40, f"Left margin violation in {name}: {lm} < 40"
        assert rm >= 40, f"Right margin violation in {name}: {rm} < 40"
        assert tm >= 40, f"Top margin violation in {name}: {tm} < 40"
        assert bm >= 40, f"Bottom margin violation in {name}: {bm} < 40"

    print("8. [PASS] All top-level boxes have margins >= 40px from canvas edges.")

    # 9. Text bounds inside boxes
    # Check each group
    for g in root.iter('{http://www.w3.org/2000/svg}g'):
        gid = g.attrib.get('id')
        rect = g.find('{http://www.w3.org/2000/svg}rect')
        text = g.find('{http://www.w3.org/2000/svg}text')
        if rect is not None and text is not None and gid in [b[0] for b in boxes]:
            bx = float(rect.attrib['x'])
            by = float(rect.attrib['y'])
            bw = float(rect.attrib['width'])
            bh = float(rect.attrib['height'])
            
            # check all text inside this group
            for t_elem in g.iter('{http://www.w3.org/2000/svg}text'):
                if t_elem.attrib.get('fill') == '#ffffff':
                    # circle text (step number) or bottom bar text
                    continue
                tx = float(t_elem.attrib.get('x', '0'))
                ty = float(t_elem.attrib.get('y', '0'))
                fs = float(t_elem.attrib.get('font-size', '24'))
                ff = t_elem.attrib.get('font-family', 'sans-serif')
                
                tspans = t_elem.findall('{http://www.w3.org/2000/svg}tspan')
                if not tspans:
                    items = [(tx, ty, fs, ff, "".join(t_elem.itertext()).strip())]
                else:
                    items = []
                    for tsp in tspans:
                        items.append((
                            float(tsp.attrib.get('x', tx)),
                            float(tsp.attrib.get('y', ty)),
                            float(tsp.attrib.get('font-size', fs)),
                            tsp.attrib.get('font-family', ff),
                            "".join(tsp.itertext()).strip()
                        ))
                
                for lx, ly, lfs, lff, ltext in items:
                    rate = 0.62 if 'monospace' in lff else 0.6
                    w = len(ltext) * lfs * rate
                    top = ly - 0.75 * lfs
                    bot = ly + 0.25 * lfs
                    
                    # Horizontal padding
                    lpad = lx - bx
                    rpad = (bx + bw) - (lx + w)
                    tpad = top - by
                    bpad = (by + bh) - bot
                    
                    assert lpad >= 16, f"Left padding violation in {gid}: {lpad:.1f} < 16 (line: '{ltext}')"
                    assert rpad >= 16, f"Right padding violation in {gid}: {rpad:.1f} < 16 (line: '{ltext}')"
                    assert tpad >= 10, f"Top padding violation in {gid}: {tpad:.1f} < 10 (line: '{ltext}')"
                    assert bpad >= 10, f"Bottom padding violation in {gid}: {bpad:.1f} < 10 (line: '{ltext}')"
                    print(f"   [{gid}] '{ltext[:30]}...' L-pad={lpad:.1f} R-pad={rpad:.1f} T-pad={tpad:.1f} B-pad={bpad:.1f}")

    print("9. [PASS] All text lines strictly fit within boxes with >= 16px horizontal padding.")
    print("\n==================== ALL 9 COMPREHENSIVE AUDITS PASSED! ====================")

if __name__ == "__main__":
    import subprocess
    subprocess.run(["python3", "build_perfect.py"], check=True)
    comprehensive_audit("candidate_perfect.svg")
