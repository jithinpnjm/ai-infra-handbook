#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

from test_audit_script import build_svg

def audit_paddings():
    svg_str = build_svg()
    root = ET.fromstring(svg_str)

    # Define all boxes with their coordinates: (x, y, w, h)
    # We will map each text element to its containing box
    boxes = {
        "title": (0, 0, 1600, 142),
        "left-panel": (40, 142, 600, 958),
        "chk-item-1": (76, 236, 528, 60),
        "chk-item-2": (76, 304, 528, 60),
        "chk-item-3": (76, 372, 528, 60),
        "chk-item-4": (76, 440, 528, 60),
        "chk-item-5": (76, 508, 528, 60),
        "chk-item-6": (76, 576, 528, 60),
        "chk-item-7": (76, 644, 528, 92),
        "arrow-area": (100, 758, 540, 190),
        "note-box": (60, 958, 560, 124),
        "right-panel": (670, 142, 890, 958),
        "questions-box": (692, 214, 846, 154),
        "card-1": (692, 384, 414, 132),
        "card-2": (1124, 384, 414, 132),
        "card-3": (692, 526, 414, 132),
        "card-4": (1124, 526, 414, 132),
        "card-5": (692, 668, 414, 132),
        "card-6": (1124, 668, 414, 132),
        "card-7": (692, 810, 414, 132),
        "card-8": (1124, 810, 414, 132),
        "card-9": (692, 952, 414, 132),
        "card-10": (1124, 952, 414, 132),
        "bottom-bar": (40, 1120, 1520, 60)
    }

    # Map text element prefixes or ids to boxes
    mapping = [
        ("Baseline and static audit", "title"),
        ("Record a baseline", "left-panel"),
        ("the 60-second checklist", "chk-item-1"),
        ("sysctl -a", "chk-item-2"),
        ("lscpu", "chk-item-3"),
        ("lspci -vv", "chk-item-4"),
        ("nvidia-smi", "chk-item-5"),
        ("firmware versions", "chk-item-6"),
        ("benchmark results", "chk-item-7"),
        ("store it with the image", "arrow-area"),
        ("If none exists", "note-box"),
        ("Static audit findings", "right-panel"),
        ("Does each component", "questions-box"),
        ("a 400 Gb NIC", "card-1"),
        ("a failed RAID", "card-2"),
        ("a GPU with a downgraded", "card-3"),
        ("stale kernel", "card-4"),
        ("IP forwarding", "card-5"),
        ("THP or governor", "card-6"),
        ("a small ulimit", "card-7"),
        ("a cgroup driver", "card-8"),
        ("debug logging left on", "card-9"),
        ("a filesystem nearly full", "card-10"),
        ("Configuration drift", "bottom-bar"),
    ]

    print("=== CHECKING PADDINGS AND BOUNDS ===")
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        
        # find matching box
        box_name = None
        for prefix, bname in mapping:
            if prefix in full_text:
                box_name = bname
                break
        
        assert box_name is not None, f"No box mapped for text: {full_text}"
        bx, by, bw, bh = boxes[box_name]

        base_fs = float(elem.attrib.get('font-size', 24))
        anchor = elem.attrib.get('text-anchor', 'start')
        elem_x = float(elem.attrib.get('x', 0))
        elem_y = float(elem.attrib.get('y', 0))

        tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
        if not tspans:
            # Single line
            t = full_text
            fs = base_fs
            # Conservative width factor: 0.62 for monospace, 0.60 for sans
            is_mono = 'monospace' in elem.attrib.get('font-family', '')
            factor = 0.62 if is_mono else 0.60
            w = len(t) * factor * fs
            if anchor == 'middle':
                xs = elem_x - w / 2
                xe = elem_x + w / 2
            elif anchor == 'end':
                xs = elem_x - w
                xe = elem_x
            else:
                xs = elem_x
                xe = elem_x + w
            
            top_y = elem_y - fs
            bot_y = elem_y + 0.25 * fs

            pad_l = xs - bx
            pad_r = (bx + bw) - xe
            pad_t = top_y - by
            pad_b = (by + bh) - bot_y

            print(f"[{box_name:14s}] '{t[:30]:30s}' pad L={pad_l:5.1f} R={pad_r:5.1f} T={pad_t:5.1f} B={pad_b:5.1f}")
            assert pad_l >= 15.9, f"Left pad {pad_l:.1f} < 16 for '{t}' in {box_name}"
            assert pad_r >= 15.9, f"Right pad {pad_r:.1f} < 16 for '{t}' in {box_name}"
            assert pad_t >= 15.9, f"Top pad {pad_t:.1f} < 16 for '{t}' in {box_name}"
            assert pad_b >= 15.9, f"Bottom pad {pad_b:.1f} < 16 for '{t}' in {box_name}"
        else:
            # Multi-line
            cur_y = elem_y
            for tsp in tspans:
                t = (tsp.text or "").strip()
                if not t:
                    continue
                fs = float(tsp.attrib.get('font-size', base_fs))
                is_mono = 'monospace' in tsp.attrib.get('font-family', elem.attrib.get('font-family', ''))
                factor = 0.62 if is_mono else 0.60
                w = len(t) * factor * fs

                tx = float(tsp.attrib.get('x', elem_x))
                dy_str = tsp.attrib.get('dy', None)
                if dy_str is not None:
                    cur_y += float(dy_str)
                else:
                    cur_y = float(tsp.attrib.get('y', cur_y))

                tsp_anchor = tsp.attrib.get('text-anchor', anchor)
                if tsp_anchor == 'middle':
                    xs = tx - w / 2
                    xe = tx + w / 2
                elif tsp_anchor == 'end':
                    xs = tx - w
                    xe = tx
                else:
                    xs = tx
                    xe = tx + w
                
                top_y = cur_y - fs
                bot_y = cur_y + 0.25 * fs

                pad_l = xs - bx
                pad_r = (bx + bw) - xe
                pad_t = top_y - by
                pad_b = (by + bh) - bot_y

                print(f"[{box_name:14s}] (tspan) '{t[:22]:22s}' pad L={pad_l:5.1f} R={pad_r:5.1f} T={pad_t:5.1f} B={pad_b:5.1f}")
                assert pad_l >= 15.9, f"Left pad {pad_l:.1f} < 16 for '{t}' in {box_name}"
                assert pad_r >= 15.9, f"Right pad {pad_r:.1f} < 16 for '{t}' in {box_name}"
                assert pad_t >= 15.9, f"Top pad {pad_t:.1f} < 16 for '{t}' in {box_name}"
                assert pad_b >= 15.9, f"Bottom pad {pad_b:.1f} < 16 for '{t}' in {box_name}"

    print("\nALL PADDING CHECKS PASSED!")

if __name__ == "__main__":
    audit_paddings()
