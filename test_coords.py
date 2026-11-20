# Let's verify vertical coordinates of each section
def verify_section(name, y_top, y_bot, code_lines, bracket, expl_items):
    print(f"=== {name} ({y_top} -> {y_bot}, h={y_bot - y_top}) ===")
    for text, y in code_lines:
        print(f"  Code: '{text}' at y={y} (inside {y_top}..{y_bot})")
        assert y_top < y < y_bot
    for item, y in expl_items:
        print(f"  Expl: '{item}' at y={y} (inside {y_top}..{y_bot})")
        assert y_top < y < y_bot

# Section 1
verify_section("ARP", 210, 400, [
    ("arp who-has...", 280),
    ("arp reply...", 340)
], None, [("hosts...", 325)])

# Section 2
verify_section("Handshake", 425, 665, [
    ("S", 495),
    ("S ... ack...", 555),
    (". ack 1", 615)
], None, [("TCP handshake", 565)])

# Section 3
verify_section("Data", 690, 930, [
    ("P 1:427(426)", 750),
    (". ack", 810),
    ("P 1:773(772)", 870)
], None, [("request", 760), ("response", 870)])

# Section 4
verify_section("Summary", 955, 1145, [
    ("9 packets...", 1015),
    ("0 packets...", 1075)
], None, [("summary", 1055)])

print("\nAll coordinates aligned and well within section boundaries!")
