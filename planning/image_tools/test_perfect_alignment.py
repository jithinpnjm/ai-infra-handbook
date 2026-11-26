# Let's adjust row heights/gaps and check positions

# Card: y = 278, h = 570
# Available for rows: 570 - 24 (top/bot pad) = 546

# If we want exact horizontal arrows from rows to checks:
# Let's see:
# Arrow 1 from Row 2 (Issuer): y = 345 -> Check 1 (h=76): y = 307..383 (center 345)
# Gap between Check 1 and Check 2: 40px -> Check 2 starts at 383 + 40 = 423
# Check 2 (Validity): y = 423..479 (h=56, center 451) -> Arrow 2 from Row 3 (Validity) at y = 451!
# Gap between Check 2 and Check 3: 40px -> Check 3 starts at 479 + 40 = 519
# Check 3 (SAN): y = 519..575 (h=56, center 547) -> Arrow 3 from Row 5 (SAN) at y = 547!
# Gap between Check 3 and Check 4: 40px -> Check 4 starts at 575 + 40 = 615
# Check 4 (Key usage & basic constraints): y = 615..671 (h=56, center 643) -> Arrow 4 from Rows 6/7 at y = 643!
# Gap between Check 4 and Check 5: 40px -> Check 5 starts at 671 + 40 = 711
# Check 5 (Revocation): y = 711..767 (h=56, center 739) -> Arrow 5 from Row 9 (CRL/OCSP) at y = 739!
# Gap between Check 5 and Check 6: 40px -> Check 6 starts at 767 + 40 = 807
# Check 6 (Each signature): y = 807..863 (h=56, center 835) -> Arrow 6 from Row 10 (Signature) at y = 835!

print("Total checks span: 307 to 863 = 556px")
print("Gaps between checks: all exactly 40px!")
print("Target arrow Y values:")
print("Arrow 1: y = 345 (Row 2 Issuer)")
print("Arrow 2: y = 451 (Row 3 Validity)")
print("Arrow 3: y = 547 (Row 5 SAN)")
print("Arrow 4: y = 643 (Row 6/7 Key usage/Basic constraints)")
print("Arrow 5: y = 739 (Row 9 CRL/OCSP)")
print("Arrow 6: y = 835 (Row 10 Signature)")
