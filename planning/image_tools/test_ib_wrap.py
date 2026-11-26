from test_geometry import wrap_text, text_width, labels

ib_text = labels["infiniband"]
print("Width 430 (icon above text):")
lines1 = wrap_text(ib_text, 430, 24)
for l in lines1:
    print(f"  [{text_width(l, 24):.1f}px] {l}")
print("Total lines:", len(lines1))

print("\nWidth 380 (icon beside text):")
lines2 = wrap_text(ib_text, 380, 24)
for l in lines2:
    print(f"  [{text_width(l, 24):.1f}px] {l}")
print("Total lines:", len(lines2))
