title_lines = [
    ("A global ratio hides one tenant,", 48, True),
    ("and per-tenant detail has a series cost", 48, True)
]

# Card 1:
# "100 tenants with equal traffic; one tenant has 100 percent errors; global error ratio = 1 percent; against a 99.9 percent target burn rate = 0.01 / 0.001 = 10"
card1_lines = [
    ("100 tenants with", 30, True),
    ("equal traffic;", 30, True),
    ("one tenant has 100", 24, False),
    ("percent errors; global", 24, False),
    ("error ratio = 1 percent;", 24, False),
    ("against a 99.9 percent", 24, False),
    ("target burn rate =", 24, False),
    ("0.01 / 0.001 = 10", 24, False),
]

# Card 2:
# "Burn 10 pages through the 6-hour rule (threshold 6) but not through the fast 14.4 rule, while that customer is fully down"
card2_lines = [
    ("Burn 10 pages through", 30, True),
    ("the 6-hour rule", 30, True),
    ("(threshold 6) but not", 24, False),
    ("through the fast 14.4 rule,", 24, False),
    ("while that customer is", 24, False),
    ("fully down", 24, False),
]

# Card 3:
# "TTFT histogram with 22 buckets plus a count series is about 23 series per tenant and model pair; 1,000 tenants x 20 models x 23 = 460,000 series for one metric"
card3_lines = [
    ("TTFT histogram with", 30, True),
    ("22 buckets plus a count", 30, True),
    ("series is about 23 series per", 24, False),
    ("tenant and model pair; 1,000", 24, False),
    ("tenants x 20 models x 23 =", 24, False),
    ("460,000 series for one metric", 24, False),
]

# Card 4:
# "page on per-model ratios, ticket on per-tenant ratios, guard low-traffic series"
card4_lines = [
    ("page on per-model", 30, True),
    ("ratios,", 30, True),
    ("ticket on per-tenant ratios,", 24, False),
    ("guard low-traffic series", 24, False),
]

# Card 5:
# "tenant with 3 requests per minute (0.05 requests per second) and every one failing has a 100 percent ratio but the rule needs more than 0.1 requests per second over three days, so it does not fire; tenant a at 100 requests per second and 0.2 percent errors fires, tenant b stays silent; a dedicated contract tenant can get an absolute count of failures in an hour instead"
card5_lines = [
    ("tenant with 3 requests", 30, True),
    ("per minute", 30, True),
    ("(0.05 requests per second)", 24, False),
    ("and every one failing has", 24, False),
    ("a 100 percent ratio but the", 24, False),
    ("rule needs more than 0.1", 24, False),
    ("requests per second over", 24, False),
    ("three days, so it does not", 24, False),
    ("fire; tenant a at 100", 24, False),
    ("requests per second and", 24, False),
    ("0.2 percent errors fires,", 24, False),
    ("tenant b stays silent;", 24, False),
    ("a dedicated contract", 24, False),
    ("tenant can get an absolute", 24, False),
    ("count of failures in an", 24, False),
    ("hour instead", 24, False),
]

cards = [
    ("Title", title_lines, 1600),
    ("Card 1", card1_lines, 480),
    ("Card 2", card2_lines, 480),
    ("Card 3", card3_lines, 480),
    ("Card 4", card4_lines, 480),
    ("Card 5", card5_lines, 480),
]

for name, lines, box_w in cards:
    print(f"=== {name} (box width {box_w}) ===")
    full = " ".join(t for t, fs, b in lines)
    print("Full text length:", len(full))
    for t, fs, b in lines:
        w = len(t) * fs * 0.6
        pad = (box_w - w) / 2
        print(f"  [{fs}px {'B' if b else ' '} | len={len(t):2d} | w={w:5.1f}px | pad={pad:5.1f}px] {t}")
