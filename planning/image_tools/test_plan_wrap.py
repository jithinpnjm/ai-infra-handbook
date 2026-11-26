import textwrap

s = "a saved plan file holds the full configuration and may hold sensitive values: treat it as sensitive"

for max_c in range(25, 45):
    lines = textwrap.wrap(s, width=max_c, break_long_words=False)
    max_len = max(len(l) for l in lines)
    w_px = max_len * 24 * 0.6
    if len(lines) <= 3 and w_px <= 560:
        print(f"max_c={max_c}: {len(lines)} lines, max_len={max_len}, w_px={w_px:.1f}")
        for l in lines:
            print(f"    '{l}' ({len(l)} chars, {len(l)*14.4:.1f}px)")
        break
