import xml.etree.ElementTree as ET

tree = ET.parse("test_adjusted.svg")
root = tree.getroot()

def get_w(text, font_family, fs):
    rate = 0.62 if "mono" in font_family else 0.60
    return len(text) * rate * fs

# Let's inspect each text element and its surrounding rect / card / icon:
# 1. Subtitle Pill:
# <rect x="450" y="72" width="700" height="64" rx="32" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
# <text x="800" y="112" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">toy numbers chosen to show the mechanism</text>
txt = "toy numbers chosen to show the mechanism"
w = get_w(txt, "sans-serif", 24)
tx = 800 - w/2
print(f"Subtitle Pill: L={tx - 450:.1f}, R={(450+700)-(tx+w):.1f}, T={112 - 0.75*24 - 72:.1f}, B={(72+64) - (112 + 0.22*24):.1f}")

# 2. Setup Container:
# <rect x="50" y="176" width="1500" height="94" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
# <g transform="translate(75, 195)" stroke="#207448" stroke-width="4" fill="none">
# Text starts at x=155. Icon is 75..131. Distance from icon = 155 - 131 = 24px >= 16px!
# Text lines:
# line 1: "Setup: eight replicas, forty prefixes, one hot prefix with 40 percent of traffic,"
# line 2: "cache of six prefixes per replica, hit costs 0.10 s and miss 0.50 s"
l1 = "Setup: eight replicas, forty prefixes, one hot prefix with 40 percent of traffic,"
l2 = "cache of six prefixes per replica, hit costs 0.10 s and miss 0.50 s"
w1 = get_w(l1, "sans-serif", 24)
w2 = get_w(l2, "sans-serif", 24)
print(f"Setup L1: L={155 - 131:.1f} (from icon), R={(50+1500)-(155+w1):.1f}, T={215 - 0.75*24 - 176:.1f}")
print(f"Setup L2: B={(176+94) - (215+33 + 0.22*24):.1f}")

# 3. Table 1 Header:
# <rect x="70" y="326" width="685" height="106" rx="10" fill="#e8f1ea"/>
# icon: 85..141. Text at x=160. Gap = 160 - 141 = 19px >= 16px!
# tspan 1: "Table 1 policy:" fs=30, y=372
# tspan 2: "hit rate, p50 s, p99 s, max over mean load" fs=24, y=372+35=407
t1_h1 = "Table 1 policy:"
t1_h2 = "hit rate, p50 s, p99 s, max over mean load"
print(f"T1 Header: L={160 - 141:.1f}, R={(70+685)-(160+get_w(t1_h2, 'sans-serif', 24)):.1f}, T={372 - 0.75*30 - 326:.1f}, B={(326+106) - (407 + 0.22*24):.1f}")

# 4. Table 1 Rows:
# Each row: <rect x="70" y="..." width="685" height="110" .../>
# Text at x=90, y=...
# Bar rect at x=90, y=..., h=24
for name, y_box, y_text, y_bar, bars in [
    ("round_robin", 438, 478, 504, [(90, 138), (240, 163), (415, 70)]),
    ("least_loaded", 560, 600, 626, [(90, 138), (240, 85), (337, 81)]),
    ("cache_only", 682, 722, 748, [(90, 294), (396, 219)]),
    ("cache_bounded", 804, 844, 870, [(90, 285), (387, 35), (434, 149)]),
]:
    # Check text padding
    top_pad = y_text - 0.75*24 - y_box
    # Gap between text bottom and bar top:
    text_bottom = y_text + 0.22*24
    gap_text_bar = y_bar - text_bottom
    # Bar bottom pad to box:
    bar_bottom = y_bar + 24
    bottom_pad = (y_box + 110) - bar_bottom
    print(f"T1 {name}: T_pad={top_pad:.1f}, gap_text_bar={gap_text_bar:.1f}, bar_B_pad={bottom_pad:.1f}")

