def wrap(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

# Minimum width needed for each box at fs=24 (char_w = 14.4 px, pad=16 px -> w = text_w + 32):
# Box 0: 'Success' -> 7 chars * 14.4 = 100.8 px -> min w = 132.8 px. Let w0 = 135 px.
# Box 1: 'General error. For grep, diff and cmp: no match or files differ, not an error'
# Box 2: 'Misuse of a command, or a real error for grep and diff'
# Box 3: 'Found but not executable' -> 'executable' is 10 chars = 144 px -> min w = 176 px.
# Box 4: 'Command not found' -> 'Command' is 7 chars = 100.8 px, 'not found' is 9 chars = 129.6 px -> min w = 161.6 px.
# Box 5: 128+N markers:
#    '130 Ctrl-C' (10 chars = 144 px)
#    '137 SIGKILL' (11 chars = 158.4 px)
#    '143 SIGTERM' (11 chars = 158.4 px)
#    min w = 158.4 + 32 = 190.4 px -> say w5 = 200 px.
# Box 6: 'Status out of range, or ssh connection failure'
#    'connection' is 10 chars = 144 px -> min w = 176 px.

# Can we allocate:
# w0 = 135
# w3 = 180
# w4 = 165
# w5 = 200
# w6 = 180
# Subtotal = 135 + 180 + 165 + 200 + 180 = 860 px.
# Remaining for w1 and w2 = 1280 - 860 = 420 px.
# Can w1 and w2 share 420 px?
# w1 = 230 px -> inner = 198 px -> max_chars = 198 / 14.4 = 13.75 -> 13 chars!
# w2 = 190 px -> inner = 158 px -> max_chars = 158 / 14.4 = 10.97 -> 10 chars!

print("Testing w1=230:")
lines1 = wrap("General error. For grep, diff and cmp: no match or files differ, not an error", 13)
for l in lines1:
    print(f"  '{l}' ({len(l)} chars, {len(l)*14.4:.1f}px <= 198px)")

print("\nTesting w2=190:")
lines2 = wrap("Misuse of a command, or a real error for grep and diff", 10)
for l in lines2:
    print(f"  '{l}' ({len(l)} chars, {len(l)*14.4:.1f}px <= 158px)")

