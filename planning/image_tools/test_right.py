def wrap(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

inp = "inventory entry gpu001 with its ansible_host value, and the cluster_domain variable"
outp = "the ansible_host value, then gpu001 followed by the cluster_domain value, then gpu001"

print("Input 28px sans (0.6*28 = 16.8px/char):")
# Available width from x=940 to 1520 is 580px -> max chars = 580 / 16.8 = 34
for l in wrap(inp, 32):
    print(f"  [{len(l)} chars, {len(l)*16.8:.1f}px] {l}")

print("\nOutput 28px sans (0.6*28 = 16.8px/char):")
for l in wrap(outp, 32):
    print(f"  [{len(l)} chars, {len(l)*16.8:.1f}px] {l}")
