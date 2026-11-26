from generate_svg import wrap_text, col2_items

for mc in [30, 31, 32]:
    print(f"--- max_chars = {mc} ---")
    lines = wrap_text(col2_items[0], mc)
    print(f"Col 2 Item 1: {len(lines)} lines")
    for l in lines:
        print(f"    '{l}' ({len(l)} chars)")
