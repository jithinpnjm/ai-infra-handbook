def wrap_text(text, max_len):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_len:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

mech = "token bucket: a jar that starts full, is spent per request, refills slowly, and allows bursts up to bucket size; charge prompt tokens plus max output tokens at admission, refund the unused at the end; reject at once what can never fit; a refused request must not burn a request slot; distributed choice: shared store such as Redis is exact but adds a hop and a dependency, local buckets are fast and slightly loose"
lines = wrap_text(mech, 75)
print(f"Mechanism strip lines ({len(lines)} lines):")
for i, l in enumerate(lines):
    print(f"  {i+1} ({len(l)} chars, {len(l)*14.4:.1f}px): '{l}'")

incident = "ten requests with 8,000 prompt tokens and a large max output made every other tenant TTFT double while a requests-per-minute limit saw nothing wrong"
inc_lines = wrap_text(incident, 75)
print(f"\nIncident lines ({len(inc_lines)} lines):")
for i, l in enumerate(inc_lines):
    print(f"  {i+1} ({len(l)} chars, {len(l)*14.4:.1f}px): '{l}'")
