t2 = "Latency-optimised: dedicated always-on replicas; customer chooses GPU type, GPUs per replica and the replica range; maps to Nebius dedicated endpoints"

lines = [
    "Latency-optimised:",
    "dedicated always-on replicas;",
    "customer chooses GPU type, GPUs per replica",
    "and the replica range; maps to Nebius",
    "dedicated endpoints",
]

full = " ".join([l.strip() for l in lines])
print("Matches?", full == t2)
for l in lines:
    fs = 30 if "Latency-optimised:" in l else 24
    w = len(l) * fs * 0.6
    print(f"[{len(l):2d} chars, {w:5.1f}px] '{l}' (right pad: {730 - 45 - w:.1f}px)")
