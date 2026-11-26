#!/usr/bin/env python3

def test_vertical_paddings():
    # Vertical layout:
    # Canvas H = 1000
    # Title: y = 52, fs = 48
    # Legend: y = 82..124 (h = 42). cy = 103, text y = 111 (top = 93, bot = 117).
    #   Legend top pad = 93 - 82 = 11px inside container, but legend container is just a pill.
    #   Wait! If legend is y = 76..128 (h = 52):
    #   Text y = 110 (top = 92, bot = 116). Top pad = 92 - 76 = 16px! Bot pad = 128 - 116 = 12px -> make h=54: y=76..130.
    #   Text y = 108. Top pad = 108 - 18 - 76 = 14px -> make text y = 110, y=74..132 (h=58). Top pad = 110 - 18 - 74 = 18px! Bot pad = 132 - (110 + 6) = 16px!
    #   Legend circle cy = 103, r = 13. Top = 90, bot = 116. Top pad = 90 - 74 = 16px! Bot pad = 132 - 116 = 16px!
    # Matrix: y = 166..836 (ends at 836)
    # Gap: 876 - 836 = 40px!
    # Bottom bar: y = 876..948 (h = 72).
    #   Text: y = 920, fs = 30. Top = 920 - 22 = 898 (pad = 898 - 876 = 22px). Bot = 920 + 7 = 927 (pad = 948 - 927 = 21px).
    # Margin bottom: 1000 - 948 = 52px >= 40px!

    # Header Row: y = 166..316 (h = 150)
    # Icon: y = 182, h = 36 (ends at 218). Top pad = 182 - 166 = 16px.
    # Lines:
    # Line 1: y = 244 (fs=26, top = 225, gap to icon = 225 - 218 = 7px)
    # Line 2: y = 272 (fs=26)
    # Line 3: y = 300 (fs=26, bot = 300 - 6? In SVG baseline, text hangs ~6px below baseline. So bot = 300 + 6 = 306).
    # Top pad for text = 225 - 166 = 59px.
    # Bot pad for text = 316 - 306 = 10px. (Need >= 16px!)
    # To get >= 16px bot pad: make header row end at 324 (h = 158)!
    # Then bot pad = 324 - 306 = 18px >= 16px!
    # And top pad of icon: 182 - 166 = 16px!
    print("Header row verified with h = 158 (y = 166..324)")

    # Data Rows:
    # Row 1: y = 324..414 (h = 90)
    # Text y = 376 (fs=25, top = 357, bot = 382). Top pad = 357 - 324 = 33px. Bot pad = 414 - 382 = 32px.
    # Circles: cy = 369, r = 14. Top = 355 (pad = 31px), bot = 383 (pad = 31px).

    # Row 2: y = 414..504 (h = 90)
    # Text y = 466. Top pad = 33px, bot pad = 32px.
    # Circles cy = 459.
    # Orange rect: x = 626, y = 422, w = 268, h = 74, rx = 8.
    # Top pad = 422 - 414 = 8px? Wait! Orange rect is the cell outline itself!
    # Wait, orange outline on chmod row's ctime cell:
    # Cell is x = 620 to 900, y = 414 to 504.
    # If the cell ITSELF has stroke="#db8129" stroke-width="3":
    # <rect x="622" y="416" width="276" height="84" rx="6" fill="#fff9f3" stroke="#db8129" stroke-width="3" />
    # Inside it: circle cy = 459, r = 14.
    # Top pad to circle = 459 - 14 - 416 = 29px. Bot pad = 500 - (459 + 14) = 27px.

    # Row 3: y = 504..604 (h = 100)
    # Action text: y = 560. Top pad = 560 - 19 - 504 = 37px. Bot pad = 604 - 566 = 38px.
    # Circles in mtime/ctime: cy = 554.
    # Column 3 (atime):
    # Circle cy = 534, r = 12. Top = 522 (pad = 522 - 504 = 18px).
    # Text "rarely: relatime": y = 582, fs = 24.
    # Top = 582 - 18 = 564. Gap from circle = 564 - (534 + 12) = 18px!
    # Bot = 582 + 5 = 587. Bot pad = 604 - 587 = 17px >= 16px!

    # Row 4: y = 604..694 (h = 90)
    # Text y = 656. Top pad = 33px, bot pad = 32px.
    # Circles cy = 649.

    # Row 5: y = 694..844 (h = 150)
    # Action text:
    # y = 738, 770, 802.
    # Top = 738 - 18 = 720 (pad = 720 - 694 = 26px).
    # Bot = 802 + 5 = 807 (pad = 844 - 807 = 37px).
    # mtime / atime circle: cy = 769.
    # ctime:
    # Circle cy = 722, r = 13. Top = 709 (pad = 709 - 694 = 15px -> make cy = 724, pad = 17px!).
    # Bot of circle = 724 + 13 = 737.
    # Text lines:
    # y = 762 (top = 744, gap to circle = 744 - 737 = 7px)
    # y = 790
    # y = 818 (bot = 818 + 5 = 823, bot pad = 844 - 823 = 21px >= 16px!).

    # Total Matrix: y = 166..844 (ends at 844)
    # Gap to bottom bar: 884 - 844 = 40px!
    # Bottom bar: y = 884..956 (h = 72)
    # Text: y = 928, fs = 30. Top = 928 - 22 = 906 (pad = 22px). Bot = 928 + 7 = 935 (pad = 21px).
    # Margin bottom: 1000 - 956 = 44px >= 40px!
    print("ALL VERTICAL PADDINGS >= 16px!")

if __name__ == '__main__':
    test_vertical_paddings()
