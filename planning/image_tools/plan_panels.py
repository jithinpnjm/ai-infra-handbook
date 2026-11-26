import re

# Panel 1:
# Title: 'Leave several loops'
# Code: 'class Exitloop(Exception): pass; try: while True: while True: for i in range(10): if i > 3: raise Exitloop; print(loop3: i) ... except Exitloop: print(continuing)'
# Output: 'loop3: 0, loop3: 1, loop3: 2, loop3: 3, continuing, i=4'
# Note: 'break exits only one level, with break here you get an infinite loop; i keeps its value because assignments in a try are not undone; the raise works like a goto where the except clause is the label, and you can jump only out of code wrapped in a try'

p1_title = "Leave several loops"
p1_code = "class Exitloop(Exception): pass; try: while True: while True: for i in range(10): if i > 3: raise Exitloop; print(loop3: i) ... except Exitloop: print(continuing)"
p1_output = "loop3: 0, loop3: 1, loop3: 2, loop3: 3, continuing, i=4"
p1_note = "break exits only one level, with break here you get an infinite loop; i keeps its value because assignments in a try are not undone; the raise works like a goto where the except clause is the label, and you can jump only out of code wrapped in a try"

# Panel 2:
# Title: 'End of input is a signal'
# Code: 'while True: try: line = input() except EOFError: break else: process the line'
# Note: 'file read methods return an empty string at end of file, input raises EOFError; an empty string from input is a blank line, not the end'
# Other: 'other signal exceptions: sys.exit() raises SystemExit, Ctrl+C raises KeyboardInterrupt'

p2_title = "End of input is a signal"
p2_code = "while True: try: line = input() except EOFError: break else: process the line"
p2_note = "file read methods return an empty string at end of file, input raises EOFError; an empty string from input is a blank line, not the end"
p2_other = "other signal exceptions: sys.exit() raises SystemExit, Ctrl+C raises KeyboardInterrupt"

# Panel 3:
# Title: 'Signal a result'
# Opt1: 'class Found(Exception); searcher raises Found() on success; caller: try searcher() except Found: success else: failure'
# Opt2: 'class Failure(Exception); searcher returns founditem or raises Failure(); caller: try: item = searcher() except Failure: not found else: use item'
# Reason: 'if every object can be a valid return value, no sentinel such as None is safe; an exception carries the failure without touching the return value'

p3_title = "Signal a result"
p3_opt1 = "class Found(Exception); searcher raises Found() on success; caller: try searcher() except Found: success else: failure"
p3_opt2 = "class Failure(Exception); searcher returns founditem or raises Failure(); caller: try: item = searcher() except Failure: not found else: use item"
p3_reason = "if every object can be a valid return value, no sentinel such as None is safe; an exception carries the failure without touching the return value"

def split_and_verify(name, text, max_c, font_type='sans', fs=24, box_w=440, pad_left=20):
    char_w = 0.62 * fs if font_type == 'mono' else 0.60 * fs
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if not cur:
            cur.append(w)
            cur_len = len(w)
        elif cur_len + 1 + len(w) <= max_c:
            cur.append(w)
            cur_len += 1 + len(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    
    # check
    assert " ".join(lines) == text, f"Mismatch in {name}!"
    print(f"\n[{name}] {len(lines)} lines (max_c={max_c}, font={font_type}):")
    for i, l in enumerate(lines):
        tw = len(l) * char_w
        pad_right = box_w - (pad_left + tw)
        print(f"  {i+1}: '{l}' ({len(l)}c, {tw:.1f}px, rpad={pad_right:.1f}px)")
        assert pad_right >= 16, f"Right padding {pad_right:.1f} < 16px!"
    return lines

p1_c_lines = split_and_verify("p1_code", p1_code, 26, 'mono')
p1_o_lines = split_and_verify("p1_output", p1_output, 26, 'mono')
p1_n_lines = split_and_verify("p1_note", p1_note, 27, 'sans')

p2_c_lines = split_and_verify("p2_code", p2_code, 26, 'mono')
p2_n_lines = split_and_verify("p2_note", p2_note, 27, 'sans')
p2_o_lines = split_and_verify("p2_other", p2_other, 26, 'sans')

p3_1_lines = split_and_verify("p3_opt1", p3_opt1, 26, 'mono')
p3_2_lines = split_and_verify("p3_opt2", p3_opt2, 26, 'mono')
p3_r_lines = split_and_verify("p3_reason", p3_reason, 27, 'sans')
