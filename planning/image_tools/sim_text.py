def check_line(text, font_size, max_width, pad=16, is_mono=False):
    factor = 0.62 if is_mono else 0.6
    w = len(text) * factor * font_size
    rem_pad = (max_width - w) / 2
    ok = rem_pad >= pad
    return ok, w, rem_pad

# Test Title
title_w = 1600
ok, w, p = check_line("Green status codes, broken streams:", 48, title_w)
print(f"Title L1: w={w:.1f}, pad={p:.1f}, ok={ok}")
ok, w, p = check_line("redefine the good event", 48, title_w)
print(f"Title L2: w={w:.1f}, pad={p:.1f}, ok={ok}")

# Test Timeline Header: in 1520px box
ok, w, p = check_line("Timeline of one streamed request", 30, 1520)
print(f"Timeline header: w={w:.1f}, pad={p:.1f}, ok={ok}")
