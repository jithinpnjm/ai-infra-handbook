def build_svg():
    # Headers
    h_y = 66
    h_h = 60
    # text at h_y + 39 = 105:
    # 30px font: top = 105 - 22 = 83 (pad_top = 83 - 66 = 17)
    # bot = 105 + 7 = 112 (pad_bot = 126 - 112 = 14) -> make h_h = 62, text at 105: pad_bot = 128 - 112 = 16!
    # h_y = 66, h_h = 62. text at y = 105. pad_top = 17, pad_bot = 17!
    
    # Gap 7
    # Row 1: y = 135, h = 112
    # Col 0 (30px 2 lines): text at 173 (dy=32):
    # line 1: 173 (top = 173 - 22 = 151, pad_top = 151 - 135 = 16)
    # line 2: 205 (bot = 205 + 7 = 212, pad_bot = 247 - 212 = 35)
    # Col 1 (24px 1 line): text at 195: top = 195-17=178 (pad 43), bot = 195+6=201 (pad 46)
    # Col 2 (24px 3 lines, dy=27):
    # line 1: 169 (top = 169 - 17 = 152, pad_top = 152 - 135 = 17)
    # line 2: 196
    # line 3: 223 (bot = 223 + 6 = 229, pad_bot = 247 - 229 = 18)
    
    # Gap 7
    # Row 2: y = 254, h = 138
    # Col 0 (30px 2 lines): text at 295 (dy=32):
    # line 1: 295 (top = 295 - 22 = 273, pad_top = 273 - 254 = 19)
    # line 2: 327 (bot = 327 + 7 = 334, pad_bot = 392 - 334 = 58)
    # Col 1 (24px 2 lines, dy=30): text at 310:
    # line 1: 310 (top = 310 - 17 = 293, pad_top = 39)
    # line 2: 340 (bot = 340 + 6 = 346, pad_bot = 392 - 346 = 46)
    # Col 2 (24px 4 lines, dy=26): text at 288:
    # line 1: 288 (top = 288 - 17 = 271, pad_top = 271 - 254 = 17)
    # line 2: 314
    # line 3: 340
    # line 4: 366 (bot = 366 + 6 = 372, pad_bot = 392 - 372 = 20)
    
    # Gap 7
    # Row 3: y = 399, h = 112
    # Col 0 (30px 2 lines): text at 437 (dy=32):
    # line 1: 437 (top = 437 - 22 = 415, pad_top = 415 - 399 = 16)
    # line 2: 469 (bot = 469 + 7 = 476, pad_bot = 511 - 476 = 35)
    # Col 1 (24px 2 lines, dy=30): text at 448:
    # line 1: 448 (top = 448 - 17 = 431, pad_top = 32)
    # line 2: 478 (bot = 478 + 6 = 484, pad_bot = 511 - 484 = 27)
    # Col 2 (24px 3 lines, dy=27): text at 433:
    # line 1: 433 (top = 433 - 17 = 416, pad_top = 416 - 399 = 17)
    # line 2: 460
    # line 3: 487 (bot = 487 + 6 = 493, pad_bot = 511 - 493 = 18)

    # Gap 7
    # Row 4: y = 518, h = 112
    # Col 0: text at 556 (dy=32):
    # line 1: 556 (top = 556 - 22 = 534, pad_top = 16)
    # line 2: 588 (bot = 588 + 7 = 595, pad_bot = 35)
    # Col 1: text at 567 (dy=30):
    # line 1: 567 (top = 567 - 17 = 550, pad_top = 32)
    # line 2: 597 (bot = 597 + 6 = 603, pad_bot = 27)
    # Col 2 (24px 3 lines, dy=27): text at 552:
    # line 1: 552 (top = 552 - 17 = 535, pad_top = 17)
    # line 2: 579
    # line 3: 606 (bot = 606 + 6 = 612, pad_bot = 18)

    # Gap 7
    # Row 5: y = 637, h = 112
    # Col 0 (30px 1 line): text at 695: top = 695 - 22 = 673 (pad_top = 36), bot = 695 + 7 = 702 (pad_bot = 47)
    # Col 1 (24px 1 line): text at 698: top = 698 - 17 = 681 (pad_top = 44), bot = 698 + 6 = 704 (pad_bot = 45)
    # Col 2 (24px 3 lines, dy=27): text at 671:
    # line 1: 671 (top = 671 - 17 = 654, pad_top = 17)
    # line 2: 698
    # line 3: 725 (bot = 725 + 6 = 731, pad_bot = 18)

    # Gap 7
    # Row 6: y = 756, h = 138
    # Col 0 (30px 2 lines): text at 797 (dy=32):
    # line 1: 797 (top = 797 - 22 = 775, pad_top = 19)
    # line 2: 829 (bot = 829 + 7 = 836, pad_bot = 58)
    # Col 1 (24px 1 line): text at 830: top = 830 - 17 = 813 (pad 57), bot = 830 + 6 = 836 (pad 58)
    # Col 2 (24px 4 lines, dy=26): text at 790:
    # line 1: 790 (top = 790 - 17 = 773, pad_top = 17)
    # line 2: 816
    # line 3: 842
    # line 4: 868 (bot = 868 + 6 = 874, pad_bot = 20)

    # Gap 9
    # Costs: y = 903, h = 114
    # text at 938 (dy=27):
    # line 1: 938 (top = 938 - 17 = 921, pad_top = 18)
    # line 2: 965
    # line 3: 992 (bot = 992 + 6 = 998, pad_bot = 1017 - 998 = 19)

    # Gap 8
    # Footer: y = 1025, h = 84
    # text at 1060 (dy=28):
    # line 1: 1060 (top = 1060 - 17 = 1043, pad_top = 18)
    # line 2: 1088 (bot = 1088 + 6 = 1094, pad_bot = 1109 - 1094 = 15) -> make h = 86! pad_bot = 17!

    # Gap 8
    # Bottom bar: y = 1119, h = 56
    # text at 1154:
    # line 1: 1154 (top = 1154 - 17 = 1137, pad_top = 18)
    # bot = 1154 + 6 = 1160 (pad_bot = 1175 - 1160 = 15) -> make h = 58, text at 1154: pad_top = 17, pad_bot = 17!
    # Bottom edge of bottom bar = 1119 + 58 = 1177 px!
    # Bottom margin = 1200 - 1177 = 23 px!
    
    print("Coordinates computed cleanly.")

build_svg()
