# Diamond center: (890, 850), width: 420, height: 200
# Left tip: 680, Right tip: 1100, Top tip: 750, Bottom tip: 950
W = 420
H = 200
cx = 890
cy = 850

# Text inside diamond:
# Label: 'validation fails: the play stops before the 10% batch'
# Wrap:
# Line 1: 'validation fails:'
# Line 2: 'the play stops before'
# Line 3: 'the 10% batch'
lines = [
    ("validation fails:", -32, 24),
    ("the play stops before", 0, 24),
    ("the 10% batch", 32, 24)
]

print("Checking diamond text paddings:")
for text, dy, fs in lines:
    y_pos = cy + dy
    dist_from_center = abs(dy)
    # At this y, diamond width is:
    available_w = W * (1 - dist_from_center / (H / 2))
    text_w = len(text) * 0.6 * fs
    pad = (available_w - text_w) / 2
    print(f"  Line '{text}': available_w = {available_w:.1f}px, text_w = {text_w:.1f}px, pad = {pad:.1f}px")
    assert pad >= 16, f"Padding {pad} < 16 px!"

print("Diamond text padding PASSED!")
