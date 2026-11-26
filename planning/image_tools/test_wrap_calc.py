def check_line(text, w_box, fs, is_mono):
    factor = 0.62 if is_mono else 0.60
    w_text = len(text) * fs * factor
    pad = (w_box - w_text) / 2.0
    return w_text, pad

w_col1 = 440
w_col2 = 660
w_col3 = 380

print("--- Col 1 ---")
for t, is_m, lines in [
    ("msg: Disk full: retry", True, ["msg: Disk full: retry"]),
    ("path: /data #1", True, ["path: /data #1"]),
    ("mode: 0644", True, ["mode: 0644"]),
    ("value starts with * & ! % @ backtick { [ | >", True, ["value starts with", "* & ! % @ backtick { [ | >"]),
    ("msg: {{ var }}", True, ["msg: {{ var }}"]),
]:
    for l in lines:
        wt, pad = check_line(l, w_col1, 24, is_m)
        print(f"'{l}': text_w={wt:.1f}, pad={pad:.1f} (ok={pad >= 16})")

print("\n--- Col 2 ---")
for t, is_m, lines in [
    ("a second colon followed by a space: it can no longer tell where the key ends", False, [
        "a second colon followed by a space:",
        "it can no longer tell where the key ends"
    ]),
    ("a hash after a space starts a comment, so only /data is stored and no error appears", False, [
        "a hash after a space starts a comment,",
        "so only /data is stored and no error appears"
    ]),
    ("octal number in YAML 1.1", False, ["octal number in YAML 1.1"]),
    ("special syntax", False, ["special syntax"]),
    ("opening brace starts a flow mapping", False, ["opening brace starts a flow mapping"])
]:
    for l in lines:
        wt, pad = check_line(l, w_col2, 24, is_m)
        print(f"'{l}': text_w={wt:.1f}, pad={pad:.1f} (ok={pad >= 16})")

print("\n--- Col 3 ---")
for t, is_m, lines in [
    ('msg: "Disk full: retry"', True, ['msg: "Disk full: retry"']),
    ("quote the value", False, ["quote the value"]),
    ('mode: "0644"', True, ['mode: "0644"']),
    ("quote it", False, ["quote it"]),
    ('msg: "{{ var }}"', True, ['msg: "{{ var }}"'])
]:
    for l in lines:
        wt, pad = check_line(l, w_col3, 24, is_m)
        print(f"'{l}': text_w={wt:.1f}, pad={pad:.1f} (ok={pad >= 16})")

