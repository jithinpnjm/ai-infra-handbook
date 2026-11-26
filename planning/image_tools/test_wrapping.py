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

# Let's test full width 1520 px (x: 40 to 1560):
# Inside 1520 px, with 56px icon + paddings (e.g. icon at x=64, text at x=140):
# text width available = 1560 - 40 - 140 = 1380 px.
# At 24px sans (0.6 * 24 = 14.4 px/char), max chars = 1380 / 14.4 = 95 chars.
# At 24px mono (0.62 * 24 = 14.88 px/char), max chars = 1380 / 14.88 = 92 chars.

print("=== Full width text wrapping ===")
for name, txt, max_c in [
    ("Cost strip", "each fact is a probe on each host: seconds per host before your first real task, minutes on hundreds of nodes", 90),
    ("Prefer strip", "ansible_facts[distribution] instead of the short injected names such as ansible_distribution: older names share one global space, so a host-reported value can sit next to your own variable of the same name; inject_facts_as_vars controls the short names", 90),
    ("Example line", "inventory_hostname: ansible_facts[distribution] ansible_facts[distribution_version], kernel ansible_facts[kernel], ansible_facts[processor_vcpus] vCPUs, (ansible_facts[memtotal_mb] / 1024) | round(1) GiB RAM, primary IP ansible_facts[default_ipv4][address]", 85),
    ("Example note", "GiB is binary: 1 GiB is 1024 MiB; the value is a plain number so the division needs no conversion", 90),
]:
    lines = wrap_text(txt, max_c)
    print(f"\n{name} ({len(lines)} lines):")
    for l in lines:
        print(f"  len={len(l):2d}: {l}")
