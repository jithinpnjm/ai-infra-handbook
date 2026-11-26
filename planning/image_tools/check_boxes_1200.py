import xml.etree.ElementTree as ET

# Canvas H = 1200
boxes_1200 = [
    {
        "name": "Command Banner",
        "box": (50, 160, 1500, 68),
        "lines": [
            ("curl --trace-ascii trace_file http://www.example.org/", "mono", 24, 800 - (51 * 24 * 0.62)/2, 202)
        ]
    },
    {
        "name": "Band 1 Header",
        "box": (50, 252, 750, 68),
        "lines": [
            ("curl's own notes, marked ==", "sans", 30, 185, 300)
        ]
    },
    {
        "name": "Band 1 Body",
        "box": (50, 252, 750, 224),
        "lines": [
            ("== Info: Trying 93.184.216.34...", "mono", 24, 75, 350),
            ("== Info: TCP_NODELAY set", "mono", 24, 75, 384),
            ("== Info: Connected to www.example.org ", "mono", 24, 75, 418),
            ("(93.184.216.34) port 80 (#0)", "mono", 24, 75, 450)
        ]
    },
    {
        "name": "Band 2 Header",
        "box": (50, 500, 750, 68),
        "lines": [
            ("request sent, marked =>", "sans", 30, 185, 548)
        ]
    },
    {
        "name": "Band 2 Body",
        "box": (50, 500, 750, 272),
        "lines": [
            ("=> Send header, 79 bytes (0x4f)", "mono", 24, 75, 598),
            ("GET / HTTP/1.1", "mono", 24, 75, 630),
            ("Host: www.example.org", "mono", 24, 75, 662),
            ("User-Agent: curl/7.58.0", "mono", 24, 75, 694),
            ("Accept: */*", "mono", 24, 75, 726)
        ]
    },
    {
        "name": "Band 3 Header",
        "box": (50, 796, 750, 68),
        "lines": [
            ("reply received, marked <=", "sans", 30, 185, 844)
        ]
    },
    {
        "name": "Band 3 Body",
        "box": (50, 796, 750, 290),
        "lines": [
            ("<= Recv header, 17 bytes", "mono", 24, 75, 894),
            ("HTTP/1.1 200 OK", "mono", 24, 75, 924),
            ("Accept-Ranges: bytes", "mono", 24, 75, 954),
            ("Age: 17629", "mono", 24, 75, 984),
            ("Content-Length: 1256", "mono", 24, 75, 1014),
            ("<= Recv data, 1256 bytes (0x4e8)", "mono", 24, 75, 1058)
        ]
    },
    {
        "name": "Callout 1",
        "box": (830, 252, 720, 194),
        "lines": [
            ("The hex numbers such as 0000: are ", "sans", 24, 940, 298),
            ("offsets curl adds to track how many ", "sans", 24, 940, 332),
            ("bytes moved; they are not part ", "sans", 24, 940, 366),
            ("of the data", "sans", 24, 940, 400)
        ]
    },
    {
        "name": "Callout 2",
        "box": (830, 470, 720, 180),
        "lines": [
            ("curl does not count headers toward ", "sans", 24, 940, 522),
            ("the offsets, so offsets restart at ", "sans", 24, 940, 556),
            ("zero after the headers", "sans", 24, 940, 590)
        ]
    },
    {
        "name": "Callout 3",
        "box": (830, 674, 720, 188),
        "lines": [
            ("A blank line marks the end of the ", "sans", 24, 940, 728),
            ("headers; everything after it is ", "sans", 24, 940, 762),
            ("the requested document", "sans", 24, 940, 796)
        ]
    },
    {
        "name": "Callout 4",
        "box": (830, 886, 720, 200),
        "lines": [
            ("The operating system and network ", "sans", 24, 940, 932),
            ("handle headers and document ", "sans", 24, 940, 966),
            ("identically; the split exists only ", "sans", 24, 940, 1000),
            ("inside the user-space curl program", "sans", 24, 940, 1034)
        ]
    },
    {
        "name": "Bottom Bar",
        "box": (50, 1110, 1500, 68),
        "lines": [
            ("Read it from the top: notes, then the request, then the reply", "sans", 26, 800 - (59 * 26 * 0.6)/2, 1152)
        ]
    }
]

all_passed = True
for b in boxes_1200:
    bx, by, bw, bh = b["box"]
    b_right = bx + bw
    b_bottom = by + bh
    print(f"\nChecking box: {b['name']} ({bx}, {by}, {bw}, {bh})")
    for txt, ftype, fs, lx, ly in b["lines"]:
        mult = 0.62 if ftype == "mono" else 0.60
        text_w = len(txt) * fs * mult
        text_top = ly - fs
        text_bottom = ly + 4 # descender
        text_right = lx + text_w
        
        pad_left = lx - bx
        pad_right = b_right - text_right
        pad_top = text_top - by
        pad_bottom = b_bottom - text_bottom
        
        print(f"  Line: '{txt[:30]}...' w={text_w:.1f} pads: L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f}")
        
        if pad_left < 16:
            print(f"    FAIL: pad_left {pad_left:.1f} < 16")
            all_passed = False
        if pad_right < 16:
            print(f"    FAIL: pad_right {pad_right:.1f} < 16")
            all_passed = False
        if pad_top < 16:
            print(f"    FAIL: pad_top {pad_top:.1f} < 16")
            all_passed = False
        if pad_bottom < 16:
            print(f"    FAIL: pad_bottom {pad_bottom:.1f} < 16")
            all_passed = False

if all_passed:
    print("\n[ALL PADDINGS PASS >= 16px!]")
else:
    print("\n[FAILURES FOUND]")
