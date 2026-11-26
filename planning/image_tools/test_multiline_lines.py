# Let's test lines for Step 3, Step 5, Step 13:

# Step 3:
s3_lines = [
    "bind Pod → node",
    "(spec.nodeName)"
]
bw3 = 270.0
for l in s3_lines:
    w = len(l) * 0.6 * 24
    pad = (bw3 - w) / 2
    print(f"S3 line '{l}': w={w:.1f} pad={pad:.1f}")
    assert pad >= 16.0

# Step 5:
s5_lines = [
    "admit pod (resources, node-fit, kernel params),",
    "create pod dirs"
]
bw5 = 710.0
for l in s5_lines:
    w = len(l) * 0.6 * 24
    pad = (bw5 - w) / 2
    print(f"S5 line '{l}': w={w:.1f} pad={pad:.1f}")
    assert pad >= 16.0

# Step 13:
s13_lines = [
    "status updates",
    "(PodScheduled, Initialized,",
    "ContainersReady, Ready)"
]
bw13 = 430.0
for l in s13_lines:
    w = len(l) * 0.6 * 24
    pad = (bw13 - w) / 2
    print(f"S13 line '{l}': w={w:.1f} pad={pad:.1f}")
    assert pad >= 16.0

print("ALL MULTI-LINE PADDINGS PASS >= 16px!")
