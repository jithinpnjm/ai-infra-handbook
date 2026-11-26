def test_alert(lines, box_w, fs_dict):
    char_w_default = 24 * 0.6
    all_ok = True
    for l in lines:
        t = l.strip()
        fs = fs_dict.get(t, 24)
        cw = fs * 0.6
        tw = len(t) * cw
        pad = (box_w - tw) / 2
        ok = pad >= 16
        if not ok: all_ok = False
        print(f"  [{'OK' if ok else 'FAIL'}] fs={fs} tw={tw:5.1f} pad={pad:4.1f}: '{t}'")
    return all_ok

fs_map = {"Page |": 30, "Ticket |": 30}

print("Alert 1:")
a1 = ["Page | ", "1 h long, 5 min short | ", "burn 14.4 | ", "threshold 0.0144 | ", "2 percent of budget | ", "50 hours to empty"]
test_alert(a1, 486, fs_map)

print("\nAlert 2:")
a2 = ["Page | ", "6 h long, 30 min short | ", "burn 6 | ", "0.006 | ", "5 percent | ", "120 hours"]
test_alert(a2, 486, fs_map)

print("\nAlert 3:")
a3 = ["Ticket | ", "3 days long, 6 h short | ", "burn 1 | ", "0.001 | ", "10 percent | ", "720 hours"]
test_alert(a3, 486, fs_map)

