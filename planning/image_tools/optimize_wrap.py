t1 = "Cost-optimised: shares instances across many models, loads on demand, bin-packs (fitting as many models onto each machine as possible, like boxes in a van); cheap but reactive, surges hurt; maps to Nebius serverless endpoints for shared pools of popular models (my reading)"

# Let's wrap t1 so no line exceeds 43 characters
words = t1.split()
print("Total words:", len(words))

# Ideal split for t1:
lines_t1 = [
    "Cost-optimised:", # 15 chars, fs=30
    "shares instances across many models,", # 35 chars
    "loads on demand, bin-packs (fitting as many", # 42 chars
    "models onto each machine as possible, like", # 42 chars
    "boxes in a van); cheap but reactive, surges", # 43 chars
    "hurt; maps to Nebius serverless endpoints", # 41 chars
    "for shared pools of popular models", # 34 chars
    "(my reading)", # 12 chars
]

full = " ".join([l.strip() for l in lines_t1])
print("Matches original?", full == t1)
for l in lines_t1:
    fs = 30 if "Cost-optimised:" in l else 24
    w = len(l) * fs * 0.6
    print(f"[{len(l):2d} chars, {w:5.1f}px] '{l}' (right pad: {730 - 45 - w:.1f}px)")
