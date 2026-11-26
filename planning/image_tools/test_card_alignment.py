# Card is y = 249 to 829 (height = 580)
# Inside card rows:
# Row 1: Subject (h=38) -> y = 257..295 (center 276)
# Row 2: Issuer (h=38) -> y = 299..337 (center 318)
# Row 3: Validity (h=60) -> y = 341..401 (center 371)
# Row 4: Public key (h=36) -> y = 405..441 (center 423)
# Row 5: SAN (h=104) -> y = 445..549 (center 497)
# Row 6: Key usage... (h=58) -> y = 553..611 (center 582)
# Row 7: Basic constraints (h=38) -> y = 615..653 (center 634)
# Row 8: Authority... (h=38) -> y = 657..695 (center 676)
# Row 9: CRL... (h=38) -> y = 699..737 (center 718)
# Row 10: Issuer's signature (h=38) -> y = 741..779 (center 760)

# Check centers:
# Check 1: 289 (y: 249..329) -> Row 2 (Issuer, 299..337) center is 318. 318 is directly inside Check 1 (249..329)!
# Check 2: 399 (y: 369..429) -> Row 3 (Validity, 341..401) center is 371. 371 is directly inside Check 2 (369..429)!
# Check 3: 499 (y: 469..529) -> Row 5 (SAN, 445..549) center is 497. 497 is directly in the center of Check 3 (469..529)!
# Check 4: 599 (y: 569..629) -> Rows 6/7 midpoint: (582+634)/2 = 608. 608 is directly inside Check 4 (569..629)!
# Check 5: 699 (y: 669..729) -> Row 9 (CRL/OCSP, 699..737) center is 718. 718 is directly inside Check 5 (669..729)!
# Check 6: 799 (y: 769..829) -> Row 10 (Signature, 741..779) center is 760. Arrow can go from 760 to 799 orthogonally!

print("Arrows:")
print("1. Issuer (y=318) -> Check 1 (y=318): horizontal!")
print("2. Validity (y=385) -> Check 2 (y=385): horizontal!")
print("3. SAN (y=499) -> Check 3 (y=499): horizontal!")
print("4. Key usage & Basic constr (y=608) -> Check 4 (y=608): horizontal!")
print("5. CRL/OCSP (y=718) -> Check 5 (y=718): horizontal!")
print("6. Issuer signature (y=760) -> Check 6 (y=799): orthogonal (720,760 -> 770,760 -> 770,799 -> 820,799)!")
