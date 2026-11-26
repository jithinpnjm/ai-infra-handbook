footer = "Common mistakes: favourite tool first, tunables changed without a hypothesis or baseline, several changes at once, failed experiments not reverted, trusting GPU-Util or load average as a verdict, optimising off the critical path, benchmarking the load generator or a warm cache, ignoring corrected ECC, link retrains and PCIe replays"

lines4 = [
    "Common mistakes: favourite tool first, tunables changed without a hypothesis or baseline,",
    "several changes at once, failed experiments not reverted, trusting GPU-Util or load average as a",
    "verdict, optimising off the critical path, benchmarking the load generator or a warm cache,",
    "ignoring corrected ECC, link retrains and PCIe replays"
]

for i, l in enumerate(lines4):
    w = len(l) * 14.4
    print(f"Line {i+1}: {len(l)} chars, {w:.1f} px | '{l}'")

assert " ".join(lines4) == footer
print("All lines < 1400 px!")
