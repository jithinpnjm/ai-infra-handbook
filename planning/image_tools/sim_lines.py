def measure_line(segments):
    w = 0
    for text, is_mono, fs in segments:
        cw = (0.62 if is_mono else 0.6) * fs
        w += len(text) * cw
    return w

# Card 1 width = 710, box from x=60 to 770. Padding left=25, right=25. Max text width = 710 - 50 = 660.
# Header icon: 56px + circle (r=24 -> d=48).
# If icon and step circle are at the top of the card:
# e.g., top row of card has:
# Circle 1 (cx=100, cy=150)
# Icon (x=140, y=122, w=56, h=56)
# Header text: "Collect as you go:" at (x=215, y=160, font-size=30 bold)
# Then below the header row, the full text continues with full card width!
# From y=210 downwards:
# Text x=95 (leaving 35px padding from left x=60, and 35px from right x=770 -> max width 640px).

