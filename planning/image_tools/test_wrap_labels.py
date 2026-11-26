import re

labels = {
    "title": "Exceptions as control flow: leave nested loops, signal end of input, signal a result",
    "p1_title": "Leave several loops",
    "p1_code": "class Exitloop(Exception): pass; try: while True: while True: for i in range(10): if i > 3: raise Exitloop; print(loop3: i) ... except Exitloop: print(continuing)",
    "p1_output": "loop3: 0, loop3: 1, loop3: 2, loop3: 3, continuing, i=4",
    "p1_note": "break exits only one level, with break here you get an infinite loop; i keeps its value because assignments in a try are not undone; the raise works like a goto where the except clause is the label, and you can jump only out of code wrapped in a try",
    "p2_title": "End of input is a signal",
    "p2_code": "while True: try: line = input() except EOFError: break else: process the line",
    "p2_note": "file read methods return an empty string at end of file, input raises EOFError; an empty string from input is a blank line, not the end",
    "p2_other": "other signal exceptions: sys.exit() raises SystemExit, Ctrl+C raises KeyboardInterrupt",
    "p3_title": "Signal a result",
    "p3_opt1": "class Found(Exception); searcher raises Found() on success; caller: try searcher() except Found: success else: failure",
    "p3_opt2": "class Failure(Exception); searcher returns founditem or raises Failure(); caller: try: item = searcher() except Failure: not found else: use item",
    "p3_reason": "if every object can be a valid return value, no sentinel such as None is safe; an exception carries the failure without touching the return value",
    "bottom": "In Python every error is an exception, but not every exception is an error"
}

def wrap_text(text, max_chars):
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if not cur:
            cur.append(w)
            cur_len = len(w)
        elif cur_len + 1 + len(w) <= max_chars:
            cur.append(w)
            cur_len += 1 + len(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

for k, v in labels.items():
    if "code" in k or "opt" in k:
        max_c = 26
    else:
        max_c = 27
    lines = wrap_text(v, max_c)
    print(f"{k} ({len(lines)} lines, max={max(len(l) for l in lines)}):")
    for l in lines:
        print(f"  '{l}'")
