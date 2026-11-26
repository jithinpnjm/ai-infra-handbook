import xml.etree.ElementTree as ET

# Test vertical clearance for each text line inside its parent card/box
# For font-size fs:
# ascender = 0.8 * fs
# descender = 0.25 * fs
# top of text = y - ascender
# bottom of text = y + descender

def check_vertical_clearances():
    # items: (name, box_y, box_h, [(line_text, y, fs)])
    items = [
        ("Lane 1 Header", 110, 100, [("what exists", 168, 30)]),
        ("Lane 1 Content", 110, 100, [
            ("weights load for about 90 seconds", 152, 24),
            ("('loading weights 62%' then nothing in the previous logs)", 186, 24)
        ]),
        ("Lane 2 Header", 275, 245, [
            ("broken", 380, 30),
            ("probes", 418, 30)
        ]),
        ("Lane 2 Config", 275, 125, [
            ("liveness initialDelaySeconds 5,", 312, 24),
            ("periodSeconds 10, failureThreshold 1,", 343, 24),
            ("no startup probe", 374, 24)
        ]),
        ("Lane 2 Impact", 275, 125, [
            ("restart count 40,", 328, 24),
            ("one restart every four minutes", 362, 24)
        ]),
        ("Lane 2 Kill Event", 420, 100, [
            ("first check near 5 s fails, event 'Unhealthy: Liveness probe failed'", 458, 24),
            ("three times then 'Killing: failed liveness probe, will be restarted'", 492, 24)
        ]),
        ("Lane 3 Header", 575, 110, [("fixed", 640, 30)]),
        ("Lane 3 Window", 575, 110, [
            ("startup probe with failureThreshold 30 and", 620, 24),
            ("period 10 gives a 300 second window", 654, 24)
        ]),
        ("Lane 3 Liveness", 575, 110, [
            ("liveness only starts after", 620, 24),
            ("the startup probe passes", 654, 24)
        ]),
        ("Restart Strip", 725, 80, [
            ("starts at 10 s, doubles, capped at 300 s, resets after ten clean minutes", 772, 24)
        ]),
        ("Contrast Panel", 845, 110, [
            ("OOM kill shows Last State Terminated, Reason OOMKilled, Exit Code 137;", 890, 24),
            ("here Reason is Error and no OOMKilled", 924, 24)
        ]),
        ("Takeaway Bar", 995, 100, [
            ("liveness answers is this process stuck, not is it ready;", 1038, 24),
            ("slow starters get a startup probe sized to a measured load time", 1072, 24)
        ])
    ]

    all_pass = True
    print("=== VERTICAL CLEARANCES (RULE: >= 16px from box top and bottom) ===")
    for name, by, bh, lines in items:
        first_line_y, first_fs = lines[0][1], lines[0][2]
        last_line_y, last_fs = lines[-1][1], lines[-1][2]
        
        top_text = first_line_y - 0.8 * first_fs
        bottom_text = last_line_y + 0.25 * last_fs
        
        pad_top = top_text - by
        pad_bottom = (by + bh) - bottom_text
        
        ok_top = pad_top >= 16.0
        ok_bottom = pad_bottom >= 16.0
        if not (ok_top and ok_bottom):
            all_pass = False
        print(f"[{'PASS' if ok_top and ok_bottom else 'FAIL'}] {name:20s} top_pad={pad_top:4.1f}px, bot_pad={pad_bottom:4.1f}px")

    assert all_pass, "Some vertical clearances failed!"
    print("All vertical clearances >= 16px!")

check_vertical_clearances()
