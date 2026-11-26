# Let's list the 27 distinct text elements:

distinct_elements = [
    # 1. Title
    "The canary ladder moves traffic up in steps, and each step must pass its gates",
    # 2. Gate 1 title
    "Latency gates",
    # 3. Gate 1 text
    "canary TTFT p99 and ITL p99 against baseline, ratio limit",
    # 4. Gate 2 title
    "Quality gates",
    # 5. Gate 2 text
    "eval score, finish_reason length share, error rate",
    # 6-11. Step numbers
    "1", "2", "3", "4", "5", "6",
    # 12-17. Step titles
    "Shadow traffic",
    "1 percent",
    "5 percent",
    "25 percent",
    "50 percent",
    "100 percent",
    # 18. Gate diamond label (appears on each of the 5 diamonds)
    "gates pass",
    # 19. Outcome 1 title
    "Promote",
    # 20. Outcome 1 text
    "all gates passed, enough traffic",
    # 21. Outcome 2 title
    "Hold",
    # 22. Outcome 2 text
    "marginal results or too few requests",
    # 23. Outcome 3 title
    "Rollback",
    # 24. Outcome 3 text
    "hard failure such as quality drop or zero tokens",
    # 25. Arrow 1 label
    "hard failure",
    # 26. Arrow 2 label
    "wait for more evidence",
    # 27. Takeaway bar
    "Promote only on a clean pass with enough traffic, hold on thin data, roll back on a hard signal."
]

print(f"Total distinct text elements: {len(distinct_elements)}")
assert len(distinct_elements) == 27
assert len(set(distinct_elements)) == 27
print("All 27 elements are 100% distinct!")
