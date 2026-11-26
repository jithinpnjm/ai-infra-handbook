def check_paddings(name, bx, by, bw, bh, lines, x, y0, dy, fs=24, anchor='start'):
    pad_l = 999
    pad_r = 999
    top_g = y0 - fs * 0.8
    pad_t = top_g - by
    
    for i, line in enumerate(lines):
        w = len(line) * fs * 0.6
        if anchor == 'middle':
            x1 = x - w/2
            x2 = x + w/2
        else:
            x1 = x
            x2 = x + w
        pad_l = min(pad_l, x1 - bx)
        pad_r = min(pad_r, (bx + bw) - x2)
        bottom_g = y0 + i * dy + fs * 0.2
        
    pad_b = (by + bh) - bottom_g
    print(f"[{name:12s}] L={pad_l:5.1f}, R={pad_r:5.1f}, T={pad_t:5.1f}, B={pad_b:5.1f} (h={bh})")
    assert pad_l >= 16.0, f"pad_l failed: {pad_l}"
    assert pad_r >= 16.0, f"pad_r failed: {pad_r}"
    assert pad_t >= 16.0, f"pad_t failed: {pad_t}"
    assert pad_b >= 16.0, f"pad_b failed: {pad_b}"

# Test Scenario:
check_paddings("Scenario", 40, 92, 740, 110,
               ["every health check green, average latency",
                "fine, one replica buried under long",
                "generations while the others sit idle"],
               x=114, y0=128, dy=26, fs=24)

def check_diff_box(name, bx, by, bw, bh, title_lines, title_x, title_y0, title_dy, conseq_lines, conseq_x, conseq_y0, conseq_dy):
    # Check title:
    t_top = title_y0 - 30 * 0.8
    pad_t = t_top - by
    pad_l = title_x - bx
    pad_r = 999
    for i, line in enumerate(title_lines):
        w = len(line) * 30 * 0.6
        pad_r = min(pad_r, (bx + bw) - (title_x + w))
        t_bot = title_y0 + i * title_dy + 30 * 0.2
        
    assert pad_t >= 16.0, f"Title pad_t failed: {pad_t}"
    assert pad_l >= 16.0, f"Title pad_l failed: {pad_l}"
    assert pad_r >= 16.0, f"Title pad_r failed: {pad_r}"
    
    # Check conseq:
    c_top = conseq_y0 - 24 * 0.8
    gap = c_top - t_bot
    assert gap >= 4.0, f"Gap between title and conseq too small: {gap}"
    
    c_pad_l = conseq_x - bx
    c_pad_r = 999
    for i, line in enumerate(conseq_lines):
        w = len(line) * 24 * 0.6
        c_pad_r = min(c_pad_r, (bx + bw) - (conseq_x + w))
        c_bot = conseq_y0 + i * conseq_dy + 24 * 0.2
        
    pad_b = (by + bh) - c_bot
    assert c_pad_l >= 16.0, f"Conseq pad_l failed: {c_pad_l}"
    assert c_pad_r >= 16.0, f"Conseq pad_r failed: {c_pad_r}"
    assert pad_b >= 16.0, f"Conseq pad_b failed: {pad_b}"
    
    min_l = min(pad_l, c_pad_l)
    min_r = min(pad_r, c_pad_r)
    print(f"[{name:12s}] L={min_l:5.1f}, R={min_r:5.1f}, T={pad_t:5.1f}, B={pad_b:5.1f}, Gap={gap:4.1f} (h={bh})")

