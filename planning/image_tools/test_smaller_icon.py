from test_dia_combo import check_diamond_icon_above

for rx in [150, 160, 170]:
    for ry in [70, 75, 80, 85]:
        d = check_diamond_icon_above(rx, ry, 145, 25, 24, 24, gap=6)
        print(f"rx={rx}, ry={ry}, iw=24: d={d:.1f}px ({'PASS' if d>=16 else 'FAIL'})")
