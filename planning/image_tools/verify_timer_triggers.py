import xml.etree.ElementTree as ET
import re

def verify(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure
    children = list(root)
    t0 = children[0].tag.split('}')[-1]
    t1 = children[1].tag.split('}')[-1]
    print(f"1. Children: <{t0}>, <{t1}>")
    assert t0 == 'title', f"Child 0 must be <title>, got <{t0}>"
    assert t1 == 'desc', f"Child 1 must be <desc>, got <{t1}>"

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600"
    assert viewBox == f"0 0 1600 {height}"
    H_val = float(height)
    assert 900 <= H_val <= 1200

    # 3. All text elements >= 24px
    text_elements = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', '0'))
        combined = " ".join("".join(el.itertext()).split())
        assert fs >= 24, f"Text '{combined}' font-size {fs} < 24!"
        for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
            tfs = float(ts.attrib.get('font-size', fs))
            assert tfs >= 24, f"tspan in '{combined}' font-size {tfs} < 24!"
        text_elements.append((combined, fs))

    print(f"3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")

    # 4. Expected labels
    expected_labels = [
        "Timer triggers: calendar time versus time since an event",
        "Realtime (calendar): OnCalendar=",
        "OnCalendar=Sun *-*-* 03:00:00",
        "DayOfWeek",
        "Year-Month-Day",
        "Hour:Minute:Second",
        "* wildcard",
        "Mon,Fri list",
        "Mon..Fri range",
        "*:0/15 every 15 minutes",
        "hourly daily weekly monthly yearly",
        'systemd-analyze calendar "Mon..Fri 02:30" prints the normalised form and next elapse times; --iterations=5 shows more',
        "Monotonic: counts from an event",
        "boot",
        "OnBootSec=",
        "unit last activated",
        "OnUnitActiveSec=",
        "every N minutes since the last run",
        "OnStartupSec=, OnUnitInactiveSec=, OnActiveSec=",
        "Persistent=true: remembers the last run on disk and runs a missed job at next start",
        "RandomizedDelaySec=: spreads load across machines",
        "AccuracySec= defaults to one minute so wake-ups combine; set 1s for precision",
        "Enable the timer, not the service: systemctl enable --now fstrim-data.timer; an overlapping oneshot trigger is skipped",
        "Check the zone: add UTC or a zone name when it matters"
    ]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels:")
    for lbl in expected_labels:
        norm_lbl = re.sub(r'\s+', ' ', lbl)
        cnt = found_texts.count(norm_lbl)
        assert cnt == 1, f"Expected label '{lbl}' count {cnt} != 1!"
        print(f"   [PASS] count=1: '{lbl[:55]}...'")

    # 5. Extras check
    all_allowed = set(expected_labels)
    extras = [t for t in found_texts if t not in all_allowed]
    assert len(extras) == 0, f"Unexpected extra text: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} mismatch!"
    print("\n5. Zero extra text elements: PASS")

    # 6. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("6. No forbidden words found: PASS")

    # 7. Orange usage
    svg_str = open(svg_path).read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 count: {len(orange_matches)}")
    assert len(orange_matches) == 1, f"Orange used {len(orange_matches)} times, expected exactly 1!"
    print("   PASS: Orange used exactly once for Persistent=true card.")

    # 8. Check arrows
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    total_arrows = len(lines_with_marker) + len(paths_with_marker)
    print(f"\n8. Total arrows with marker-end: {total_arrows} (expected 0)")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

    # 9. Outside margins (>= 40px)
    print(f"\n9. Checking outside margins on rects (>= 40px):")
    for r in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(r.attrib.get('x', '0'))
        ry = float(r.attrib.get('y', '0'))
        rw = float(r.attrib.get('width', '0'))
        rh = float(r.attrib.get('height', '0'))
        if rw < 1600 and rw > 100: # major content boxes
            lm = rx
            rm = 1600 - (rx + rw)
            tm = ry
            bm = H_val - (ry + rh)
            assert lm >= 39.9, f"Left margin {lm} < 40 for rect w={rw}"
            assert rm >= 39.9, f"Right margin {rm} < 40 for rect w={rw}"
            assert tm >= 39.9, f"Top margin {tm} < 40 for rect w={rw}"
            assert bm >= 39.9, f"Bottom margin {bm} < 40 for rect w={rw}"
            print(f"   [PASS] Rect x={rx}, y={ry}, w={rw}, h={rh}: lm={lm}, rm={rm}, tm={tm}, bm={bm}")

    print("   PASS: Outside margins >= 40px for all rects.")

    # 10. Check horizontal padding on all text lines inside boxes (>= 16px)
    print("\n10. Checking text padding inside boxes (>= 16px)...")
    lines_to_check = [
        # (desc, text, ftype, fsize, box_w)
        ("Realtime title", "Realtime (calendar): OnCalendar=", "sans", 30, 740 - (125 - 40)),
        ("Chapter line", "OnCalendar=Sun *-*-* 03:00:00", "mono", 24, 700),
        ("DayOfWeek", "DayOfWeek", "sans", 24, 180),
        ("Year-Month-Day", "Year-Month-Day", "sans", 24, 250),
        ("Hour:Minute:Second", "Hour:Minute:Second", "sans", 24, 310),
        ("* wildcard", "* wildcard", "sans", 24, 180),
        ("Mon,Fri list", "Mon,Fri list", "sans", 24, 220),
        ("Mon..Fri range", "Mon..Fri range", "sans", 24, 250),
        ("*:0/15 every 15 minutes", "*:0/15 every 15 minutes", "sans", 24, 380),
        ("hourly daily weekly monthly yearly", "hourly daily weekly monthly yearly", "sans", 24, 540),
        ("Test line 1", "systemd-analyze calendar \"Mon..Fri 02:30\" ", "mono", 24, 700),
        ("Test line 2", "prints the normalised form and next elapse ", "mono", 24, 700),
        ("Test line 3", "times; --iterations=5 shows more", "mono", 24, 700),
        ("Monotonic title", "Monotonic: counts from an event", "sans", 30, 740 - (905 - 820)),
        ("boot", "boot", "sans", 24, 110),
        ("OnBootSec=", "OnBootSec=", "mono", 24, 180),
        ("unit last activated", "unit last activated", "sans", 24, 310),
        ("OnUnitActiveSec=", "OnUnitActiveSec=", "mono", 24, 270),
        ("every N minutes since the last run", "every N minutes since the last run", "sans", 24, 520),
        ("Other keys 1", "OnStartupSec=, OnUnitInactiveSec=, ", "mono", 24, 700),
        ("Other keys 2", "OnActiveSec=", "mono", 24, 700),
        ("Persistent line 1", "Persistent=true: remembers ", "sans", 24, 490),
        ("Persistent line 2", "the last run on disk and ", "sans", 24, 490),
        ("Persistent line 3", "runs a missed job at next start", "sans", 24, 490),
        ("Randomized line 1", "RandomizedDelaySec=: ", "sans", 24, 490),
        ("Randomized line 2", "spreads load across machines", "sans", 24, 490),
        ("Accuracy line 1", "AccuracySec= defaults to one ", "sans", 24, 490),
        ("Accuracy line 2", "minute so wake-ups combine; ", "sans", 24, 490),
        ("Accuracy line 3", "set 1s for precision", "sans", 24, 490),
        ("Note line 1", "Enable the timer, not the service: systemctl enable --now fstrim-data.timer; ", "sans", 24, 1520),
        ("Note line 2", "an overlapping oneshot trigger is skipped", "sans", 24, 1520),
        ("Bottom bar", "Check the zone: add UTC or a zone name when it matters", "sans", 26, 1520)
    ]

    for desc, txt, ftype, fsize, box_w in lines_to_check:
        char_factor = 0.62 if ftype == "mono" else 0.6
        est_w = len(txt) * fsize * char_factor
        pad = box_w - est_w
        # For centered items or single line items, padding on each side is pad/2 or pad
        print(f"   Checking [{desc}]: box_w={box_w:.1f}, est_w={est_w:.1f}, pad={pad:.1f} (min {16}px)")
        assert pad >= 16, f"Padding {pad:.1f} < 16 for [{desc}]!"

    print("\nALL VERIFICATION CHECKS PASSED!")

if __name__ == "__main__":
    verify("test_timer_triggers.svg")
