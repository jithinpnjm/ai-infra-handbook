from test_geometry import wrap_text, text_width

text = "Rail-optimised: one NIC per GPU, often its own subnet, VLAN or VRF; 8 x 400G back end; a single x4 link at 100G instead of 400G slows the whole job because collectives move at the speed of the slowest participant"

# Max width 1380 px
lines = wrap_text(text, 1380, 24)
print(f"Max 1380 px ({len(lines)} lines):")
for l in lines:
    w = text_width(l, 24)
    print(f"   [{w:6.1f}px] '{l}'")

lines4 = wrap_text(text, 1100, 24)
print(f"\nMax 1100 px ({len(lines4)} lines):")
for l in lines4:
    w = text_width(l, 24)
    print(f"   [{w:6.1f}px] '{l}'")
