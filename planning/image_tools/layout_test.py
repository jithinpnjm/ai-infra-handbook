# Let's verify text wrapping and dimensions for all boxes

def wrap_text(text, max_chars):
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

c4 = "each line uses the host's ansible_host and its name, so the file follows the inventory: add a host to the inventory, run the playbook, and the new line appears without anyone touching the file"
print("Callout 4 wrapped at 45 chars:")
for l in wrap_text(c4, 45):
    print(f"  ({len(l)} chars, {len(l)*14.4:.1f}px) {l}")

c3 = "the loop writes one line per host in sorted order: the sort keeps the output the same on every render"
print("\nCallout 3 wrapped at 50 chars:")
for l in wrap_text(c3, 50):
    print(f"  ({len(l)} chars, {len(l)*14.4:.1f}px) {l}")

inp = "inventory entry gpu001 with its ansible_host value, and the cluster_domain variable"
print("\nInput wrapped at 40 chars:")
for l in wrap_text(inp, 40):
    print(f"  ({len(l)} chars, {len(l)*14.4:.1f}px) {l}")

outp = "the ansible_host value, then gpu001 followed by the cluster_domain value, then gpu001"
print("\nOutput wrapped at 40 chars:")
for l in wrap_text(outp, 40):
    print(f"  ({len(l)} chars, {len(l)*14.4:.1f}px) {l}")

