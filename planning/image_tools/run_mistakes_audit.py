import xml.etree.ElementTree as ET
import re
import sys

def audit_svg(svg_path):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

    # 2. Dimensions
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"Expected width 1600, got {width}"
    assert viewBox == "0 0 1600 1200", f"Expected viewBox '0 0 1600 1200', got {viewBox}"
    assert height == "1200", f"Expected height 1200, got {height}"

    # 3. Check font-size >= 24 on all text and tspans
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

    print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")

    # 4. Expected labels
    expected_labels = [
        "Ten class and typing mistakes with their fixes",
        "Mistake",
        "Fix",
        "Mutable class attributes and mutable default arguments; forgetting default_factory in a dataclass",
        "create state in __init__; field(default_factory=list)",
        "Deep inheritance; inconsistent super().__init__ calls breaking cooperative inheritance; overriding methods with different signatures",
        "one or two levels, composition, compatible signatures",
        "Classes as namespaces for functions, where a module is the right tool, or as singletons",
        "a module and module-level objects",
        "Assuming type hints enforce anything at runtime; sprinkling Any and unchecked # type: ignore",
        "run mypy or pyright in CI; validate at the boundary with pydantic",
        "Validating the same data over and over, or never",
        "validate once at the boundary",
        "Exposing mutable internals such as returning the internal list",
        "return copies or tuples",
        "Overloading operators with surprising semantics, or __eq__ without __hash__",
        "natural meanings only; keep them consistent",
        "IO in __init__, or catching exceptions in constructors and leaving half-initialized objects",
        "explicit factory classmethod or lazy connection",
        "Pickling untrusted data, or relying on __del__",
        "JSON, YAML or protobuf; __enter__ and __exit__; pickle with __getstate__ is unsafe for untrusted data and breaks across versions",
        "Storing secrets in attributes that repr shows",
        "SecretStr",
        "copy.copy and copy.deepcopy can be customized with __copy__ and __deepcopy__",
        "Look for each of them in turn when you review your own code"
    ]

    found_texts = [t for t, fs in text_elements]

    print(f"\n4. Checking {len(expected_labels)} expected labels:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n5. No forbidden words found! (PASS)")

    # 6. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n8. All required colors present! (PASS)")

    # 9. Check outside margins and box bounds
    print("\n9. Checking outside margins...")
    rects = []
    for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
        x = float(elem.attrib.get('x', 0))
        y = float(elem.attrib.get('y', 0))
        w = float(elem.attrib.get('width', 0))
        h = float(elem.attrib.get('height', 0))
        if w == 1600 and h == 1200:
            continue
        rects.append((elem, x, y, w, h))
        assert x >= 40.0, f"Left margin {x} < 40!"
        assert x + w <= 1560.01, f"Right margin {x+w} > 1560!"
        assert y >= 40.0, f"Top margin {y} < 40!"
        assert y + h <= 1160.01, f"Bottom margin {y+h} > 1160!"
    print(f"   [PASS] All {len(rects)} content boxes obey >= 40px outside margins.")

    # 10. Check text padding inside containers
    # For each text, find its enclosing rect (or the rect right before it / containing it)
    print("\n10. Checking text line paddings...")
    # Map each text to the bounding rect it lives in
    # In our SVG, each row/header/bar has an enclosing rect.
    # We can check each text element against the rect that contains it:
    for text_elem in root.iter('{http://www.w3.org/2000/svg}text'):
        # Skip title
        full_text = "".join(text_elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        if full_text == "Ten class and typing mistakes with their fixes":
            continue
        
        base_fs = float(text_elem.attrib.get('font-size', 24))
        # Find containing rect:
        # text x and y
        tx = float(text_elem.attrib.get('x', 0))
        ty = float(text_elem.attrib.get('y', 0))
        
        # Candidate rects that enclose (tx, ty)
        containing = []
        for elem, rx, ry, rw, rh in rects:
            if rx <= tx <= rx + rw and ry <= ty <= ry + rh:
                containing.append((rx, ry, rw, rh))
            elif text_elem.attrib.get('text-anchor') == 'middle':
                # text center could be in the middle of rect
                if rx <= tx <= rx + rw and ry <= ty <= ry + rh:
                    containing.append((rx, ry, rw, rh))
        
        assert len(containing) >= 1, f"Could not find containing rect for text '{full_text}' at ({tx}, {ty})"
        rx, ry, rw, rh = containing[0]

        tspans = text_elem.findall('{http://www.w3.org/2000/svg}tspan')
        if not tspans:
            tspans = [text_elem]
        
        cur_ty = ty
        for tsp_idx, tsp in enumerate(tspans):
            t = (tsp.text or "").strip()
            if not t: continue
            fs = float(tsp.attrib.get('font-size', base_fs))
            dy = float(tsp.attrib.get('dy', 0))
            if tsp_idx > 0:
                cur_ty += dy
            
            w = len(t) * 0.60 * fs
            anchor = tsp.attrib.get('text-anchor', text_elem.attrib.get('text-anchor', 'start'))
            tsp_x = float(tsp.attrib.get('x', tx))
            if anchor == 'middle':
                x_left = tsp_x - w / 2
                x_right = tsp_x + w / 2
            elif anchor == 'end':
                x_left = tsp_x - w
                x_right = tsp_x
            else:
                x_left = tsp_x
                x_right = tsp_x + w
            
            pad_l = x_left - rx
            pad_r = (rx + rw) - x_right
            pad_t = (cur_ty - fs * 0.8) - ry
            pad_b = (ry + rh) - cur_ty

            # Check horizontal padding for each line
            assert pad_l >= 15.9, f"Left padding violation: {pad_l:.1f}px < 16px (text='{t}')"
            assert pad_r >= 15.9, f"Right padding violation: {pad_r:.1f}px < 16px (text='{t}')"
            # For first line, check pad_t
            if tsp_idx == 0:
                assert pad_t >= 15.9, f"Top padding violation: {pad_t:.1f}px < 16px (text='{t}')"
            # For last line, check pad_b
            if tsp_idx == len(tspans) - 1:
                assert pad_b >= 15.9, f"Bottom padding violation: {pad_b:.1f}px < 16px (text='{t}')"

    print("   [PASS] All text elements fit within boxes with >= 16px padding on all sides!")
    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg("test_mistakes.svg")
