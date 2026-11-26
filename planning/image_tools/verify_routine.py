import xml.etree.ElementTree as ET
import re

def verify_all(svg_path):
    print(f"=== VERIFYING {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # 1. Structure
    children = list(root)
    assert children[0].tag.endswith('title'), "First child must be title"
    assert children[1].tag.endswith('desc'), "Second child must be desc"
    print("1. Title and Desc structure: PASS")
    
    # 2. Dimensions
    width = root.attrib.get('width')
    height = root.attrib.get('height')
    viewBox = root.attrib.get('viewBox')
    assert width == "1600", f"Width {width} != 1600"
    vb = [float(x) for x in viewBox.split()]
    assert vb[2] == 1600, f"viewBox width {vb[2]} != 1600"
    assert 900 <= vb[3] <= 1200, f"viewBox height {vb[3]} not in [900, 1200]"
    assert float(height) == vb[3], f"Height {height} != viewBox height {vb[3]}"
    print(f"2. Dimensions width={width}, height={height}, viewBox={viewBox}: PASS")
    
    # 3. Text and font sizes
    raw = open(svg_path).read()
    font_sizes = [float(fs) for fs in re.findall(r'font-size="([^"]+)"', raw)]
    assert min(font_sizes) >= 24, f"Minimum font size {min(font_sizes)} < 24"
    print(f"3. Font sizes: min={min(font_sizes)}, max={max(font_sizes)}: PASS")
    
    # 4. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    text_nodes = []
    for elem in root.iter():
        if elem.tag.endswith('text'):
            full = "".join(elem.itertext()).strip()
            full = re.sub(r'\s+', ' ', full)
            text_nodes.append(full)
    
    for t in text_nodes:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'"
    print("4. Forbidden style words in text: NONE (PASS)")
    
    # 5. Required content labels
    required_labels = [
        "A four-week practice routine",
        "Language basics",
        "Dicts, counters, sorting, strings, the harness",
        "Time: 5 sessions of 1 hour",
        "Core patterns",
        "Hash maps, two pointers, sliding window, stacks",
        "Time: 4 sessions of 75 minutes",
        "Heaps, intervals, binary search, graphs",
        "Full mock rounds",
        "Two problems in 60 minutes, once recorded",
        "Time: 3 mocks of 90 minutes",
        "Keep a bug log: harness-found bugs are what to practise on",
        "End-of-week test",
        "Practise the process under time pressure."
    ]
    
    print("\nText nodes found in SVG:")
    for i, t in enumerate(text_nodes, 1):
        print(f"  {i:2d}: '{t}'")
        
    for req in required_labels:
        cnt = text_nodes.count(req)
        print(f"Checking '{req}': count = {cnt}")
        assert cnt >= 1, f"Missing required label: '{req}'"
    print("5. Required labels check: PASS")
    
    # 6. Colors
    assert "#f5f8f5" in raw, "Light background #f5f8f5 missing"
    assert "#303a36" in raw, "Text #303a36 missing"
    assert "#207448" in raw, "Main green #207448 missing"
    assert "#e8f1ea" in raw, "Light green panels #e8f1ea missing"
    assert "#db8129" in raw, "Orange #db8129 missing"
    print("6. Color palette: PASS")

if __name__ == '__main__':
    verify_all("test_routine.svg")
