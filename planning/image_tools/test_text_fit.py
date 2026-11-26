import re

def check_line(text, font_size, is_mono, box_width):
    char_w = 0.62 * font_size if is_mono else 0.60 * font_size
    line_w = len(text) * char_w
    pad = (box_width - line_w) / 2
    return line_w, pad

items = [
    # where to set
    ("/etc/security/limits.d/*.conf for logins", 24, False, 650),
    ("LimitMEMLOCK=infinity for systemd units", 24, False, 650),
    ("--ulimit memlock=-1:-1 for Docker", 24, False, 650),
    ("Slurm PropagateResourceLimits", 24, False, 650),
    ("runtime configuration for Kubernetes", 24, False, 650),
]

for t, fs, mono, bw in items:
    lw, pad = check_line(t, fs, mono, bw)
    print(f"'{t}': width={lw:.1f}, pad={pad:.1f} in box={bw} ({'OK' if pad >= 16 else 'FAIL'})")

