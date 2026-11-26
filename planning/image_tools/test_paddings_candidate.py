#!/usr/bin/env python3
import xml.etree.ElementTree as ET

def check_paddings():
    tree = ET.parse("candidate.svg")
    root = tree.getroot()

    # Rule:
    # Estimate widths conservatively: sans 0.6 x font-size per character, monospace 0.62 x font-size per character.
    # Every text line must fit inside its box with at least 16 px padding.
    
    # We will list every visual line of text, its font type, font size, the width of the containing box,
    # and the clearance (left and right padding).
    
    checks = [
        # (text, font_type, font_size, box_width, description)
        ("Where facts about a GPU host come from,", "sans", 48, 1600, "Title Line 1"),
        ("and how to read each safely", "sans", 48, 1600, "Title Line 2"),
        ("Source", "sans", 30, 340, "Table Header 1"),
        ("How to read", "sans", 30, 700, "Table Header 2"),
        ("Care", "sans", 30, 480, "Table Header 3"),
        ("nvidia-smi", "mono", 30, 340, "Row 1 Source"),
        ("nvidia-smi --query-gpu=index,name,", "mono", 24, 700, "Row 1 Col 2 L1"),
        ("temperature.gpu,utilization.gpu,", "mono", 24, 700, "Row 1 Col 2 L2"),
        ("memory.used,memory.total,power.draw,", "mono", 24, 700, "Row 1 Col 2 L3"),
        ("ecc.errors.uncorrected.volatile.total ", "mono", 24, 700, "Row 1 Col 2 L4"),
        ("--format=csv,noheader,nounits: one CSV line ", "mono", 24, 700, "Row 1 Col 2 L5"),
        ("per GPU; nvidia-smi -q -x for XML", "mono", 24, 700, "Row 1 Col 2 L6"),
        ("parse with csv module; treat ", "sans", 24, 480, "Row 1 Col 3 L1"),
        ("[N/A] and [Not Supported] as ", "sans", 24, 480, "Row 1 Col 3 L2"),
        ("missing; each call ", "sans", 24, 480, "Row 1 Col 3 L3"),
        ("initialises NVML and can ", "sans", 24, 480, "Row 1 Col 3 L4"),
        ("take a second on a busy host", "sans", 24, 480, "Row 1 Col 3 L5"),
        ("NVML bindings", "sans", 30, 340, "Row 2 Source"),
        ("pynvml and nvidia-ml-py: ", "mono", 24, 700, "Row 2 Col 2 L1"),
        ("nvmlDeviceGetTemperature, ", "mono", 24, 700, "Row 2 Col 2 L2"),
        ("nvmlDeviceGetUtilizationRates, ", "mono", 24, 700, "Row 2 Col 2 L3"),
        ("nvmlDeviceGetMemoryInfo, ", "mono", 24, 700, "Row 2 Col 2 L4"),
        ("nvmlDeviceGetPowerUsage; ", "mono", 24, 700, "Row 2 Col 2 L5"),
        ("throttling reasons and XID events", "mono", 24, 700, "Row 2 Col 2 L6"),
        ("continuous monitoring", "sans", 24, 480, "Row 2 Col 3"),
        ("DCGM", "sans", 30, 340, "Row 3 Source"),
        ("Python bindings for health checks ", "sans", 24, 700, "Row 3 Col 2 L1"),
        ("and diagnostics; dcgmi diag -r 1|2|3 ", "sans", 24, 700, "Row 3 Col 2 L2"),
        ("as a subprocess", "sans", 24, 700, "Row 3 Col 2 L3"),
        ("-", "sans", 24, 480, "Row 3 Col 3"),
        ("/proc and /sys", "mono", 30, 340, "Row 4 Source"),
        ("/proc/meminfo, /proc/pressure/*, ", "mono", 24, 700, "Row 4 Col 2 L1"),
        ("/sys/class/infiniband/*/ports/*/counters/*, ", "mono", 24, 700, "Row 4 Col 2 L2"),
        ("/sys/class/net/*/statistics/*", "mono", 24, 700, "Row 4 Col 2 L3"),
        ("dependency-free; files can ", "sans", 24, 480, "Row 4 Col 3 L1"),
        ("vanish between listing ", "sans", 24, 480, "Row 4 Col 3 L2"),
        ("and reading", "sans", 24, 480, "Row 4 Col 3 L3"),
        # Subprocess rules strip: box width 1520, icon 56px at x=76. Text starts at x=170 -> text box width = 1520 - 130 = 1390
        ("argument list, timeout=, check=False so you handle the return code, capture stderr, ", "sans", 24, 1390, "Subp L1"),
        ("never shell=True with uncontrolled input; subprocess.run timeout kills the child ", "sans", 24, 1390, "Subp L2"),
        ("but not its descendants: start_new_session=True then os.killpg; ", "sans", 24, 1390, "Subp L3"),
        ("in long-running agents call wait() to avoid zombies", "sans", 24, 1390, "Subp L4"),
        # Design strip: box width 1520, icon 56px at x=76. Text starts at x=170 -> text box width = 1390
        ("wrap each source in a function returning a typed result such as a dataclass, ", "sans", 24, 1390, "Design L1"),
        ("so the CLI, exporter and agent share one collection layer and tests feed canned output", "sans", 24, 1390, "Design L2"),
        # Bottom bar: box width 1520
        ("Read in a way that survives odd output, slow tools and vanishing files", "sans", 24, 1520, "Bottom bar")
    ]

    all_passed = True
    print("\nChecking conservative line widths and paddings:")
    for text, ftype, fsize, bwidth, desc in checks:
        mult = 0.62 if ftype == "mono" else 0.60
        est_w = len(text) * fsize * mult
        pad = (bwidth - est_w) / 2
        status = "OK" if pad >= 16 else "FAIL"
        if pad < 16:
            all_passed = False
        print(f"[{status}] pad={pad:5.1f}px (box={bwidth:4d}, est_w={est_w:6.1f}px) : {desc} '{text[:35]}...'")

    assert all_passed, "Some lines failed min 16px padding!"
    print("\nALL LINES SATISFY >= 16px PADDING RULE! (PASS)")

if __name__ == "__main__":
    check_paddings()
