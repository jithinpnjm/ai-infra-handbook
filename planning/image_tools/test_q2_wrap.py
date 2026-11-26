# If pill is 2 lines:
# pill width = 270 px
# Remaining width for question text: 860 - 270 - 25 = 565 px!
# 565 / 14.4 = 39.2 chars per line!
# Let's wrap question text to 38 chars:
def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    current = []
    current_len = 0
    for w in words:
        if current_len + len(w) + (1 if current else 0) <= max_chars:
            current.append(w)
            current_len += len(w) + (1 if len(current) > 1 else 0)
        else:
            lines.append(" ".join(current))
            current = [w]
            current_len = len(w)
    if current:
        lines.append(" ".join(current))
    return lines

q = "Is the CPU the limiter? Single-thread Python launch overhead, torch ops launching tiny kernels"
lines = wrap_text(q, 38)
print("Lines of q (max_chars=38):", len(lines))
for l in lines:
    print(f"  [{len(l)} ch, {len(l)*14.4:.1f}px] '{l}'")
