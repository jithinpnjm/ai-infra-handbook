import xml.etree.ElementTree as ET
import re

# Let's verify the exact labels and test text wrapping and padding
expected_labels = [
    "Retry layers multiply",
    "SDK",
    "gateway",
    "mesh sidecar",
    "router",
    "(and sometimes more)",
    "retries on its own",
    "Arithmetic panel",
    "One client, k attempts, failure chance p: expected attempts = 1 + p + p squared ... p to the power k - 1; for k = 4: p 0.1 gives 1.11, p 0.5 gives 1.875, p 0.8 gives 2.95",
    "SRE chapter: three layers each making 3 retries (4 attempts) can create 64 attempts at the bottom (4 x 4 x 4)",
    "AWS builders article: 243 times for a five-deep call chain = 3 to the power 5, three attempts per layer",
    "With 4 attempts per layer, five layers give 1,024",
    "set the budget at the gateway in one layer and turn off every other retry loop; retry at the layer directly above the one rejecting, not at every layer; if a large share of backends is overloaded, do not retry at all"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. len={len(l):3d}: '{l}'")
