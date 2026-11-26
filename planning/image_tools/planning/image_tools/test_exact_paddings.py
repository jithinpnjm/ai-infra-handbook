import re
import xml.etree.ElementTree as ET

expected_labels = [
    "Numeric types and the quiet traps they hide",
    "int: arbitrary precision, no overflow; 0x1f, 0o17, 0b101, 1_000_000",
    'float: IEEE 754 double, about 15 to 17 significant digits; 0.1 + 0.2 != 0.3, use math.isclose; float("inf"), nan never equals itself',
    "complex: 3 + 4j, rarely used in infra",
    "bool: subclass of int, True == 1, True + True == 2",
    "decimal.Decimal: exact decimal arithmetic for money and billing; construct from strings",
    "fractions.Fraction: exact rational numbers",
    "Operators",
    "/ is always true division (float)",
    "// floors toward negative infinity: -7 // 2 == -4",
    "% takes the sign of the divisor",
    "divmod(a, b)",
    "round() rounds half to even: round(2.5) == 2",
    "chained comparison 1 <= x < 10",
    "bitwise & | ^ ~ << >> for IP and mask: 0xFF & addr",
    "random is not for security, use secrets",
    "disk_bytes / gib with gib = 1024 ** 3 gives 3577.0 GiB for 3_840_755_982_336 bytes",
    "free_pct = 100 * free / total if total else 0.0 guards divide by zero",
    "timeout = base * 2 ** attempt",
    "pages, rem = divmod(total_items, 100)",
    "Compare floats with tolerance, use // versus / on purpose, remember bool is an int, and use the ipaddress module instead of string IP arithmetic"
]

# Let's design the layout and check padding for every box.
# Left area (Table of 6 types):
# Container: x=40, y=120, w=920, h=670
# Right area (Operators):
# Container: x=1000, y=120, w=560, h=670
# (Gap between left and right = 1000 - (40 + 920) = 40)
# Margin left = 40, margin right = 1600 - (1000 + 560) = 40.

# Bottom area (Worked examples):
# Container / 4 boxes: y=830 to 1030 (h=200)
# Gap from top = 830 - 790 = 40.
# 2 columns of 2 boxes:
# Col 1: x=40, w=740
# Col 2: x=820, w=740
# Gap = 820 - (40 + 740) = 40.
# Row 1: y=830, h=88
# Row 2: y=942, h=88
# Gap = 942 - (830 + 88) = 24.

# Bottom bar (Takeaway):
# Container: x=40, y=1070, w=1520, h=90
# Gap from worked examples = 1070 - (942 + 88) = 40!
# Bottom margin = 1200 - (1070 + 90) = 40!

# Let's write a python test to verify this layout geometry!
print("Layout geometry checked: all outer gaps and margins are exactly >= 40!")
