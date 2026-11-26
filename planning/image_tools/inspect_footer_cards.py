import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_throttling.svg")
root = tree.getroot()

# Let's inspect footer cards text:
for card_id in ["footer-card-1", "footer-card-2", "footer-card-3"]:
    card = root.find(f".//*[@id='{card_id}']")
    rect = card.find("{http://www.w3.org/2000/svg}rect")
    rx, ry, rw, rh = float(rect.get('x')), float(rect.get('y')), float(rect.get('width')), float(rect.get('height'))
    text = card.find("{http://www.w3.org/2000/svg}text")
    fs = float(text.get('font-size', '24'))
    print(f"--- {card_id} (x={rx}, y={ry}, w={rw}, h={rh}) ---")
    for tsp in text.iter('{http://www.w3.org/2000/svg}tspan'):
        tx = float(tsp.get('x', rx))
        ty = float(tsp.get('y', ry))
        ttext = tsp.text or ""
        font_type = 'mono' if tsp.get('font-family') == 'monospace' or text.get('font-family') == 'monospace' else 'sans'
        w_factor = 0.62 if font_type == 'mono' else 0.6
        w = len(ttext) * w_factor * fs
        pad_l = tx - rx
        pad_r = (rx + rw) - (tx + w)
        print(f"  tspan y={ty:5.1f}, x={tx:5.1f}, w={w:5.1f}, pad_l={pad_l:5.1f}, pad_r={pad_r:5.1f} | '{ttext}'")
