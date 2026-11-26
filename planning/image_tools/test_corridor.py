# Let us test this corridor design
# Left container: x = 60 to 770 (w = 710)
# Boxes inside RED: x = 90 to 620 (w = 530)
# Right corridor inside RED: x = 620 to 770 (w = 150)
# Header: icon at x = 95, y = 255. Text at x = 165, y = 295.
# Max text width at 26px = 31 * 0.6 * 26 = 483 px. 165 + 483 = 648 < 770. (Padding 122px!)
# Latency box: x = 90, y = 330, w = 530, h = 130
# Traffic box: x = 90, y = 495, w = 530, h = 130
# Errors box: x = 90, y = 660, w = 530, h = 130

# Arrows:
# Arrow 1 (Latency): M 580 166 V 205 H 355 V 328
# Arrow 2 (Traffic): M 650 166 V 560 H 622
# Arrow 3 (Errors): M 700 166 V 725 H 622
# Arrow 4 (Saturation): M 950 166 V 205 H 1185 V 328

print("Corridor routes:")
print("Arrow 1: leaves at x=580, y=166 -> H to 355 -> V to 328 (enters top of Latency)")
print("Arrow 2: leaves at x=650, y=166 -> straight V at 650 to y=560 -> H left to 622 (enters right of Traffic)")
print("Arrow 3: leaves at x=700, y=166 -> straight V at 700 to y=725 -> H left to 622 (enters right of Errors)")
print("Arrow 4: leaves at x=950, y=166 -> H to 1185 -> V to 328 (enters top of Saturation)")
