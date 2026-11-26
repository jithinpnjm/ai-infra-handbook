#!/usr/bin/env python3
import xml.etree.ElementTree as ET

def check_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Boxes:
    boxes = {
        "row-1": (40, 150, 1520, 145),
        "row-2": (40, 335, 1520, 145),
        "row-3": (40, 520, 1520, 145),
        "policy-box": (40, 705, 740, 395),
        "context-box": (820, 705, 740, 395),
    }

    # Verify spacing between boxes:
    # Row 1 and Row 2: 335 - (150 + 145) = 335 - 295 = 40 >= 40
    # Row 2 and Row 3: 520 - (335 + 145) = 520 - 480 = 40 >= 40
    # Row 3 and Bottom boxes: 705 - (520 + 145) = 705 - 665 = 40 >= 40
    # Policy and Context: 820 - (40 + 740) = 820 - 780 = 40 >= 40
    # Left margin: 40 >= 40
    # Right margin: 1600 - (820 + 740) = 40 >= 40
    # Bottom margin: 1140 - (705 + 395) = 1140 - 1100 = 40 >= 40

    # Icons per box:
    icons = {
        "row-1": (65, 188, 62, 34), # from 65 to 127
        "row-2": (65, 352, 61, 59), # from 65 to 126
        "row-3": (65, 542, 57, 57), # from 65 to 122
        "policy-box": (64, 725, 52, 63), # from 64 to 116, y=725..788
        "context-box": (846, 738, 48, 48), # from 846 to 894, y=738..786
    }

    all_passed = True

    for gid, (bx, by, bw, bh) in boxes.items():
        g = root.find(f".//*[@id='{gid}']")
        assert g is not None, f"Group {gid} not found"
        ix, iy, iw, ih = icons[gid]

        for text in g.findall('{http://www.w3.org/2000/svg}text'):
            base_fs = float(text.attrib.get('font-size', 24))
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            if not tspans:
                tspans = [text]
            for tsp in tspans:
                t = (tsp.text or "").strip()
                if not t: continue
                fs = float(tsp.attrib.get('font-size', base_fs))
                w = len(t) * 0.60 * fs
                tx = float(tsp.attrib.get('x', text.attrib.get('x', 0)))
                ty = float(tsp.attrib.get('y', text.attrib.get('y', 0)))

                # Text bounds
                top_y = ty - fs
                bot_y = ty + 0.25 * fs
                left_x = tx
                right_x = tx + w

                pad_l = left_x - bx
                pad_r = (bx + bw) - right_x
                pad_t = top_y - by
                pad_b = (by + bh) - bot_y

                # Icon collision check:
                # Does text bounding box [left_x, right_x] x [top_y, bot_y] intersect icon [ix, ix+iw] x [iy, iy+ih]?
                # They collide if not (right_x < ix or left_x > ix + iw or bot_y < iy or top_y > iy + ih)
                horiz_overlap = not (right_x < ix or left_x > ix + iw)
                vert_overlap = not (bot_y < iy or top_y > iy + ih)
                icon_collision = horiz_overlap and vert_overlap

                # If beside icon (vert overlap), check gap to icon
                icon_gap = None
                if vert_overlap:
                    if left_x >= ix + iw:
                        icon_gap = left_x - (ix + iw)
                    elif right_x <= ix:
                        icon_gap = ix - right_x
                # If below icon (horiz overlap), check gap to icon
                elif horiz_overlap:
                    if top_y >= iy + ih:
                        icon_gap = top_y - (iy + ih)
                    elif bot_y <= iy:
                        icon_gap = iy - bot_y

                print(f"[{gid}] '{t[:28]}...' (fs={fs}): pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}, icon_gap={icon_gap}")

                if pad_l < 16:
                    print(f"  FAIL: pad_l {pad_l:.1f} < 16 for '{t}'")
                    all_passed = False
                if pad_r < 16:
                    print(f"  FAIL: pad_r {pad_r:.1f} < 16 for '{t}'")
                    all_passed = False
                if pad_t < 16:
                    print(f"  FAIL: pad_t {pad_t:.1f} < 16 for '{t}'")
                    all_passed = False
                if pad_b < 16:
                    print(f"  FAIL: pad_b {pad_b:.1f} < 16 for '{t}'")
                    all_passed = False
                if icon_collision:
                    print(f"  FAIL: COLLISION WITH ICON for '{t}'")
                    all_passed = False
                if icon_gap is not None and icon_gap < 16:
                    print(f"  FAIL: icon_gap {icon_gap:.1f} < 16 for '{t}'")
                    all_passed = False

    # Check title paddings
    title_elem = root.find('{http://www.w3.org/2000/svg}text')
    assert title_elem is not None
    base_fs = float(title_elem.attrib.get('font-size', 48))
    for tsp in title_elem.findall('{http://www.w3.org/2000/svg}tspan'):
        t = (tsp.text or "").strip()
        fs = float(tsp.attrib.get('font-size', base_fs))
        w = len(t) * 0.60 * fs
        tx = float(tsp.attrib.get('x', 800))
        ty = float(tsp.attrib.get('y', 0))
        # anchor is middle
        left_x = tx - w / 2
        right_x = tx + w / 2
        top_y = ty - fs
        bot_y = ty + 0.25 * fs
        print(f"[Title] '{t[:28]}...': left={left_x:.1f}, right={right_x:.1f}, top={top_y:.1f}, bot={bot_y:.1f}")
        assert left_x >= 16, f"Title left {left_x} < 16"
        assert (1600 - right_x) >= 16, f"Title right {1600 - right_x} < 16"
        assert top_y >= 16, f"Title top {top_y} < 16"

    if all_passed:
        print("\n>>> ALL PADDINGS AND CLEARANCES PASSED! <<<")
    else:
        print("\n>>> SOME CHECKS FAILED! <<<")
        exit(1)

if __name__ == '__main__':
    check_paddings("candidate_failover.svg")
