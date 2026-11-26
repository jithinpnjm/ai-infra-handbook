# Check heights:
# Check 1: 2 lines -> height 76
# Check 2: 1 line  -> height 56
# Check 3: 1 line  -> height 56
# Check 4: 1 line  -> height 56
# Check 5: 1 line  -> height 56
# Check 6: 1 line  -> height 56

h_checks = [76, 56, 56, 56, 56, 56]
print("Sum of check heights:", sum(h_checks))
# 5 gaps between them:
# 570 - 356 = 214px available for 5 gaps!
# 214 / 5 = 42.8px per gap!
print("Average gap:", 214 / 5)
