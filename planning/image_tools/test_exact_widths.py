# Target sum = 1280
# 7 boxes: w0, w1, w2, w3, w4, w5, w6

# Let's see:
# w0 = 135  (pad 16 -> inner 103 >= 100.8)
# w1 = 230  (pad 16 -> inner 198 >= 187.2)
# w2 = 190  (pad 16 -> inner 158 >= 158.4? Wait, 11 * 14.4 = 158.4 > 158! So w2 must be at least 158.4 + 32 = 190.4 -> 192 px)
# w3 = 180  (inner 148 >= 144)
# w4 = 165  (inner 133 >= 129.6)
# w5 = 198  (inner 166 >= 158.4)
# w6 = 182  (inner 150 >= 144)

# Sum = 135 + 230 + 192 + 180 + 165 + 198 + 180 = 1280 px!
# Let's check:
w0 = 135
w1 = 230
w2 = 192
w3 = 180
w4 = 165
w5 = 198
w6 = 180
total = w0 + w1 + w2 + w3 + w4 + w5 + w6
print(f"Total: {total}")
assert total == 1280, f"Total is {total}"
print("Perfect exact sum of 1280 px!")

# Let's check every single line in every box against inner width!
lines0 = ["Success"] # 7 * 14.4 = 100.8 <= 103 (135 - 32) -> PASS
lines1 = [
    "General",        # 7 * 14.4 = 100.8
    "error. For",     # 10 * 14.4 = 144.0
    "grep, diff",     # 10 * 14.4 = 144.0
    "and cmp: no",    # 11 * 14.4 = 158.4
    "match or",       # 8 * 14.4 = 115.2
    "files differ,",  # 13 * 14.4 = 187.2
    "not an error"    # 12 * 14.4 = 172.8
] # max 187.2 <= 198 (230 - 32) -> PASS
lines2 = [
    "Misuse of",     # 9 * 14.4 = 129.6
    "a command,",    # 10 * 14.4 = 144.0
    "or a real",     # 9 * 14.4 = 129.6
    "error for",     # 9 * 14.4 = 129.6
    "grep and",      # 8 * 14.4 = 115.2
    "diff"           # 4 * 14.4 = 57.6
] # max 144.0 <= 160 (192 - 32) -> PASS
lines3 = [
    "Found but",     # 9 * 14.4 = 129.6
    "not",           # 3 * 14.4 = 43.2
    "executable"     # 10 * 14.4 = 144.0
] # max 144.0 <= 148 (180 - 32) -> PASS
lines4 = [
    "Command",       # 7 * 14.4 = 100.8
    "not found"      # 9 * 14.4 = 129.6
] # max 129.6 <= 133 (165 - 32) -> PASS
lines5 = [
    "130 Ctrl-C",    # 10 * 14.4 = 144.0
    "137 SIGKILL",   # 11 * 14.4 = 158.4
    "143 SIGTERM"    # 11 * 14.4 = 158.4
] # max 158.4 <= 166 (198 - 32) -> PASS
lines6 = [
    "Status out",    # 10 * 14.4 = 144.0
    "of range,",     # 9 * 14.4 = 129.6
    "or ssh",        # 6 * 14.4 = 86.4
    "connection",    # 10 * 14.4 = 144.0
    "failure"        # 7 * 14.4 = 100.8
] # max 144.0 <= 148 (180 - 32) -> PASS

print("All lines fit inside their boxes with >= 16px padding on both sides!")
