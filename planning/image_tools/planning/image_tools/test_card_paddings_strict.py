import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# Map each text element to its parent/surrounding card box
# Let's extract all rects and texts
rects = []
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(elem.attrib.get('x', '0'))
    y = float(elem.attrib.get('y', '0'))
    w = float(elem.attrib.get('width', '0'))
    h = float(elem.attrib.get('height', '0'))
    if w > 0 and h > 0 and (w < 1600 or h < 1200): # exclude background
        rects.append((x, y, w, h))

print(f"Total rects found: {len(rects)}")

# Define all text lines and their enclosing bounding boxes
boxes = [
    # Main Title
    {"name": "Title", "box": (40, 20, 1520, 75), "align": "middle", "mono": False,
     "lines": [("Numeric types and the quiet traps they hide", 48, 70, 800)]},
    
    # Left Type 1: int
    {"name": "int", "box": (54, 124, 832, 84), "align": "left", "mono": True,
     "lines": [
         ("int: arbitrary precision, no overflow;", 24, 160, 140),
         ("0x1f, 0o17, 0b101, 1_000_000", 24, 188, 140)
     ]},

    # Left Type 2: float
    {"name": "float", "box": (54, 218, 832, 140), "align": "left", "mono": True,
     "lines": [
         ("float: IEEE 754 double, about 15 to 17", 24, 254, 140),
         ("significant digits; 0.1 + 0.2 != 0.3,", 24, 282, 140),
         ("use math.isclose; float(\"inf\"),", 24, 310, 140),
         ("nan never equals itself", 24, 338, 140)
     ]},

    # Left Type 3: complex
    {"name": "complex", "box": (54, 368, 832, 60), "align": "left", "mono": True,
     "lines": [
         ("complex: 3 + 4j, rarely used in infra", 24, 406, 140)
     ]},

    # Left Type 4: bool
    {"name": "bool", "box": (54, 438, 832, 84), "align": "left", "mono": True,
     "lines": [
         ("bool: subclass of int,", 24, 474, 140),
         ("True == 1, True + True == 2", 24, 502, 140)
     ]},

    # Left Type 5: decimal.Decimal
    {"name": "decimal.Decimal", "box": (54, 532, 832, 88), "align": "left", "mono": True,
     "lines": [
         ("decimal.Decimal: exact decimal arithmetic", 24, 568, 140),
         ("for money and billing; construct from strings", 24, 596, 140)
     ]},

    # Left Type 6: fractions.Fraction
    {"name": "fractions.Fraction", "box": (54, 630, 832, 60), "align": "left", "mono": True,
     "lines": [
         ("fractions.Fraction: exact rational numbers", 24, 668, 140)
     ]},

    # Right Header: Operators
    {"name": "Operators Header", "box": (956, 124, 588, 56), "align": "left", "mono": False,
     "lines": [
         ("Operators", 30, 162, 1040)
     ]},

    # Op 1
    {"name": "Op 1", "box": (956, 188, 588, 52), "align": "left", "mono": True,
     "lines": [
         ("/ is always true division (float)", 24, 222, 976)
     ]},

    # Op 2
    {"name": "Op 2", "box": (956, 246, 588, 78), "align": "left", "mono": True,
     "lines": [
         ("// floors toward negative", 24, 278, 976),
         ("infinity: -7 // 2 == -4", 24, 306, 976)
     ]},

    # Op 3
    {"name": "Op 3", "box": (956, 330, 588, 52), "align": "left", "mono": True,
     "lines": [
         ("% takes the sign of the divisor", 24, 364, 976)
     ]},

    # Op 4
    {"name": "Op 4", "box": (956, 388, 588, 52), "align": "left", "mono": True,
     "lines": [
         ("divmod(a, b)", 24, 422, 976)
     ]},

    # Op 5
    {"name": "Op 5", "box": (956, 446, 588, 78), "align": "left", "mono": True,
     "lines": [
         ("round() rounds half to even:", 24, 478, 976),
         ("round(2.5) == 2", 24, 506, 976)
     ]},

    # Op 6
    {"name": "Op 6", "box": (956, 530, 588, 52), "align": "left", "mono": True,
     "lines": [
         ("chained comparison 1 <= x < 10", 24, 564, 976)
     ]},

    # Op 7
    {"name": "Op 7", "box": (956, 588, 588, 78), "align": "left", "mono": True,
     "lines": [
         ("bitwise & | ^ ~ << >> for IP", 24, 620, 976),
         ("and mask: 0xFF & addr", 24, 648, 976)
     ]},

    # Op 8
    {"name": "Op 8", "box": (956, 672, 588, 78), "align": "left", "mono": True,
     "lines": [
         ("random is not for security,", 24, 704, 976),
         ("use secrets", 24, 732, 976)
     ]},

    # Ex 1
    {"name": "Ex 1", "box": (40, 820, 740, 94), "align": "left", "mono": True,
     "lines": [
         ("disk_bytes / gib with gib = 1024 ** 3", 24, 856, 128),
         ("gives 3577.0 GiB for 3_840_755_982_336 bytes", 24, 884, 128)
     ]},

    # Ex 2
    {"name": "Ex 2", "box": (820, 820, 740, 94), "align": "left", "mono": True,
     "lines": [
         ("free_pct = 100 * free / total", 24, 856, 908),
         ("if total else 0.0 guards divide by zero", 24, 884, 908)
     ]},

    # Ex 3
    {"name": "Ex 3", "box": (40, 934, 740, 76), "align": "left", "mono": True,
     "lines": [
         ("timeout = base * 2 ** attempt", 24, 980, 128)
     ]},

    # Ex 4
    {"name": "Ex 4", "box": (820, 934, 740, 76), "align": "left", "mono": True,
     "lines": [
         ("pages, rem = divmod(total_items, 100)", 24, 980, 908)
     ]},

    # Takeaway Bar
    {"name": "Takeaway", "box": (40, 1050, 1520, 110), "align": "middle", "mono": False,
     "lines": [
         ("Compare floats with tolerance, use // versus / on purpose,", 24, 1092, 800),
         ("remember bool is an int, and use the ipaddress module instead of string IP arithmetic", 24, 1124, 800)
     ]}
]

all_pass = True
for b in boxes:
    bx, by, bw, bh = b["box"]
    factor = 0.62 if b["mono"] else 0.6
    print(f"\nChecking {b['name']}: box=({bx}, {by}, {bw}, {bh})")
    for txt, fs, baseline, anchor_x in b["lines"]:
        line_w = len(txt) * fs * factor
        if b["align"] == "middle":
            t_left = anchor_x - line_w / 2
            t_right = anchor_x + line_w / 2
        elif b["align"] == "right":
            t_left = anchor_x - line_w
            t_right = anchor_x
        else:
            t_left = anchor_x
            t_right = anchor_x + line_w
        
        pad_l = t_left - bx
        pad_r = (bx + bw) - t_right
        pad_t = (baseline - fs) - by
        pad_b = (by + bh) - baseline
        
        ok_l = pad_l >= 16
        ok_r = pad_r >= 16
        ok_t = pad_t >= 16
        ok_b = pad_b >= 16
        
        if not (ok_l and ok_r and ok_t and ok_b):
            all_pass = False
            print(f"  FAILED: '{txt}'")
            print(f"    pad_l={pad_l:.1f} (>=16: {ok_l}), pad_r={pad_r:.1f} (>=16: {ok_r}), pad_t={pad_t:.1f} (>=16: {ok_t}), pad_b={pad_b:.1f} (>=16: {ok_b})")
        else:
            print(f"  OK: '{txt[:30]}...' pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")

assert all_pass, "Some boxes failed padding check!"
print("\nALL BOXES PASSED STRICT >= 16PX PADDING!")
