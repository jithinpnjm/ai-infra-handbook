from generate_svg import wrap_text, col1_items, col2_items, col3_items

print("=== Wrap at 27 chars ===")
for col_name, items in [("Col 1", col1_items), ("Col 2", col2_items), ("Col 3", col3_items)]:
    print(f"\n{col_name}:")
    for i, it in enumerate(items):
        lines = wrap_text(it, 27)
        max_l = max(len(l) for l in lines)
        print(f"  Item {i+1}: {len(lines)} lines, max={max_l} chars ({max_l * 14.4:.1f}px)")
        for l in lines:
            print(f"     '{l}'")
