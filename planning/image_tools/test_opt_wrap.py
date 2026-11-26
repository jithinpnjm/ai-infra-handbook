import textwrap

def wrap_text(text, max_chars):
    return textwrap.wrap(text, width=max_chars, break_long_words=False)

s = "generated credentials end up in state; convenient because Terraform can read the credential back next run, and the same convenience makes the state a target"

for max_c in range(25, 45):
    lines = wrap_text(s, max_c)
    max_len = max(len(l) for l in lines)
    w_px = max_len * 24 * 0.6
    print(f"max_c={max_c}: {len(lines)} lines, max_len={max_len}, w_px={w_px:.1f}")
    if len(lines) <= 5 and w_px <= 660:
        print("  Lines:")
        for l in lines:
            print(f"    '{l}' ({len(l)} chars, {len(l)*14.4:.1f}px)")
        break
