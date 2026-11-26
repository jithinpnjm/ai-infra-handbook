# Layout planning
# Let's check text length of 'Common wrong approach':
cwa_text = "cut -d space -f1 access.log | uniq -c | sort -rn | head -3 skips the first sort, so uniq counted only neighbouring lines and printed 3 203.0.113.77 twice"
print("Common wrong approach total chars:", len(cwa_text))

step6_text = "Cross-check: count the same thing with an awk array and compare"
print("Step 6 total chars:", len(step6_text))

takeaway_text = "Never report a number you have produced only one way."
print("Takeaway total chars:", len(takeaway_text))
print("Takeaway width at 28px sans:", len(takeaway_text) * 0.6 * 28)
