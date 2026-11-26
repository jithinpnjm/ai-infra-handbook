import math

def dist_to_diamond(px, py, cx, cy, rx, ry):
    dx = abs(px - cx)
    dy = abs(py - cy)
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    val = dx/rx + dy/ry
    return (1.0 - val) / scale

# Right diamond 1 (a succeeds?):
# icon at 915..947, text at 960..1135
# y: cy=285. Text: 285-17.5 = 267.5..302.5. Icon: 285-16 = 269..301.
pts1 = [
    ("text top-right", 1135, 267.5), ("text bot-right", 1135, 302.5),
    ("icon top-left", 915, 269), ("icon bot-left", 915, 301)
]

# Right diamond 2 (b succeeded?):
# text width 196 (from 950 to 1146? or total w = 32 + 12 + 196 = 240 px, half=120)
# group: 1025-120 = 905 to 1025+120 = 1145
# icon at 905..937, text at 949..1145
# y: cy=535. Text: 535-17.5 = 517.5..552.5. Icon: 535-16 = 519..551.
pts2 = [
    ("text top-right", 1145, 517.5), ("text bot-right", 1145, 552.5),
    ("icon top-left", 905, 519), ("icon bot-left", 905, 551)
]

for rx in [190, 200, 210, 220, 230]:
    for ry in [65, 70, 75, 80, 85]:
        m1 = min(dist_to_diamond(px, py, 1025, 285, rx, ry) for _, px, py in pts1)
        m2 = min(dist_to_diamond(px, py, 1025, 535, rx, ry) for _, px, py in pts2)
        if m1 >= 16.0 and m2 >= 16.0:
            print(f"PASS rx={rx}, ry={ry}: m1={m1:.2f}px, m2={m2:.2f}px")
            break
