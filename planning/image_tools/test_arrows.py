# Compute exact positions for rows and checks

card_y = 278
card_h = 570
pad_top = 18

row_defs = [
    ("Row 1", 38, "Subject: who it is for"),
    ("Row 2", 38, "Issuer: the CA that signed it"),
    ("Row 3", 60, "Validity: notBefore and notAfter, checked against the client's own clock"),
    ("Row 4", 36, "Public key"),
    ("Row 5", 96, "Subject Alternative Names (SAN): the DNS names or IPs the certificate is valid for; browsers and modern libraries ignore the old CN field"),
    ("Row 6", 58, "Key usage and extended key usage: serverAuth, clientAuth"),
    ("Row 7", 38, "Basic constraints: whether this is a CA"),
    ("Row 8", 38, "Authority and subject key identifiers"),
    ("Row 9", 38, "CRL and OCSP URLs"),
    ("Row 10", 38, "Issuer's signature"),
]

row_gap = 7
curr_y = card_y + pad_top
row_positions = []
for name, h, text in row_defs:
    row_positions.append((name, curr_y, h, curr_y + h/2, text))
    curr_y += h + row_gap

print("Card bottom padding:", (card_y + card_h) - (curr_y - row_gap))
for r in row_positions:
    print(f"{r[0]:6s} | y={r[1]:.1f} | h={r[2]:.1f} | center={r[3]:.1f} | {r[4][:30]}")

print("\n--- Check Positions ---")
# 6 checks in right column
# Gaps must be >= 40px
# Let's see:
# Check 1: h=76
# Check 2: h=56
# Check 3: h=56
# Check 4: h=56
# Check 5: h=56
# Check 6: h=56

# Let's align each check close to its row center:
# Row 2 center: ~353 -> Check 1 (h=76) center ~ 335 (y: 297 to 373)
# Row 3 center: ~409 -> Check 2 (h=56) center ~ 441 (y: 413 to 469) -> Gap from Check 1: 413 - 373 = 40px!
# Row 5 center: ~556 -> Check 3 (h=56) center ~ 537 (y: 509 to 565) -> Gap from Check 2: 509 - 469 = 40px!
# Row 6/7 center: ~661 -> Check 4 (h=56) center ~ 633 (y: 605 to 661) -> Gap from Check 3: 605 - 565 = 40px!
# Row 9 center: ~764 -> Check 5 (h=56) center ~ 729 (y: 701 to 757) -> Gap from Check 4: 701 - 661 = 40px!
# Row 10 center: ~809 -> Check 6 (h=56) center ~ 825 (y: 797 to 853) -> Gap from Check 5: 797 - 853? wait: 797 - 757 = 40px!

checks = [
    ("Check 1 (chain)", 297, 76, 335.0),
    ("Check 2 (validity)", 413, 56, 441.0),
    ("Check 3 (SAN)", 509, 56, 537.0),
    ("Check 4 (key usage)", 605, 56, 633.0),
    ("Check 5 (revocation)", 701, 56, 729.0),
    ("Check 6 (signature)", 797, 56, 825.0)
]

for c in checks:
    print(f"{c[0]:25s} | y={c[1]}..{c[1]+c[2]} | h={c[2]} | center={c[3]}")

# Check gaps between checks:
for i in range(len(checks)-1):
    gap = checks[i+1][1] - (checks[i][1] + checks[i][2])
    print(f"Gap {i+1}->{i+2}: {gap}px")
