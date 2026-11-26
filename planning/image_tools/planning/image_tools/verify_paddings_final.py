import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_final_candidate.svg")
root = tree.getroot()

boxes = [
    # Main Title
    {"name": "Title", "box": (40, 0, 1520, 104), "align": "middle", "mono": False,
     "lines": [("Numeric types and the quiet traps they hide", 48, 64, 800)]},
    
    # Left Type 1: int
    {"name": "int", "box": (54, 118, 832, 88), "align": "left", "mono": True,
     "lines": [
         ("int: arbitrary precision, no overflow;", 24, 158, 140),
         ("0x1f, 0o17, 0b101, 1_000_000", 24, 186, 140)
     ]},

    # Left Type 2: float
    {"name": "float", "box": (54, 214, 832, 144), "align": "left", "mono": True,
     "lines": [
         ("float: IEEE 754 double, about 15 to 17", 24, 254, 140),
         ("significant digits; 0.1 + 0.2 != 0.3,", 24, 282, 140),
         ("use math.isclose; float(\"inf\"),", 24, 310, 140),
         ("nan never equals itself", 24, 338, 140)
     ]},

    # Left Type 3: complex
    {"name": "complex", "box": (54, 366, 832, 64), "align": "left", "mono": True,
     "lines": [
         ("complex: 3 + 4j, rarely used in infra", 24, 406, 140)
     ]},

    # Left Type 4: bool
    {"name": "bool", "box": (54, 438, 832, 88), "align": "left", "mono": True,
     "lines": [
         ("bool: subclass of int,", 24, 478, 140),
         ("True == 1, True + True == 2", 24, 506, 140)
     ]},

    # Left Type 5: decimal.Decimal
    {"name": "decimal.Decimal", "box": (54, 534, 832, 88), "align": "left", "mono": True,
     "lines": [
         ("decimal.Decimal: exact decimal arithmetic", 24, 574, 140),
         ("for money and billing; construct from strings", 24, 602, 140)
     ]},

    # Left Type 6: fractions.Fraction
    {"name": "fractions.Fraction", "box": (54, 630, 832, 64), "align": "left", "mono": True,
     "lines": [
         ("fractions.Fraction: exact rational numbers", 24, 670, 140)
     ]},

    # Right Header: Operators
    {"name": "Operators Header", "box": (956, 114, 588, 62), "align": "left", "mono": False,
     "lines": [
         ("Operators", 30, 160, 1038)
     ]},

    # Op 1
    {"name": "Op 1", "box": (956, 182, 588, 56), "align": "left", "mono": True,
     "lines": [
         ("/ is always true division (float)", 24, 222, 976)
     ]},

    # Op 2
    {"name": "Op 2", "box": (956, 244, 588, 84), "align": "left", "mono": True,
     "lines": [
         ("// floors toward negative", 24, 284, 976),
         ("infinity: -7 // 2 == -4", 24, 312, 976)
     ]},

    # Op 3
    {"name": "Op 3", "box": (956, 334, 588, 56), "align": "left", "mono": True,
     "lines": [
         ("% takes the sign of the divisor", 24, 374, 976)
     ]},

    # Op 4
    {"name": "Op 4", "box": (956, 396, 588, 56), "align": "left", "mono": True,
     "lines": [
         ("divmod(a, b)", 24, 436, 976)
     ]},

    # Op 5
    {"name": "Op 5", "box": (956, 458, 588, 84), "align": "left", "mono": True,
     "lines": [
         ("round() rounds half to even:", 24, 498, 976),
         ("round(2.5) == 2", 24, 526, 976)
     ]},

    # Op 6
    {"name": "Op 6", "box": (956, 548, 588, 56), "align": "left", "mono": True,
     "lines": [
         ("chained comparison 1 <= x < 10", 24, 588, 976)
     ]},

    # Op 7
    {"name": "Op 7", "box": (956, 610, 588, 84), "align": "left", "mono": True,
     "lines": [
         ("bitwise & | ^ ~ << >> for IP", 24, 650, 976),
         ("and mask: 0xFF & addr", 24, 678, 976)
     ]},

    # Op 8
    {"name": "Op 8", "box": (956, 700, 588, 80), "align": "left", "mono": True,
     "lines": [
         ("random is not for security,", 24, 740, 976),
         ("use secrets", 24, 764, 976)
     ]},

    # Ex 1
    {"name": "Ex 1", "box": (40, 830, 740, 108), "align": "left", "mono": True,
     "lines": [
         ("disk_bytes / gib with gib = 1024 ** 3", 24, 870, 120),
         ("gives 3577.0 GiB for", 24, 896, 120),
         ("3_840_755_982_336 bytes", 24, 922, 120)
     ]},

    # Ex 2
    {"name": "Ex 2", "box": (820, 830, 740, 108), "align": "left", "mono": True,
     "lines": [
         ("free_pct = 100 * free / total", 24, 870, 900),
         ("if total else 0.0 guards divide by zero", 24, 898, 900)
     ]},

    # Ex 3
    {"name": "Ex 3", "box": (40, 950, 740, 76), "align": "left", "mono": True,
     "lines": [
         ("timeout = base * 2 ** attempt", 24, 992, 120)
     ]},

    # Ex 4
    {"name": "Ex 4", "box": (820, 950, 740, 76), "align": "left", "mono": True,
     "lines": [
         ("pages, rem = divmod(total_items, 100)", 24, 992, 900)
     ]},

    # Takeaway Bar
    {"name": "Takeaway", "box": (40, 1066, 1520, 94), "align": "middle", "mono": False,
     "lines": [
         ("Compare floats with tolerance, use // versus / on purpose,", 24, 1106, 800),
         ("remember bool is an int, and use the ipaddress module instead of string IP arithmetic", 24, 1138, 800)
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
print("\n>>> ALL BOXES PASSED STRICT >= 16PX PADDING! <<<")
