# Test wrapping Step 11 onto multiple lines
# Label: "CRI: RunPodSandbox, CreateContainer, StartContainer (CNI, CSI mounts)"
lines3 = [
    "CRI: RunPodSandbox,",
    "CreateContainer, StartContainer",
    "(CNI, CSI mounts)"
]
print("3 lines:")
for l in lines3:
    w = len(l) * 0.62 * 24
    print(f"  '{l}': w={w:.1f}px, min_box={w+32:.1f}px")

lines4 = [
    "CRI: RunPodSandbox,",
    "CreateContainer,",
    "StartContainer",
    "(CNI, CSI mounts)"
]
print("\n4 lines:")
for l in lines4:
    w = len(l) * 0.62 * 24
    print(f"  '{l}': w={w:.1f}px, min_box={w+32:.1f}px")
