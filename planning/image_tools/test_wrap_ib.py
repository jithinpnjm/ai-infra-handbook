from test_geometry import wrap_text, text_width

text = "InfiniBand: credit-based flow control per virtual lane, lossless by construction; LIDs and GIDs replace MACs and IPs; the Subnet Manager programs forwarding tables"

# Let's test max_width = 390
lines = wrap_text(text, 390, 24)
print(f"Max 390 px ({len(lines)} lines):")
for l in lines:
    print(f"   [{text_width(l, 24):5.1f}px] '{l}'")

