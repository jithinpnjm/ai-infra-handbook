# Let's test the 2-line wrapping for f1 and f4:

char_w = 14.88 # 0.62 * 24

# f1:
l1_f1 = "[gpu] gpu01 ansible_host=10.0.10.11, "
l2_f1 = "gpu02 ansible_host=10.0.10.12"
w1_f1 = len(l1_f1.strip()) * char_w
w2_f1 = len(l2_f1.strip()) * char_w
print(f"f1 line 1 width: {w1_f1:.1f}px, line 2 width: {w2_f1:.1f}px")

# f4:
l1_f4 = "[cluster:vars] ansible_user=automation, "
l2_f4 = "ansible_python_interpreter=/usr/bin/python3"
w1_f4 = len(l1_f4.strip()) * char_w
w2_f4 = len(l2_f4.strip()) * char_w
print(f"f4 line 1 width: {w1_f4:.1f}px, line 2 width: {w2_f4:.1f}px")

# Available width inside box (x=40 to 800, text starts at x=135):
avail = 800 - 135
print(f"Available width: {avail}px")
assert w1_f1 <= avail - 16, "f1 line 1 too wide"
assert w2_f1 <= avail - 16, "f1 line 2 too wide"
assert w1_f4 <= avail - 16, "f4 line 1 too wide"
assert w2_f4 <= avail - 16, "f4 line 2 too wide"

print("All 2-line monospace widths fit with >= 16px padding!")
