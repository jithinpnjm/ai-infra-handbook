# Check 1: h=80
# Gap: 40
# Check 2: h=60
# Gap: 40
# Check 3: h=60
# Gap: 40
# Check 4: h=60
# Gap: 40
# Check 5: h=60
# Gap: 40
# Check 6: h=60

check_hs = [80, 60, 60, 60, 60, 60]
total_h = sum(check_hs) + 5 * 40
print("Total checks span:", total_h)
assert total_h == 580
