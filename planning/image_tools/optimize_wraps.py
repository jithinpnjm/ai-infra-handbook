def wrap_strictly(text, max_chars=38):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if not curr:
            curr.append(w)
            curr_len = len(w)
        elif curr_len + 1 + len(w) <= max_chars:
            curr.append(w)
            curr_len += 1 + len(w)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

spec_items = {
    "aid1": "Bottom-up: physical, link, network, transport, application; when many things fail at once or after a hardware change; physical problems are cheapest to rule out (a loose cable or dead optic shows in a light or counter)",
    "aid2": "Top-down: when only one application misbehaves",
    "aid3": "Divide and conquer (half-split): when the path is long",
    "aid4": "Follow the path: trace the actual flow end to end, including NAT, overlays and load balancers",
    "aid5": "Compare with a working peer: diff a good node against a bad one; check configs, firmware, ethtool, sysctls, routes and counters; configuration drift is the most common root cause in fleets",
    "aid6": "Change one thing at a time, and revert the experiments that fail",
    "aid7": "Use the packet: a capture beats opinion",
    "side": "Two engineers, same alert: one changes settings at once and the evidence is gone by the time the cause would have shown; the other writes down the symptom, saves the counters, and only then changes one thing"
}

for k, txt in spec_items.items():
    lines = wrap_strictly(txt, 38)
    print(f"[{k}] ({len(lines)} lines):")
    for l in lines:
        w = len(l) * 0.6 * 24
        print(f"  '{l}' (chars: {len(l)}, w: {w:.1f}px)")
