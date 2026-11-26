import re

def check_line(text, fs, baseline_y, anchor_x, box, is_mono=False):
    box_x, box_y, box_w, box_h = box
    factor = 0.62 if is_mono else 0.6
    line_w = len(text) * fs * factor
    t_left = anchor_x
    t_right = anchor_x + line_w
    
    pad_l = t_left - box_x
    pad_r = (box_x + box_w) - t_right
    pad_t = (baseline_y - fs) - box_y
    pad_b = (box_y + box_h) - baseline_y
    
    min_pad = min(pad_l, pad_r, pad_t, pad_b)
    status = "PASS" if min_pad >= 16 else "FAIL"
    print(f"[{status}] '{text[:35]}...' (fs={fs}) pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
    assert min_pad >= 16, f"Padding violation on '{text}': min_pad={min_pad:.1f}"

# Let's test all lines!
print("=== BLOCK 1 INNER 1 ===")
b1_box = (128, 145, 632, 94)
check_line("X = 99; [X for X in range(5)] gives ", 24, 186, 146, b1_box, True)
check_line("[0, 1, 2, 3, 4]; outer X is still 99", 24, 220, 146, b1_box, True)

print("\n=== BLOCK 1 INNER 2 ===")
b2_box = (128, 247, 632, 94)
check_line("for X in range(5): pass ", 24, 288, 146, b2_box, True)
check_line("changes outer X to 4", 24, 322, 146, b2_box, True)

print("\n=== BLOCK 2 INNER ===")
b2_inner = (908, 137, 632, 206)
check_line("S = 'hack'; ", 24, 178, 930, b2_inner, True)
check_line("[(temp := S[i]) + temp.upper() ", 24, 208, 930, b2_inner, True)
check_line("for i in range(len(S))] gives ", 24, 238, 930, b2_inner, True)
check_line("['hH', 'aA', 'cC', 'kK']; temp is 'k' ", 24, 268, 930, b2_inner, True)
check_line("in the enclosing scope, i raises ", 24, 298, 930, b2_inner, True)
check_line("NameError: name i is not defined", 24, 327, 930, b2_inner, True)

print("\n=== RULES STRIP ===")
rules_box = (40, 390, 1520, 84)
check_line("a for variable in a list, set, dict or generator comprehension lives in the comprehension's own ", 24, 430, 140, rules_box, False)
check_line("scope; := binds its target in the enclosing scope; a yield inside a comprehension is forbidden", 24, 458, 140, rules_box, False)

print("\n=== PLACEMENT STRIP ===")
place_box = (40, 514, 1520, 116)
check_line("a filter if sits after the for; a conditional expression that picks a value sits before it: ", 24, 555, 140, place_box, False)
check_line('["even" if n % 2 == 0 else "odd" for n in range(5)]; nested for clauses read left to right like ', 24, 586, 140, place_box, False)
check_line("nested for statements", 24, 614, 140, place_box, False)

print("\n=== WALRUS USE ===")
walrus_box = (40, 670, 740, 118)
check_line("[y for x in data if ", 24, 710, 145, walrus_box, True)
check_line("(y := expensive(x)) is not None] ", 24, 740, 145, walrus_box, True)
check_line("calls expensive once per item", 24, 770, 145, walrus_box, True)

print("\n=== MATRIX EXAMPLES ===")
mat_box = (40, 828, 740, 228)
check_line("M = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]: ", 24, 868, 145, mat_box, True)
check_line("column [row[1] for row in M] is ", 24, 896, 145, mat_box, True)
check_line("[2, 5, 8]; diagonal [M[i][i] ...] is ", 24, 924, 145, mat_box, True)
check_line("[1, 5, 9]; anti-diagonal is [3, 5, 7]; ", 24, 952, 145, mat_box, True)
check_line("[col + 10 for row in M for col in row] ", 24, 980, 145, mat_box, True)
check_line("is flat while [[col + 10 for col in row] ", 24, 1008, 145, mat_box, True)
check_line("for row in M] keeps rows", 24, 1036, 145, mat_box, True)

print("\n=== RULES OF THUMB ===")
rot_box = (820, 670, 740, 386)
check_line("more than two for or if clauses, or side ", 24, 792, 855, rot_box, False)
check_line("effects: use a loop; never [print(x) for x ", 24, 824, 855, rot_box, False)
check_line("in xs]; you cannot catch exceptions inside a ", 24, 856, 855, rot_box, False)
check_line("comprehension, wrap risky code in a function; ", 24, 888, 855, rot_box, False)
check_line("use [[0]*c for _ in range(r)]; generator ", 24, 920, 855, rot_box, False)
check_line("expressions for sum, any, all, max, sorted, ", 24, 952, 855, rot_box, False)
check_line("join, set, tuple; comprehensions are usually ", 24, 984, 855, rot_box, False)
check_line("20 to 50% faster than the equivalent loops", 24, 1016, 855, rot_box, False)

print("\n=== BOTTOM BAR ===")
bot_box = (40, 1096, 1520, 64)
w_bot = len("If a comprehension needs a second look to understand, split it into a loop") * 24 * 0.6
left_bot = 800 - w_bot / 2
check_line("If a comprehension needs a second look to understand, split it into a loop", 24, 1138, left_bot, bot_box, False)

print("\nALL LINES PASSED STRICT PADDING CHECKS (>= 16px)!")
