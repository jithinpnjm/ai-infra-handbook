from test_all_rows_detail import rows_data, sidenote_lines

# Row geometry
# Full width rows: x=40, y=..., w=1520
# Text starts at x=116.
# Icon is at x=55, y_center, w=44, h=44. (from x=55 to 99). Gap between icon and text is 116 - 99 = 17px (>= 16px).
# Text right bound must not exceed 1560 - 16 = 1544.
# So max text width in full rows = 1544 - 116 = 1428px.

# Row 3: x=40, w=880.
# Text starts at x=116. Max text width = (40 + 880 - 16) - 116 = 904 - 116 = 788px.

# Side note: x=940, w=620.
# Text starts at x=965. Max text width = (940 + 620 - 16) - 965 = 1544 - 965 = 579px.

print("Checking full width rows:")
for row_num, title, rule_lines, is_orange in rows_data:
    if row_num == 3:
        continue
    # Title at font 30
    tw = len(title) * 0.60 * 30
    assert tw <= 1428, f"Row {row_num} title overflow: {tw} > 1428"
    print(f"Row {row_num:2d} Title ({len(title)} chars): width={tw:.1f}px (avail: 1428px)")
    for l in rule_lines:
        rw = len(l) * 0.60 * 24
        assert rw <= 1428, f"Row {row_num} rule line overflow: {rw} > 1428 ({l})"
        print(f"       Rule  ({len(l)} chars): width={rw:.1f}px (avail: 1428px)")

print("\nChecking Row 3 (w=880):")
row3_title = rows_data[2][1]
tw = len(row3_title) * 0.60 * 30
assert tw <= 788, f"Row 3 title overflow: {tw} > 788"
print(f"Row 3 Title ({len(row3_title)} chars): width={tw:.1f}px (avail: 788px)")
for l in rows_data[2][2]:
    rw = len(l) * 0.60 * 24
    assert rw <= 788, f"Row 3 rule line overflow: {rw} > 788 ({l})"
    print(f"      Rule  ({len(l)} chars): width={rw:.1f}px (avail: 788px)")

print("\nChecking Side note (w=620):")
for l in sidenote_lines:
    sw = len(l) * 0.60 * 24
    assert sw <= 579, f"Side note line overflow: {sw} > 579 ({l})"
    print(f"      Side note ({len(l)} chars): width={sw:.1f}px (avail: 579px)")

print("\nALL LINES FIT COMFORTABLY WITH AT LEAST 16PX PADDING!")
