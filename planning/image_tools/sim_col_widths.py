# Total width budget = 1520 (canvas 1600, margins 40 and 40)
# Gap between grid and right strip: 25 px
# Width left for Grid + Right Strip = 1495 px.
# Let's allocate:
# Fabric Col: 285 px
# L1/L2 Col: 270 px
# L3 Col: 270 px
# L4 Col: 370 px
# Grid total = 285 + 270 + 270 + 370 = 1195 px
# Gap = 25 px
# Right strip (NCCL): 300 px
# Total = 1195 + 25 + 300 = 1520 px! Exactly 1520 px!

col_widths = {
    'fabric': 285,
    'l12': 270,
    'l3': 270,
    'l4': 370,
    'nccl': 300
}

# Usable widths (width - 32):
# fabric: 253 px
# l12: 238 px
# l3: 238 px
# l4: 338 px
# nccl: 268 px

# Let's test Fabric at 28 px bold (16.8 px/char):
lines = ['Ethernet with', 'TCP (front end,', 'storage,', 'control plane)']
for l in lines:
    px = len(l) * 0.6 * 28
    print(f"'{l}': {px:.1f}px / 253px ({'OK' if px <= 253 else 'OVERFLOW'})")

