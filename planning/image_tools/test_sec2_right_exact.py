def check_sec2_right():
    # Card 1: x=1000, y=330, w=560, h=150
    # Icon beside text or top?
    # If icon at left: x=1020..1076 (56px)
    # Available width for text = 560 - 20 - 56 - 16 - 20 = 448 px
    # Max chars at 24px: 448 / 14.4 = 31 chars!
    lines1 = [
        "each decision is random and made", # 32 chars -> 460.8 px
        "per connection, with no view of",  # 31 chars -> 446.4 px
        "how busy each pod is"              # 20 chars -> 288.0 px
    ]
    # If icon is centered at top: y = 348..396 (48px high)
    # Then text has full width = 560 - 32 = 528 px!
    # Max chars at 24px: 528 / 14.4 = 36.6 chars!
    # 32 chars * 14.4 = 460.8 px -> pad = (560 - 460.8)/2 = 49.6 px >= 16 px!
    # Vertical fit with icon at top:
    # Icon: y = 346, h = 44 (ends at 390)
    # Text line 1: baseline = 416 (top_pad = 416-24-390 = 2) wait!
    # What if icon is at top-left, and text is 3 lines beside it?
    # Let's check text lines if 4 lines:
    lines1_4 = [
        "each decision is random", # 23 chars -> 331.2 px
        "and made per connection,", # 24 chars -> 345.6 px
        "with no view of how",      # 19 chars -> 273.6 px
        "busy each pod is"          # 16 chars -> 230.4 px
    ]
    # With 4 lines, max chars = 24 chars -> 345.6 px!
    # Then icon (56px) at x=1020 + gap (16px) + text (345.6px) = 437.6 px!
    # Left pad: 20px, right pad: 560 - 437.6 = 122.4 px!
    # And vertical: 4 lines of 24px with line-height 28px:
    # 4 lines fit in height 150 with plenty of room!
    print("Card 1 with 4 lines fits beside icon with pad > 100px!")

check_sec2_right()
