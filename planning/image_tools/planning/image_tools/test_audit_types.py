#!/usr/bin/env python3
import glob, re

files = glob.glob("*.py")
has_step_numbers = []
strict_len_equals = []

for f in files:
    content = open(f).read()
    if "step_numbers" in content:
        has_step_numbers.append(f)
    if "assert len(found" in content or "assert len(all_found" in content:
        strict_len_equals.append(f)

print(f"Files with step_numbers ({len(has_step_numbers)}):")
for f in sorted(has_step_numbers)[:10]:
    print(" ", f)

print(f"\nFiles with strict len equality ({len(strict_len_equals)}):")
for f in sorted(strict_len_equals)[:10]:
    print(" ", f)
