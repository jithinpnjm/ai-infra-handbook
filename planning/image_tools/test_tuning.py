import xml.etree.ElementTree as ET

def test_tuning():
    card_analogy = (840, 575, 290, 130)
    card_libraries = (1150, 575, 410, 130)
    
    # Analogy text:
    # "a fuse in a wall" at x=985 centered
    # w = 16 * 14.4 = 230.4
    x_center = 985
    w_analogy = 16 * 14.4
    left = x_center - w_analogy / 2
    right = x_center + w_analogy / 2
    pad_left = left - 840
    pad_right = 1130 - right
    print(f"Analogy padding: left={pad_left:.1f}, right={pad_right:.1f} (both >= 16: {pad_left >= 16 and pad_right >= 16})")
    
    # Libraries lines:
    lines = [
        "pybreaker,",
        "circuitbreaker,",
        "or a class of",
        "about 30 lines"
    ]
    tx = 1220
    box_right = 1560
    for l in lines:
        w = len(l) * 14.4
        pad = box_right - (tx + w)
        print(f"Libraries line '{l}' | w={w:.1f} | end={tx+w:.1f} | pad_right={pad:.1f} (>=16: {pad >= 16})")

test_tuning()
