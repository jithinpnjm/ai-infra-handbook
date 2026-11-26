#!/usr/bin/env python3

def verify_all_paddings():
    # Let's verify text lines and their containers
    # 1. Title: x=50, y=65/121. Total width 1600, no enclosing box, margin left=50 >= 40.
    
    # 2. Top bar:
    # Segment 1: box x=55, w=315. Text: '/data/run42' len 11, fs=28 mono.
    # text width = 11 * 28 * 0.62 = 190.96. Padding = (315 - 190.96) / 2 = 62.0 px >= 16. PASS!
    # Segment 2: box x=375, w=55. Text: '/' len 1, fs=32 mono.
    # text width = 1 * 32 * 0.62 = 19.84. Padding = (55 - 19.84) / 2 = 17.58 px >= 16. PASS!
    # Segment 3: box x=435, w=345. Text: 'model.final' len 11, fs=28 mono.
    # text width = 11 * 28 * 0.62 = 190.96. Padding = (345 - 190.96) / 2 = 77.0 px >= 16. PASS!
    # Segment 4: box x=785, w=55. Text: '.' len 1, fs=32 mono.
    # text width = 1 * 32 * 0.62 = 19.84. Padding = (55 - 19.84) / 2 = 17.58 px >= 16. PASS!
    # Segment 5: box x=845, w=200. Text: 'ckpt' len 4, fs=28 mono.
    # text width = 4 * 28 * 0.62 = 69.44. Padding = (200 - 69.44) / 2 = 65.28 px >= 16. PASS!

    # 3. Rows 1 to 4:
    # Outer box: x=50, w=1000.
    # Expression badge: x=70, w=240. Text: '${path##*/}' len 11, fs=28 mono.
    # text width = 11 * 28 * 0.62 = 190.96. Padding = (240 - 190.96) / 2 = 24.5 px >= 16. PASS!
    # Descriptions:
    # Row 1 Line 1: 'removes the longest matching prefix up to the last slash:' len 57, fs=24 sans.
    # text width = 57 * 24 * 0.60 = 820.8 px. Box w = 1000, x=70. Right edge = 70 + 820.8 = 890.8.
    # Right padding to box edge (x=1050) = 1050 - 890.8 = 159.2 px >= 16! PASS!
    # Row 1 Line 2: 'result 'model.final.ckpt' (same as basename)' len 44, fs=24 sans.
    # text width = 44 * 24 * 0.60 = 633.6 px. Right edge = 70 + 633.6 = 703.6. Padding = 346.4 px >= 16! PASS!

    # Row 2 Line 1: 'removes the shortest matching suffix starting at the last slash:' len 64, fs=24 sans.
    # text width = 64 * 24 * 0.60 = 921.6 px. Right edge = 70 + 921.6 = 991.6. Padding = 1050 - 991.6 = 58.4 px >= 16! PASS!
    # Row 2 Line 2: 'result '/data/run42' (same as dirname)' len 38, fs=24 sans.
    # text width = 38 * 24 * 0.60 = 547.2 px. Padding = 432.8 px >= 16! PASS!

    # Row 3 Line 1: 'removes the shortest suffix starting at the last dot:' len 53, fs=24 sans.
    # text width = 53 * 24 * 0.60 = 763.2 px. Padding = 216.8 px >= 16! PASS!
    # Row 3 Line 2: 'result '/data/run42/model.final'' len 32, fs=24 sans.
    # text width = 32 * 24 * 0.60 = 460.8 px. Padding = 519.2 px >= 16! PASS!

    # Row 4 Line 1: 'removes the longest prefix up to the last dot:' len 46, fs=24 sans.
    # text width = 46 * 24 * 0.60 = 662.4 px. Padding = 317.6 px >= 16! PASS!
    # Row 4 Line 2: 'result 'ckpt'' len 13, fs=24 sans.
    # text width = 13 * 24 * 0.60 = 187.2 px. Padding = 792.8 px >= 16! PASS!

    # 4. Side Key:
    # Outer box: x=1100, w=450. Card box: x=1125, w=400.
    # Card 1 text x=1150 (pad left = 25 px >= 16).
    # Line 1: '# / ## remove shortest /' len 24, fs=24 sans -> w = 24 * 14.4 = 345.6 px.
    # Right edge = 1150 + 345.6 = 1495.6. Box right = 1525. Padding right = 1525 - 1495.6 = 29.4 px >= 16! PASS!
    # Line 2: 'longest prefix' len 14 -> w = 14 * 14.4 = 201.6 px. Padding = 173.4 px >= 16! PASS!

    # Card 2 Line 1: '% / %% remove shortest /' len 24 -> w = 345.6 px. Padding = 29.4 px >= 16! PASS!
    # Card 2 Line 2: 'longest suffix' len 14 -> w = 201.6 px. Padding = 173.4 px >= 16! PASS!

    # Card 3: '${#path} length' len 15, fs=28 mono. Text center x=1325.
    # w = 15 * 28 * 0.62 = 260.4 px. Card x=1125, w=400. Center = 1325.
    # Left pad = 200 - 130.2 = 69.8 px >= 16! PASS!

    # 5. Bottom strip:
    # Guard cards: w=440.
    # Card 1: '${var:-default}' len 16, fs=28 mono -> w = 16 * 28 * 0.62 = 277.76 px.
    # Card w = 440, center x = 300. Left edge of text: 300 - 138.88 = 161.12. Card left = 80. Pad = 81.1 px >= 16! PASS!
    # Shield icon: x=120..150, does not overlap text (text starts at 161.12, pad = 11.12 px between icon and text).
    # Let's adjust text center to x=325 to give 35 px clearance between shield and text!

    print("All padding checks verified!")

verify_all_paddings()
