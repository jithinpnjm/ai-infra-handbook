from test_card_paddings import check_panel

# Card 2:
check_panel(2, 'A', (850, 217, 680, 128), 872, [217+40, 217+70, 217+100], 24, [
    "a one-minute average shows a device at 80%",
    "while one-second samples show bursts to",
    "100% with queueing (Case 1)"
])
check_panel(2, 'B', (850, 357, 680, 116), 872, [357+62], 24, [
    "shorten the interval before you move on"
])

# Card 3:
check_panel(3, 'A', (70, 672, 680, 128), 92, [672+40, 672+70, 672+100], 24, [
    "profilers, tracers and heavy sampling use",
    "CPU and can turn a rare stall into a",
    "constant one on a GPU node"
])
check_panel(3, 'B', (70, 812, 680, 116), 92, [812+44, 812+76], 24, [
    "start with cheap counters; turn on heavy",
    "tools only for a short, announced window"
])

# Card 4:
check_panel(4, 'A', (850, 672, 680, 116), 872, [672+44, 672+76], 24, [
    "you find a real fault, fix it, and stop, but",
    "it explains only a fraction of the slowdown"
])
check_panel(4, 'B', (850, 800, 680, 128), 872, [800+40, 800+70, 800+100], 24, [
    "check the fix against the original problem",
    "statement; if step time did not return to",
    "baseline, the investigation is not finished"
])

print("All panels across all 4 cards validated!")
