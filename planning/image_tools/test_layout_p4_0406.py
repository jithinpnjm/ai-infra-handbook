import re

def calc_width(text, fs=26, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * fs * factor

labels = {
    "title": "Scheduled --check runs catch hand-made changes before anyone is surprised",
    "event": "last week: someone logs in to a node and changes a setting by hand; nothing in the playbook knows about it",
    "branch_a": "no scheduled check: the next normal run quietly reverts the change",
    "branch_b": "scheduled --check run: exits non-zero or reports changed>0, revealing the manual change before anyone is surprised",
    "parse": "for drift detection parse the recap and look at changed= counts, or use ANSIBLE_STDOUT_CALLBACK=json or ansible.posix.json for machine-readable output; in CI treat any non-zero exit as a failure",
    "evidence": "use the --check --diff output as evidence in pull requests (4.2)",
    "bottom": "A dry run notices the difference first"
}

print("=== CHECKING LINE WRAPS ===")
# Event: in box x=40, width=1520. Icon x=70 (w=56). Text x=150. Max x=1520. Usable width = 1370.
line1 = "last week: someone logs in to a node and changes a setting by hand;"
line2 = "nothing in the playbook knows about it"
w1 = calc_width(line1, 28)
w2 = calc_width(line2, 28)
print(f"Event L1 ({len(line1)} chars): {w1:.1f} px (limit 1330)")
print(f"Event L2 ({len(line2)} chars): {w2:.1f} px (limit 1330)")

# Branch A: in box x=40, width=740. Icon x=70 (w=56). Text x=150. Usable width = 740 - (150-40) - 20 = 610.
# Let's test 2 lines vs 3 lines
ba_l1 = "no scheduled check:"
ba_l2 = "the next normal run"
ba_l3 = "quietly reverts the change"
print(f"Branch A L1: {calc_width(ba_l1, 26):.1f} px")
print(f"Branch A L2: {calc_width(ba_l2, 26):.1f} px")
print(f"Branch A L3: {calc_width(ba_l3, 26):.1f} px (limit 590)")

# Branch B: in box x=820, width=740. Icon x=850 (w=56). Text x=930. Usable width = 740 - (930-820) - 20 = 610.
bb_l1 = "scheduled --check run:"
bb_l2 = "exits non-zero or reports changed>0,"
bb_l3 = "revealing the manual change"
bb_l4 = "before anyone is surprised"
print(f"Branch B L1: {calc_width(bb_l1, 26):.1f} px")
print(f"Branch B L2: {calc_width(bb_l2, 26):.1f} px")
print(f"Branch B L3: {calc_width(bb_l3, 26):.1f} px")
print(f"Branch B L4: {calc_width(bb_l4, 26):.1f} px (limit 590)")

# Parse strip: box x=40, width=1520. Icon x=70. Text x=150. Usable = 1370.
p_l1 = "for drift detection parse the recap and look at changed= counts, or use"
p_l2 = "ANSIBLE_STDOUT_CALLBACK=json or ansible.posix.json for machine-readable output;"
p_l3 = "in CI treat any non-zero exit as a failure"
print(f"Parse L1: {calc_width(p_l1, 25):.1f} px")
print(f"Parse L2: {calc_width(p_l2, 25, is_mono=True):.1f} px (limit 1330)")
print(f"Parse L3: {calc_width(p_l3, 25):.1f} px")

# Evidence strip: box x=40, width=1520. Icon x=70. Text x=150. Usable = 1370.
ev_l1 = "use the --check --diff output as evidence in pull requests (4.2)"
print(f"Evidence L1: {calc_width(ev_l1, 26):.1f} px (limit 1330)")

# Bottom bar: box x=40, width=1520, height=70. Text centered at x=800.
bot_l1 = "A dry run notices the difference first"
print(f"Bottom L1: {calc_width(bot_l1, 30):.1f} px (limit 1480)")
