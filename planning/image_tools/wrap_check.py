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

texts = {
    "Callout 1": "first line marks the file as generated so nobody edits it by hand",
    "Callout 2": "second line keeps the loopback address",
    "Callout 3": "the loop writes one line per host in sorted order: the sort keeps the output the same on every render",
    "Callout 4": "each line uses the host's ansible_host and its name, so the file follows the inventory: add a host to the inventory, run the playbook, and the new line appears without anyone touching the file",
    "Input": "inventory entry gpu001 with its ansible_host value, and the cluster_domain variable",
    "Output": "the ansible_host value, then gpu001 followed by the cluster_domain value, then gpu001"
}

for name, t in texts.items():
    print(f"=== {name} ===")
    for l in wrap(t, 38):
        print(f"  [{len(l)} chars, {len(l)*14.4:.1f}px] {l}")
