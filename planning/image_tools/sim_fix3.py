from sim_layout import check_wrap

def w_sans(text, size=24):
    return len(text) * size * 0.6

f3 = [
    "if a published port must stay private",
    "on a shared host, restrict it in",
    "DOCKER-USER before you publish it"
]

for l in f3:
    print(f"'{l}' w={w_sans(l):.1f}px <= 785px ({w_sans(l) <= 785})")
