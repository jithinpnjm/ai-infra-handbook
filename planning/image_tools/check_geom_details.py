def check_all():
    # Canvas: 1600 x 1200
    # Rule: "every text line must fit inside its box with at least 16 px padding."
    # Rule: "no label may overlap a box, arrow or another label"
    # Rule: "put edge labels in clear space beside the arrow"
    # Rule: "make boxes tall enough for all their text lines"
    # Rule: "Every node gets one simple outline icon drawn in SVG shapes (about 56 px, green stroke 4), placed beside or above its title, never overlapping text."
    
    # Let us check Box 1:
    # Title: Batch shell (script)
    # Icon: 56x56 px
    # If icon is beside title:
    # Icon at x=90, y=385, w=56, h=56.
    # Title at x=165, y=422 (font-size 32 bold, ascender ~24px -> top ~398, bottom ~428).
    # Icon is at x=90..146. Title starts at x=165. Gap = 19px! No overlap.
    # Title right: 165 + 20*0.6*32 = 165 + 384 = 549px. Box width is 900 (x=60..960). Right padding = 411px.
    # Subpanel for code:
    # x=90, y=455, w=840, h=60.
    # Code: 'trap kill -USR1 $pid; wait $pid USR1' (36 chars mono, 24px)
    # 36 * 0.62 * 24 = 535.7px.
    # Code text at x=115, y=492.
    # Left padding: 115 - 90 = 25px >= 16px!
    # Right padding: 930 - (115 + 535.7) = 279.3px >= 16px!
    # Top padding: 492 - 18 - 455 = 19px >= 16px!
    # Bottom padding: 515 - (492 + 5) = 18px >= 16px!
    # Box 1 height: y=365 to 535 (height 170).
    # Bottom padding of Box 1: 535 - 515 = 20px >= 16px!

    # Let us check Arrow 2:
    # Loop from Box 1 right edge (x=960)
    # Out to x=1005, down, back to x=960.
    # Circle (2) at cx=1005, cy=450, r=24.
    # Arrow 2 label:
    # Starts at x=1045.
    # Line 1: 'trap fires at once because' (26 chars * 14.4 = 374.4px)
    # Line 2: 'the shell is in wait, not in' (28 chars * 14.4 = 403.2px)
    # Line 3: 'a foreground command' (20 chars * 14.4 = 288px)
    # Rightmost point: 1045 + 403.2 = 1448.2px. Inside 1560px! Margin = 111.8px > 40px.
    # Y range: lines at y=422, 452, 482.
    # Top of text ~ 404, bottom ~ 488.
    # Completely clear of Box 1 (ends at x=960) and Circle 2 (ends at x=1029).

    # Let us check Arrow 3:
    # Between Box 1 (bottom y=535) and Box 2 (top y=605). Gap = 70px.
    # Arrow vertical line at x=350, from y=535 to y=605.
    # Circle (3) at cx=350, cy=570, r=24.
    # Arrow 3 label at x=395:
    # Line 1: 'kill -USR1 forwards the signal' (30 chars * 14.4 = 432px)
    # Line 2: 'to the training process' (23 chars * 14.4 = 331.2px)
    # Rightmost: 395 + 432 = 827px. Well inside Box 1/2 right edge (960px).
    # Lines at y=558, 586.
    # Fits inside the 70px vertical band!

    # Let us check Box 2:
    # y=605 to 775 (height 170).
    # Icon at x=90, y=625, w=56, h=56.
    # Text:
    # Line 1: 'python train.py' (monospace 30px bold, 15 chars * 0.62 * 30 = 279px).
    # Position: x=165, y=660.
    # Line 2: 'running in the background (&), pid saved in $pid' (sans 24px, 47 chars * 14.4 = 676.8px).
    # Position: x=165, y=702.
    # Left padding: 165 - 60 = 105px (with icon at 90..146, gap to text is 19px).
    # Right padding: 960 - (165 + 676.8) = 118.2px >= 16px!
    # Top padding: 660 - 22 - 605 = 33px >= 16px!
    # Bottom padding: 775 - (702 + 6) = 67px >= 16px!

    # Let us check Arrow 4:
    # Loop from Box 2 right edge (x=960)
    # Out to x=1005, down, back to x=960.
    # Circle (4) at cx=1005, cy=690, r=24.
    # Arrow 4 label at x=1045, y=698:
    # 'training writes the checkpoint' (30 chars * 14.4 = 432px).
    # Rightmost: 1045 + 432 = 1477px < 1560px! Margin = 83px > 40px!

    # Let us check Arrow 5:
    # Between Box 2 (bottom y=775) and Box 3 (top y=845). Gap = 70px.
    # Arrow vertical line at x=350, from y=775 to y=845.
    # Circle (5) at cx=350, cy=810, r=24.
    # Arrow 5 label at x=395, y=818:
    # 'wait returns, job ends cleanly' (30 chars * 14.4 = 432px).
    # Rightmost: 395 + 432 = 827px < 960px.
    # Fits inside the 70px vertical band!

    # Let us check Box 3:
    # y=845 to 975 (height 130).
    # Icon at x=90, y=882, w=56, h=56.
    # Text: 'wait $pid' (monospace 32px bold, 9 chars * 0.62 * 32 = 178.6px).
    # Position: x=165, y=920.
    # Left padding: 165 - 60 = 105px (gap from icon is 19px).
    # Right padding: 960 - (165 + 178.6) = 616.4px >= 16px!
    # Top padding: 920 - 24 - 845 = 51px >= 16px!
    # Bottom padding: 975 - (920 + 6) = 49px >= 16px!

    # Let us check Contrast Box:
    # Position: x=1010, y=775, width=530, height=200.
    # Right edge = 1540 (margin 60px > 40px).
    # Icon at x=1035, y=795, w=56, h=56.
    # Text:
    # Line 1: 'If python train.py ran in the' (30 chars * 14.4 = 432px)
    # Line 2: 'foreground, the shell would' (27 chars * 14.4 = 388.8px)
    # Line 3: 'defer the trap until it' (23 chars * 14.4 = 331.2px)
    # Line 4: 'finished' (8 chars * 14.4 = 115.2px)
    # Position: x=1105.
    # Left padding: 1105 - 1010 = 95px (gap from icon at 1035..1091 is 14px -> make text x=1110, gap = 19px!).
    # Right padding: 1540 - (1110 + 418) = 12px -> WAIT!
    # Look at Line 1: 'If python train.py ran in the' -> 30 chars.
    # 1110 + 432 = 1542 > 1540!
    # That would overflow the contrast box right edge!
    # Let us fix the line wrapping of the contrast box!
    # What if we wrap onto 4 lines with smaller line lengths, or center the text in the box?
    # Let us calculate:
    # Contrast box width = 530px (x=1010 to 1540).
    # If the icon is ABOVE the text or centered:
    # Icon at cx=1275 (center of 1010..1540), y=795..851.
    # Then text is centered at x=1275!
    # Max line width: 432px.
    # In 530px box, left = 1275 - 216 = 1059, right = 1275 + 216 = 1491!
    # Left padding: 1059 - 1010 = 49px >= 16px!
    # Right padding: 1540 - 1491 = 49px >= 16px!
    # That solves it completely and symmetrically!
    print("Geometry analysis complete!")

check_all()
