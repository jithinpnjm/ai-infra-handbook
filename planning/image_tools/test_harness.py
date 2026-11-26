import xml.etree.ElementTree as ET
import re

EXPECTED_LABELS = [
    "Dedicated endpoint lifecycle as a state machine",
    "disabled",
    "enabled",
    "deleted",
    "create (from nothing) leads to disabled: validate the spec before any GPU is reserved",
    "enable: disabled to enabled: data plane starts replicas",
    "disable: enabled to disabled: traffic stops, replicas scale to zero, spec kept",
    "update: allowed in either state, state unchanged, may start a rollout",
    "delete: only from disabled: forces a deliberate two-step removal",
    "rejects a GPU type outside the four public choices, a region outside EU and US, fewer than one GPU per replica, and a maximum below the minimum; a bad request costs only a rejected call",
    "control plane keeps reading desired state, looking at what is running and taking the smallest step that closes the gap",
    "control plane holds spec and lifecycle and sends desired state to the EU and US regional data planes; replicas pull weights from the weights hub; client traffic goes through the router to replicas"
]

FORBIDDEN_WORDS = [
    'orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow',
    'cylinder', 'folder', 'callout', 'sub-line', 'subline', 'takeaway'
]

def validate_svg(svg_content):
    root = ET.fromstring(svg_content)
    
    # 1. Structure
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    assert first_tag == "title", f"First child must be title, got {first_tag}"
    assert second_tag == "desc", f"Second child must be desc, got {second_tag}"
    
    # 2. Canvas
    vb = root.attrib.get("viewBox").split()
    W = float(vb[2])
    H = float(vb[3])
    width = float(root.attrib.get("width"))
    height = float(root.attrib.get("height"))
    assert W == 1600, f"W={W} != 1600"
    assert 900 <= H <= 1200, f"H={H} not between 900 and 1200"
    assert width == 1600, f"width={width} != 1600"
    assert height == H, f"height={height} != H={H}"
    
    # 3. Text elements & font sizes
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        fs = float(elem.attrib.get('font-size', '0'))
        assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
        text_elements.append((full_text, fs))
        
    print(f"Total text elements found: {len(text_elements)}")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"  {i:2d}. [{fs:2.0f}px] {t}")
        
    found_texts = [t for t, fs in text_elements]
    
    # 4. Expected labels match exactly
    for exp in EXPECTED_LABELS:
        cnt = found_texts.count(exp)
        assert cnt == 1, f"Expected '{exp}' count {cnt} != 1!"
        print(f"  [OK] '{exp}' count = 1")
        
    extras = [t for t in found_texts if t not in EXPECTED_LABELS]
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    assert len(found_texts) == len(EXPECTED_LABELS), f"Count {len(found_texts)} != {len(EXPECTED_LABELS)}"
    
    # 5. Forbidden words
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in FORBIDDEN_WORDS:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
            
    # 6. Colors
    assert '#f5f8f5' in svg_content, "Missing #f5f8f5 background"
    assert '#303a36' in svg_content, "Missing #303a36 text color"
    assert '#207448' in svg_content, "Missing #207448 main green"
    assert '#e8f1ea' in svg_content, "Missing #e8f1ea light green panel"
    oranges = re.findall(r'#db8129', svg_content, re.IGNORECASE)
    assert 1 <= len(oranges) <= 5, f"Unexpected orange count: {len(oranges)}"
    
    print("\nALL HARNESS CHECKS PASSED!")
    return True

if __name__ == "__main__":
    print("Test harness loaded.")
