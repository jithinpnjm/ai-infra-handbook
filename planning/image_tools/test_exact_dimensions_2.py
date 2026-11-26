# Let's change proprietary GPU-to-GPU links to 3 lines:
# 'proprietary', 'GPU-to-GPU', 'links'
# Reconstructed: ' '.join(['proprietary', 'GPU-to-GPU', 'links']) == 'proprietary GPU-to-GPU links'
lines = ['proprietary', 'GPU-to-GPU', 'links']
full = 'proprietary GPU-to-GPU links'
assert ' '.join(lines) == full
for l in lines:
    px = len(l) * 0.6 * 24
    print(f"'{l}': {px:.1f}px / 223px ({'OK' if px <= 223 else 'OVERFLOW'})")
