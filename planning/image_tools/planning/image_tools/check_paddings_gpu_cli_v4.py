import xml.etree.ElementTree as ET

# Strict padding and gap auditor for GPU CLI infographic v4

boxes = {
    "cli.py": {
        "box": (40, 132, 1000, 72), # x, y, w, h
        "icon": (56, 140, 56, 56),
        "lines": [
            ("cli.py: Click group, output formatting and exit codes", 28, 128, 176, False)
        ]
    },
    "collect.py": {
        "box": (40, 244, 1000, 90),
        "icon": (56, 261, 56, 56),
        "lines": [
            ("collect.py: per-host executor over SSH, an agent or Redfish, ", 24, 128, 280, False),
            ("with timeout and bounded concurrency", 24, 128, 310, False)
        ]
    },
    "parsers.py": {
        "box": (56, 390, 968, 264),
        "icon": (72, 406, 56, 56),
        "lines": [
            ("parsers.py: pure functions turning nvidia-smi CSV ", 24, 144, 426, False),
            ("and dcgmi output into frozen dataclasses ", 24, 144, 452, False),
            ("(a pure function answers from its inputs alone: ", 24, 144, 478, False),
            ("no network, no clock, no randomness)", 24, 144, 504, False),
            ("Gpu(index, name, temp_c, util_pct, ", 24, 144, 536, True),
            ("mem_used_mib, mem_total_mib, ecc_uncorrected); ", 24, 144, 560, True),
            ("_int maps empty, [N/A] and [Not Supported] to None; ", 24, 144, 584, True),
            ("a line without exactly 7 columns raises ", 24, 144, 608, True),
            ("ValueError unexpected nvidia-smi columns", 24, 144, 632, True)
        ]
    },
    "rules.py": {
        "box": (56, 694, 968, 154),
        "icon": (72, 708, 56, 56),
        "lines": [
            ("rules.py: evaluate(gpus, expected=8, max_temp=85)", 26, 144, 732, False),
            ("problems for: expected 8 GPUs but found a different count; ", 24, 144, 766, False),
            ("temp above 85; uncorrected ECC non-zero; ", 24, 144, 792, False),
            ("plus XID in a set of known codes", 24, 144, 818, False)
        ]
    },
    "models.py": {
        "box": (1080, 132, 480, 96),
        "icon": (1096, 152, 56, 56),
        "lines": [
            ("models.py: dataclasses ", 26, 1172, 172, False),
            ("or pydantic models", 26, 1172, 204, False)
        ]
    },
    "exit_0": {
        "box": (1100, 288, 440, 112),
        "icon": (1116, 316, 56, 56),
        "lines": [
            ("0 all GPUs healthy", 28, 1188, 354, False)
        ]
    },
    "exit_1": {
        "box": (1100, 436, 440, 112),
        "icon": (1116, 464, 56, 56),
        "lines": [
            ("1 usage or ", 26, 1188, 482, False),
            ("runtime failure", 26, 1188, 514, False)
        ]
    },
    "exit_3": {
        "box": (1100, 584, 440, 112),
        "icon": (1116, 612, 56, 56),
        "lines": [
            ("3 any GPU unhealthy", 28, 1188, 650, False)
        ]
    },
    "exit_4": {
        "box": (1100, 732, 440, 112),
        "icon": (1116, 760, 56, 56),
        "lines": [
            ("4 partial ", 26, 1188, 778, False),
            ("collection failure", 26, 1188, 810, False)
        ]
    },
    "Test strip": {
        "box": (40, 904, 1520, 120),
        "icon": (56, 936, 56, 56),
        "lines": [
            ("canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, ", 24, 136, 940, False),
            ("empty output, missing GPU; then CliRunner with a stubbed executor ", 24, 136, 970, False),
            ("asserting exit codes and JSON shape", 24, 136, 1000, False)
        ]
    },
    "Bottom bar": {
        "box": (40, 1064, 1520, 80),
        "icon": (56, 1076, 56, 56),
        "lines": [
            ("Parser, rules, executor and CLI stay separate", 28, 800 - 0.5 * len("Parser, rules, executor and CLI stay separate") * 0.6 * 28, 1114, False)
        ]
    }
}

print("=== CHECKING ALL TEXT PADDINGS AND ICON GAPS ===")
all_pass = True
for name, data in boxes.items():
    bx, by, bw, bh = data["box"]
    icon = data.get("icon")
    if icon:
        ix, iy, iw, ih = icon
        icon_gap = min(l[2] - (ix + iw) for l in data["lines"])
        ok_icon = icon_gap >= 16
        if not ok_icon:
            all_pass = False
        print(f"[{'PASS' if ok_icon else 'FAIL'}] {name} icon gap: {icon_gap:.1f}px (need >= 16)")
    
    for text, fs, tx, ty, is_mono in data["lines"]:
        factor = 0.62 if is_mono else 0.6
        tw = len(text) * factor * fs
        ascent = fs * 0.8
        descent = fs * 0.25
        
        left_pad = tx - bx
        right_pad = (bx + bw) - (tx + tw)
        top_pad = (ty - ascent) - by
        bot_pad = (by + bh) - (ty + descent)
        
        ok = left_pad >= 16 and right_pad >= 16 and top_pad >= 14 and bot_pad >= 14
        if not ok:
            all_pass = False
        print(f"  [{'PASS' if ok else 'FAIL'}] '{text[:35]}...': left={left_pad:.1f}, right={right_pad:.1f}, top={top_pad:.1f}, bot={bot_pad:.1f}")

assert all_pass, "Some paddings failed!"
print("\nALL STRICT PADDING CHECKS PASSED!")
