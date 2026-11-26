import xml.etree.ElementTree as ET

# Let's write an exact padding-optimizer script that checks and prints exact padding for all lines!
def check_pad(box_name, bx, by, bw, bh, text, fs, x, y, is_mono, anchor='start'):
    char_w = 0.62 * fs if is_mono else 0.6 * fs
    w = len(text) * char_w
    if anchor == 'middle':
        pad_l = (x - w/2) - bx
        pad_r = (bx + bw) - (x + w/2)
    else:
        pad_l = x - bx
        pad_r = (bx + bw) - (x + w)
    pad_t = y - 0.75 * fs - by
    pad_b = (by + bh) - (y + 0.25 * fs)
    ok = pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16
    print(f"[{'OK' if ok else 'FAIL'}] {box_name}: '{text[:30]}...' -> l={pad_l:.1f}, r={pad_r:.1f}, t={pad_t:.1f}, b={pad_b:.1f}")
    return ok

# Test pre-step with box (40, 64, 1520, 80):
ok1 = check_pad("pre-step L1", 40, 64, 1520, 80, "python3 code/part02/packet_capture_bpf_lab.py checks the byte-offset filters, ", 24, 128, 98, True)
ok2 = check_pad("pre-step L2", 40, 64, 1520, 80, "the 8.13 Mpps rate at 100 Gb/s, ring storage with -s 96, and the two-endpoint comparison", 24, 128, 126, True)
