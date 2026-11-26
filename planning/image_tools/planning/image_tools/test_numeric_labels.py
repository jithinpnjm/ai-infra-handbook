import re

spec_labels = [
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

print(f"Total spec labels: {len(spec_labels)}")
for i, l in enumerate(spec_labels, 1):
    print(f"{i:2d}. {l}")
