from sim_layout import check_wrap

for w in [260, 280, 300, 320, 360]:
    lines = check_wrap("Client on the office network or anywhere", w, size=24)
    print(f"w={w}:", lines)
