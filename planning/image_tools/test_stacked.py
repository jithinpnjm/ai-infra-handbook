print("=== Testing Vertically Stacked Ladders ===")
w = 1520 # full width
# In full width 1520:
# Card width = 1480
# Circle: x=44
# Icon: x=90..146
# Text start x: 170
# Available text width = 1480 - 170 - 16 = 1294 px!

lines_step2 = [
    "./ansible.cfg in the current directory ",
    "(honoured only if it is not world-writable: a folder any user can change cannot be trusted)"
]
for line in lines_step2:
    w_mono = len(line) * 24 * 0.62
    w_sans = len(line) * 24 * 0.6
    print(f"  Line: '{line}' | w_mono={w_mono:.1f}, w_sans={w_sans:.1f} (avail=1294)")
