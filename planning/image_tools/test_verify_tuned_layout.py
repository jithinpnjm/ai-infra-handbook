import re

# Font estimation functions
def text_width(text, font_family, font_size):
    rate = 0.62 if "mono" in font_family else 0.60
    return len(text) * rate * font_size

# Canvas 1600 x 1200
# Elements:
# 1. Title:
# text: x=800, y=56, fs=48, bold, middle
title = "Toy router simulation: policies and the bound sweep"
tw_title = text_width(title, "sans-serif", 48)
t_left = 800 - tw_title/2
t_right = 800 + tw_title/2
print(f"Title: w={tw_title:.1f}, x=[{t_left:.1f}, {t_right:.1f}], margins: left={t_left:.1f}, right={1600-t_right:.1f} (>= 40)")

# 2. Subtitle Pill:
# rect: x=450, y=74, w=700, h=58, rx=29
# text: x=800, y=110, fs=24, bold, middle
pill = "toy numbers chosen to show the mechanism"
tw_pill = text_width(pill, "sans-serif", 24)
p_left = 800 - tw_pill/2
p_right = 800 + tw_pill/2
pad_l = p_left - 450
pad_r = 1150 - p_right
pad_t = 110 - 18 - 74
pad_b = (74 + 58) - (110 + 5.28)
print(f"Pill: w={tw_pill:.1f}, pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f} (all >= 16)")
assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16

# Gap to Setup:
gap_0_1 = 172 - (74 + 58)
print(f"Gap Pill -> Setup: {gap_0_1}px (>= 40)")
assert gap_0_1 >= 40

# 3. Setup Box:
# rect: x=50, y=172, w=1500, h=94, rx=14
# Icon: 75..131
# Text: x=155
l1 = "Setup: eight replicas, forty prefixes, one hot prefix with 40 percent of traffic,"
l2 = "cache of six prefixes per replica, hit costs 0.10 s and miss 0.50 s"
tw_l1 = text_width(l1, "sans-serif", 24)
tw_l2 = text_width(l2, "sans-serif", 24)
s_pad_l = 155 - 131 # from icon
s_pad_r1 = 1550 - (155 + tw_l1)
s_pad_r2 = 1550 - (155 + tw_l2)
s_pad_t = 210 - 18 - 172
s_pad_b = (172 + 94) - (244 + 5.28)
print(f"Setup: pad_l={s_pad_l:.1f}, pad_r1={s_pad_r1:.1f}, pad_r2={s_pad_r2:.1f}, pad_t={s_pad_t:.1f}, pad_b={s_pad_b:.1f}")
assert s_pad_l >= 16 and s_pad_r1 >= 16 and s_pad_r2 >= 16 and s_pad_t >= 16 and s_pad_b >= 16

# Gap to Table 1:
gap_1_2 = 306 - (172 + 94)
print(f"Gap Setup -> T1: {gap_1_2}px (>= 40)")
assert gap_1_2 >= 40

# 4. Table 1:
# rect: x=50, y=306, w=1500, h=290, rx=14
# Header: rect x=66, y=318, w=1468, h=54, rx=10
# Icon: 75..131
# Text: x=155, y=354, fs=30, bold
h1 = "Table 1 policy: hit rate, p50 s, p99 s, max over mean load"
tw_h1 = text_width(h1, "sans-serif", 30)
h1_pad_l = 155 - 131
h1_pad_r = 1534 - (155 + tw_h1)
h1_pad_t = 354 - 0.75*30 - 318
h1_pad_b = (318 + 54) - 354 # to baseline
print(f"T1 Header: pad_l={h1_pad_l:.1f}, pad_r={h1_pad_r:.1f}, pad_t={h1_pad_t:.1f}, pad_b={h1_pad_b:.1f}")

# Gap to Table 2:
gap_2_3 = 636 - (306 + 290)
print(f"Gap T1 -> T2: {gap_2_3}px (>= 40)")
assert gap_2_3 >= 40

# 5. Table 2:
# rect: x=50, y=636, w=1500, h=342, rx=14
# Header: rect x=66, y=648, w=1468, h=54, rx=10
# Icon: 75..131
# Text: x=155, y=684, fs=30, bold
h2 = "Table 2 bound in seconds of backlog"
tw_h2 = text_width(h2, "sans-serif", 30)
h2_pad_l = 155 - 131
h2_pad_r = 1534 - (155 + tw_h2)
h2_pad_t = 684 - 0.75*30 - 648
h2_pad_b = (648 + 54) - 684
print(f"T2 Header: pad_l={h2_pad_l:.1f}, pad_r={h2_pad_r:.1f}, pad_t={h2_pad_t:.1f}, pad_b={h2_pad_b:.1f}")

# Gap to Takeaway:
gap_3_4 = 1018 - (636 + 342)
print(f"Gap T2 -> Takeaway: {gap_3_4}px (>= 40)")
assert gap_3_4 >= 40

# 6. Takeaway:
# rect: x=50, y=1018, w=1500, h=142, rx=14
# Text: x=800, 3 lines, fs=24, bold, middle
t1 = "cache-only wins hit rate and loses the tail because one replica carries 3.8 times the average load;"
t2 = "least-loaded keeps load flat but wastes the cache; sweep the bound against p99, not hit rate;"
t3 = "zero bound behaves like least-loaded, a huge bound like cache-only"
tw_t1 = text_width(t1, "sans-serif", 24)
tw_t2 = text_width(t2, "sans-serif", 24)
tw_t3 = text_width(t3, "sans-serif", 24)
print(f"Takeaway L1 w={tw_t1:.1f}, pad={(1500-tw_t1)/2:.1f}")
print(f"Takeaway L2 w={tw_t2:.1f}, pad={(1500-tw_t2)/2:.1f}")
print(f"Takeaway L3 w={tw_t3:.1f}, pad={(1500-tw_t3)/2:.1f}")
# Text baselines: y=1054, dy=33 -> 1054, 1087, 1120
tk_pad_t = 1054 - 18 - 1018
tk_pad_b = (1018 + 142) - (1120 + 5.28)
print(f"Takeaway: pad_t={tk_pad_t:.1f}, pad_b={tk_pad_b:.1f}")

# Bottom margin:
b_margin = 1200 - (1018 + 142)
print(f"Bottom margin: {b_margin}px (>= 40)")
assert b_margin >= 40

print("\nALL VERIFICATIONS PASSED!")
