# Layout calculator script
y_title = 58
y1 = 100
h_c1 = 90
gap_c1_c2 = 40
y_c2 = y1 + h_c1 + gap_c1_c2 # 230
h_c2 = 90
gap_c2_c3 = 40
y_c3 = y_c2 + h_c2 + gap_c2_c3 # 360
h_c3 = 120
y_left_end = y_c3 + h_c3 # 480

y_r = 100
h_r = 380
y_right_end = y_r + h_r # 480

gap_sec1_sec2 = 40
y_ex = y_left_end + gap_sec1_sec2 # 520
h_ex = 220
y_ex_end = y_ex + h_ex # 740

gap_sec2_sec3 = 40
y_pref = y_ex_end + gap_sec2_sec3 # 780
h_pref = 130
y_pref_end = y_pref + h_pref # 910

gap_sec3_sec4 = 40
y_cost = y_pref_end + gap_sec3_sec4 # 950
h_cost = 100
y_cost_end = y_cost + h_cost # 1050

gap_sec4_sec5 = 40
y_bot = y_cost_end + gap_sec4_sec5 # 1090
h_bot = 70
y_bot_end = y_bot + h_bot # 1160

margin_bottom = 1200 - y_bot_end # 40

print(f"Section 1 Left:  Card1={y1}..{y1+h_c1}, Card2={y_c2}..{y_c2+h_c2}, Card3={y_c3}..{y_c3+h_c3} (ends {y_left_end})")
print(f"Section 1 Right: RightBox={y_r}..{y_r+h_r} (ends {y_right_end})")
print(f"Section 2 Ex:    {y_ex}..{y_ex_end} (h={h_ex})")
print(f"Section 3 Pref:  {y_pref}..{y_pref_end} (h={h_pref})")
print(f"Section 4 Cost:  {y_cost}..{y_cost_end} (h={h_cost})")
print(f"Section 5 Bot:   {y_bot}..{y_bot_end} (h={h_bot})")
print(f"Bottom margin:   {margin_bottom}px")
