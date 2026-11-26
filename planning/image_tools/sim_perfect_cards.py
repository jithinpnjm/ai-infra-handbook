from sim_full_audit import audit_card

# 3 cards per lane.
# Let card 1, 2, 3 all have height 80px or let 2-line cards have 88px, 1-line cards have 64px.
# What if all cards have equal height 80px?
# In an 80px card:
# For 1-line: baseline = top + 46.
#   top pad = 46 - 18 = 28px.
#   bottom pad = 80 - (46 + 6) = 28px. Perfect!
# For 2-line in 80px card:
#   line 1: top + 34 (top pad = 16px)
#   line 2: top + 60 (bottom pad = 80 - 66 = 14px -> slightly < 16)
# So for 2-line card, height = 86px or 88px!
# Let card 1: height 88px.
# Card 2: height 88px (allows 2 lines in Right lane!).
# Card 3: height 68px.
# Let us test this exact geometry!

lane_y = 144
header_h = 66
card1_y = lane_y + header_h + 12 # 222
card1_h = 88 # ends at 310
gap = 10
card2_y = card1_y + card1_h + gap # 320
card2_h = 88 # ends at 408
card3_y = card2_y + card2_h + gap # 418
card3_h = 68 # ends at 486
lane_h = card3_y + card3_h + 14 - lane_y # 500 - 144 = 356px

print("=== Left Lane Cards ===")
audit_card("Left Card 1", 58, card1_y, 704, card1_h, [
    ("source .venv/bin/activate puts .venv/bin ", 76, card1_y + 34),
    ("at the front of PATH and sets VIRTUAL_ENV", 76, card1_y + 64)
])

audit_card("Left Card 2", 58, card2_y, 704, card2_h, [
    ("python resolves to the venv interpreter", 76, card2_y + 48)
])

audit_card("Left Card 3", 58, card3_y, 704, card3_h, [
    ("import works", 76, card3_y + 40)
])

print("\n=== Right Lane Cards ===")
audit_card("Right Card 1", 838, card1_y, 704, card1_h, [
    ("no activation, a different PATH", 856, card1_y + 48)
])

audit_card("Right Card 2", 838, card2_y, 704, card2_h, [
    ("bare python3 resolves to the ", 856, card2_y + 34),
    ("system interpreter", 856, card2_y + 64)
])

audit_card("Right Card 3", 838, card3_y, 704, card3_h, [
    ("ModuleNotFoundError: No module named x", 856, card3_y + 40)
], is_mono=True)

print(f"\nLane bottom is at {lane_y + lane_h}")
