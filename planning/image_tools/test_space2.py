fix_bottom = 624
checks_top = fix_bottom + 40 # 664
bar_bottom = 1150 # <= 1160
bar_top = bar_bottom - 56 # 1094
gap_rules_bar = 40
rules_bottom = bar_top - gap_rules_bar # 1054
rules_top = rules_bottom - 148 # 906
gap_checks_rules = 40
checks_bottom = rules_top - gap_checks_rules # 866
checks_height = checks_bottom - checks_top # 866 - 664 = 202px!

print(f"Checks strip can be {checks_height}px high!")
