def plan_vertical_layout():
    # Elements:
    # 0. Title: y=50, font-size=48, bold
    # 1. Story strip: h=76, y=74..150
    # 2. Config card: h=52, y=162..214
    # 3. Pre-step: h=52, y=226..278
    # 4. Step 1 (orange): h=84, y=290..374 (2 lines)
    # 5. Step 2: h=52, y=386..438 (1 line)
    # 6. Step 3: h=116, y=450..566 (3 lines)
    # 7. Step 4: h=52, y=578..630 (1 line)
    # 8. Step 5: h=84, y=642..726 (2 lines)
    # 9. Gate: h=84, y=738..822 (2 lines)
    # 10. Strip (resume): h=52, y=834..886 (1 line)
    # Gap: 886 to 1110 = 224 px? Wait! That leaves 224 px empty space!
    
    total_content_height = 886
    print(f"Content ends at y={total_content_height}, H=1200, bottom bar at 1120..1180")
    # We can expand card heights and gaps so the timeline fills the canvas gracefully!
    
plan_vertical_layout()
