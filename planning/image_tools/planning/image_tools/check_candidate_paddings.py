import xml.etree.ElementTree as ET

def check_paddings(svg_path):
    print("Checking text paddings...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Boxes:
    # 1. Address A: rect x=64, y=170, w=460, h=86 -> right edge 524
    # text x=156, text: "Address A: " (11 chars), "10.20.37.130" (12 chars)
    # 12 * 0.6 * 28 = 201.6 px. 156 + 201.6 = 357.6 < 524 (padding = 166.4 px)
    # y=206, baseline dy=34 -> y=240. Bottom edge 256 (padding = 16 px).
    
    # 2. Mask: rect x=548, y=170, w=508, h=86 -> right edge 1056
    # text x=640, text: "(third octet 252)" (17 chars)
    # 17 * 0.6 * 28 = 285.6 px. 640 + 285.6 = 925.6 < 1056 (padding = 130.4 px)
    
    # 3. A AND mask: rect x=200, y=310, w=696, h=66 -> right edge 896
    # text x=278, text: 30 chars monospace
    # 30 * 0.62 * 26 = 483.6 px. 278 + 483.6 = 761.6 < 896 (padding = 134.4 px)
    
    # 4. Address B: rect x=300, y=435, w=496, h=86 -> right edge 796
    # text x=395, text: 10 chars
    # 10 * 0.6 * 28 = 168 px. 395 + 168 = 563 < 796 (padding = 233 px)
    
    # 5. B AND mask: rect x=200, y=575, w=696, h=66 -> right edge 896
    # text x=278, padding = 134.4 px
    
    # 6. Side note: rect x=1145, y=275, w=390, h=350 -> right edge 1535
    # text x=1170, max line: "third octets 36 to 39, " (23 chars)
    # 23 * 0.6 * 26 = 358.8 px. 1170 + 358.8 = 1528.8 < 1535
    # Let's check: 1535 - 1528.8 = 6.2 px! THAT'S LESS THAN 16 PX PADDING!
    print("Warning: Line 2 in Side note has right padding 6.2 px!")
    
check_paddings("test_candidate.svg")
