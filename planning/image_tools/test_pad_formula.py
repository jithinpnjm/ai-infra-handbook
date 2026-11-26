import xml.etree.ElementTree as ET

# Step 1: y=160 to 410 (h=250)
# Subcard: y=225 to 400 (h=175, pad_t=65, pad_b=10 in outer)
# Inside subcard:
# 'token = None': y=254 (top=230, pad_t = 230-225 = 5? -> If subcard starts at y=220, top=230, pad_t=10.
# What if we don't need a nested subcard and nested loopbox?
# Look at Step 1: Step 1 itself is a card!
# Inside Step 1, can we just have the lines directly, or one clean code box?
# If Step 1 has a code card from y=220 to 395 (h=175):
# y=252: token = None (top=228, pad_t = 228-220 = 8)
# What if code card is y=215 to 395 (h=180)?
# y=248: token = None (top=224, pad_t = 224-215 = 9)

# Wait! How is padding tested in test_card_paddings_strict.py?
# Let's inspect test_card_paddings_strict.py again!
