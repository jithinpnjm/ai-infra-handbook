from test_inline_flow import wrap_text, items

row4 = items[3]
print("Row 4 text length:", len(row4))
print("At 98 chars:")
for l in wrap_text(row4, 98):
    print(f"[{len(l)}] {l}")

print("\nAt 100 chars:")
for l in wrap_text(row4, 100):
    print(f"[{len(l)}] {l}")

print("\nAt 102 chars:")
for l in wrap_text(row4, 102):
    print(f"[{len(l)}] {l}")
