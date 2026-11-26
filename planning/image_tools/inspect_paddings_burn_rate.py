import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_burn_rate.svg")
root = tree.getroot()

# Let's inspect each group and text element
# Boxes and their corresponding texts:
boxes = {
    "formula-1": {"rect": (40, 155, 486, 155), "icon": (65, 175, 50, 45)},
    "formula-2": {"rect": (556, 155, 486, 155), "icon": (581, 185, 46, 30)},
    "formula-3": {"rect": (1072, 155, 486, 155), "icon": (1097, 175, 50, 50)},
    "meaning-card": {"rect": (40, 330, 1520, 110), "icon": (65, 355, 45, 50)},
    "alert-1": {"rect": (40, 465, 486, 270), "icon": (65, 485, 60, 40)},
    "alert-2": {"rect": (556, 465, 486, 270), "icon": (581, 485, 55, 40)},
    "alert-3": {"rect": (1072, 465, 486, 270), "icon": (1097, 485, 40, 45)},
    "check-1": {"rect": (40, 760, 365, 190), "icon": (60, 780, 40, 40)},
    "check-2": {"rect": (425, 760, 365, 190), "icon": (445, 780, 40, 40)},
    "check-3": {"rect": (810, 760, 365, 190), "icon": (830, 780, 40, 40)},
    "check-4": {"rect": (1195, 760, 365, 190), "icon": (1215, 780, 40, 40)},
    "note-bar": {"rect": (40, 975, 1520, 140), "icon": (65, 1005, 45, 50)}
}

for gid, bdata in boxes.items():
    g = root.find(f".//*[@id='{gid}']")
    rx, ry, rw, rh = bdata["rect"]
    r_right = rx + rw
    r_bottom = ry + rh
    ix, iy, iw, ih = bdata["icon"]
    i_right = ix + iw
    i_bottom = iy + ih

    text_elem = g.find('{http://www.w3.org/2000/svg}text')
    default_fs = float(text_elem.attrib.get('font-size', 24))
    font_family = text_elem.attrib.get('font-family', '')
    is_mono = 'mono' in font_family

    print(f"\nGroup [{gid}]: Box ({rx}, {ry}, w={rw}, h={rh}), Icon ({ix}, {iy}, w={iw}, h={ih})")
    tspans = text_elem.findall('{http://www.w3.org/2000/svg}tspan')
    if not tspans:
        tspans = [text_elem]

    for tsp in tspans:
        tx = float(tsp.attrib.get('x', rx))
        ty = float(tsp.attrib.get('y', ry))
        fs = float(tsp.attrib.get('font-size', default_fs))
        t_text = tsp.text.strip() if tsp.text else ""
        char_w = fs * (0.62 if is_mono else 0.6)
        text_w = len(t_text) * char_w
        text_right = tx + text_w

        # Paddings
        left_pad = tx - rx
        right_pad = r_right - text_right
        top_pad = ty - fs - ry
        bottom_pad = r_bottom - ty

        # Icon overlap check
        # Icon box: [ix, ix+iw] x [iy, iy+ih]
        # Text line box: [tx, text_right] x [ty - fs, ty]
        h_overlap = max(0, min(text_right, i_right) - max(tx, ix))
        v_overlap = max(0, min(ty, i_bottom) - max(ty - fs, iy))
        has_icon_overlap = (h_overlap > 0 and v_overlap > 0)

        ok = (left_pad >= 16) and (right_pad >= 16) and (not has_icon_overlap)
        status = "OK" if ok else "FAIL"
        print(f"  [{status}] '{t_text[:30]}...' fs={fs} tx={tx} tr={text_right:.1f} (r_right={r_right}) L_pad={left_pad:.1f} R_pad={right_pad:.1f} icon_overlap={has_icon_overlap}")
        assert ok, f"Padding or overlap violation in {gid} on '{t_text}'!"

print("\nALL BOX PADDINGS >= 16PX AND ZERO ICON OVERLAPS!")
