import re

labels = {
    "title": "Top-level code runs in order, a def body runs only when called",
    "step1": "1 func1()  would raise NameError: func1 not yet assigned",
    "step2": "2 def func1(): print(func2())  binds the name func1; the body does not run",
    "step3": "3 func1() here raises NameError: func2 not yet assigned when func1 runs",
    "step4": '4 def func2(): return "Hello"',
    "step5": "5 func1() works: both names assigned, prints Hello",
    "side_hdr": "names assigned so far",
    "side_r1": "none",
    "side_r23": "func1",
    "side_r45": "func1, func2",
    "rule": "when Python first imports or reloads a module it runs top-level statements from top to bottom, so top-level code cannot use names assigned lower down; a def body can refer to a name defined later as long as it exists by the time of the call",
    "strip": 'Keep import-time work small: no network calls, config file reads, thread starts or heavy imports at the top of a module; in command-line tools move a heavy import into the function that needs it; measure with python -X importtime; module with print("util loaded") shows side effects at import time: avoid in libraries',
    "bottom": "The name must exist by the time of the call, not by the time of the def"
}

# Check conservative widths
# Rule: sans 0.6 * font_size, monospace 0.62 * font_size
for k, v in labels.items():
    print(f"{k}: len={len(v)}, sans24={len(v)*0.6*24:.1f}px, sans30={len(v)*0.6*30:.1f}px")

