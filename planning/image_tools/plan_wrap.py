def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

t1 = "Cost-optimised: shares instances across many models, loads on demand, bin-packs (fitting as many models onto each machine as possible, like boxes in a van); cheap but reactive, surges hurt; maps to Nebius serverless endpoints for shared pools of popular models (my reading)"
t2 = "Latency-optimised: dedicated always-on replicas; customer chooses GPU type, GPUs per replica and the replica range; maps to Nebius dedicated endpoints"
t3 = "a tenant calls a model no replica holds; tens of GB of weights must load onto a GPU, which takes seconds to minutes; cold start latency can cause timeouts and cascading failures"
t4 = "keep popular models always resident with at least two replicas; keep weights on local NVMe or a node-local cache so a new replica does not download from the object store"

# If box width is 710px, padding at least 16px means max width 710 - 32 = 678px.
# Conservative width at 24px is chars * 24 * 0.6 = chars * 14.4px.
# 678 / 14.4 = 47.08 chars max.
# At 30px bold: chars * 30 * 0.6 = chars * 18px.
# Let's inspect manual wraps around 40-44 chars:

print("--- T1 ---")
for l in wrap_text(t1, 44):
    print(f"[{len(l):2d} chars, {len(l)*14.4:5.1f}px] {l}")

print("\n--- T2 ---")
for l in wrap_text(t2, 44):
    print(f"[{len(l):2d} chars, {len(l)*14.4:5.1f}px] {l}")

print("\n--- T3 ---")
for l in wrap_text(t3, 44):
    print(f"[{len(l):2d} chars, {len(l)*14.4:5.1f}px] {l}")

print("\n--- T4 ---")
for l in wrap_text(t4, 44):
    print(f"[{len(l):2d} chars, {len(l)*14.4:5.1f}px] {l}")

