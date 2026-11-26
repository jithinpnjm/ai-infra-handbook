import textwrap

def wrap_text(text, max_chars):
    lines = []
    # Try greedy wrapping on spaces, semicolons, etc.
    # Preserve words
    words = text.split(' ')
    cur_line = []
    cur_len = 0
    for w in words:
        if cur_line and cur_len + 1 + len(w) > max_chars:
            lines.append(" ".join(cur_line))
            cur_line = [w]
            cur_len = len(w)
        else:
            cur_line.append(w)
            cur_len += (1 if cur_len > 0 else 0) + len(w)
    if cur_line:
        lines.append(" ".join(cur_line))
    return lines

labels = {
    "title": "A global ratio hides one tenant, and per-tenant detail has a series cost",
    "left1": "100 tenants with equal traffic; one tenant has 100 percent errors; global error ratio = 1 percent; against a 99.9 percent target burn rate = 0.01 / 0.001 = 10",
    "left2": "Burn 10 pages through the 6-hour rule (threshold 6) but not through the fast 14.4 rule, while that customer is fully down",
    "middle": "TTFT histogram with 22 buckets plus a count series is about 23 series per tenant and model pair; 1,000 tenants x 20 models x 23 = 460,000 series for one metric",
    "right1": "page on per-model ratios, ticket on per-tenant ratios, guard low-traffic series",
    "right2": "tenant with 3 requests per minute (0.05 requests per second) and every one failing has a 100 percent ratio but the rule needs more than 0.1 requests per second over three days, so it does not fire; tenant a at 100 requests per second and 0.2 percent errors fires, tenant b stays silent; a dedicated contract tenant can get an absolute count of failures in an hour instead"
}

# Max width inside a 480px box:
# box width = 480
# padding = 24 each side -> max text width = 432px
# At 24px sans-serif (0.6 * 24 = 14.4px per char): 432 / 14.4 = 30 chars
# At 26px: 432 / 15.6 = 27.6 chars

for k, text in labels.items():
    if k == "title": continue
    print(f"=== {k} ===")
    lines = wrap_text(text, 28)
    for i, line in enumerate(lines):
        w = len(line) * 24 * 0.6
        print(f"  [{len(line):2d} ch, {w:5.1f}px] {line}")
    print(f"Total lines: {len(lines)}")
