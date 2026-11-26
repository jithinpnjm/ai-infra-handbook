import re

labels = {
    "title": "A global ratio hides one tenant, and per-tenant detail has a series cost",
    "left1": "100 tenants with equal traffic; one tenant has 100 percent errors; global error ratio = 1 percent; against a 99.9 percent target burn rate = 0.01 / 0.001 = 10",
    "left2": "Burn 10 pages through the 6-hour rule (threshold 6) but not through the fast 14.4 rule, while that customer is fully down",
    "middle": "TTFT histogram with 22 buckets plus a count series is about 23 series per tenant and model pair; 1,000 tenants x 20 models x 23 = 460,000 series for one metric",
    "right1": "page on per-model ratios, ticket on per-tenant ratios, guard low-traffic series",
    "right2": "tenant with 3 requests per minute (0.05 requests per second) and every one failing has a 100 percent ratio but the rule needs more than 0.1 requests per second over three days, so it does not fire; tenant a at 100 requests per second and 0.2 percent errors fires, tenant b stays silent; a dedicated contract tenant can get an absolute count of failures in an hour instead"
}

for k, v in labels.items():
    print(f"{k}: len={len(v)}")
