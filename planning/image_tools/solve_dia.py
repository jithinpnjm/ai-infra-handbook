import math

def solve_diamond(tw, th, min_pad=16.0):
    px = tw / 2
    py = th / 2
    # Try different rx, ry
    best = None
    for rx in range(140, 220, 5):
        for ry in range(50, 100, 5):
            scale = math.sqrt(1/(rx*rx) + 1/(ry*ry))
            val = px/rx + py/ry
            d = (1.0 - val) / scale
            if d >= min_pad:
                # valid!
                area = 2 * rx * ry
                if best is None or area < best[0]:
                    best = (area, rx, ry, d)
    return best

# "a succeeds?" with font-size 26: tw ~ 156, th ~ 28
res = solve_diamond(156, 28, 16.0)
print("a succeeds? (tw=156, th=28):", res)
# "b succeeded?" with font-size 25: tw ~ 170, th ~ 27
res2 = solve_diamond(170, 27, 16.0)
print("b succeeded? (tw=170, th=27):", res2)
