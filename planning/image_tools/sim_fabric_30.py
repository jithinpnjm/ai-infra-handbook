w = 260
usable_w = w - 32 # 228
fs = 30
char_w = 0.6 * fs # 18 px

fabrics = [
    ('Ethernet with TCP (front end, storage, control plane)', [
        'Ethernet with',
        'TCP (front end,',
        'storage,',
        'control plane)'
    ]),
    ('RoCE v2', ['RoCE v2']),
    ('InfiniBand', ['InfiniBand']),
    ('NVLink / NVSwitch', ['NVLink /', 'NVSwitch']),
    ('PCIe', ['PCIe'])
]

for name, lines in fabrics:
    print(f"\nFabric: {name}")
    for l in lines:
        px = len(l) * char_w
        print(f"  '{l}': {px:.1f}px / {usable_w}px ({'OK' if px <= usable_w else 'OVERFLOW'})")
