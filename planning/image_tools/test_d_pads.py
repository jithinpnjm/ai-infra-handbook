import math

def dist_to_diamond(px, py, cx, cy, rx, ry):
    dx = abs(px - cx)
    dy = abs(py - cy)
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    val = dx/rx + dy/ry
    return (1.0 - val) / scale

# Right diamond 1 (a succeeds?): cx=1025, cy=300, rx=230, ry=80
# icon: translate(915, 284), size 32x32 -> x in [915, 947], y in [284, 316]
# text: x in [970.6, 1145.4], y in [281, 316]
pts_r1 = [(970.6, 281), (1145.4, 281), (970.6, 316), (1145.4, 316), (915, 284), (947, 284), (915, 316), (947, 316)]
min_dr1 = min(dist_to_diamond(px, py, 1025, 300, 230, 80) for px, py in pts_r1)
print("Right diamond 1 min pad:", min_dr1)

# Right diamond 2 (b succeeded?): cx=1025, cy=575, rx=235, ry=85
# icon: translate(900, 559), size 32x32 -> x in [900, 932], y in [559, 591]
# text: x in [955.1, 1150.8], y in [556, 591]
pts_r2 = [(955.1, 556), (1150.8, 556), (955.1, 591), (1150.8, 591), (900, 559), (932, 559), (900, 591), (932, 591)]
min_dr2 = min(dist_to_diamond(px, py, 1025, 575, 235, 85) for px, py in pts_r2)
print("Right diamond 2 min pad:", min_dr2)
