import re

left_pairs = [
    ("Failed to start X: Unit X not found", "wrong name, path or alias; daemon-reload may fix it"),
    ("Job for X failed because the control process exited with error code", "read journalctl -xeu X"),
    ("start request repeated too quickly", "start limit hit: reset-failed, fix the cause, lengthen RestartSec"),
    ("Dependency failed for X", "a Requires dependency failed"),
    ("Unit is masked", "the unit cannot be started at all")
]

# If Left message box w = 310 (usable 310 - 32 = 278), Cause box w = 360 (usable 360 - 32 = 328)
# Arrow = 30 -> 310 + 30 + 360 = 700. Plus 20px padding in left column -> 720.

def check_wrap(text, usable_w, font_size=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    char_w = font_size * factor
    max_c = int(usable_w / char_w)
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if not curr:
            curr.append(w)
            curr_len = len(w)
        elif curr_len + 1 + len(w) <= max_c:
            curr.append(w)
            curr_len += 1 + len(w)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    print(f"Text: '{text}' -> {len(lines)} lines (max_c={max_c}):")
    for l in lines:
        w = len(l) * char_w
        print(f"   [{w:.1f}px / {usable_w}px] '{l}'")
    return lines

print("=== LEFT COLUMN CHECKS ===")
for msg, cause in left_pairs:
    print("\n--- Pair ---")
    check_wrap(msg, 278, 24, False)
    check_wrap(cause, 328, 24, False)
