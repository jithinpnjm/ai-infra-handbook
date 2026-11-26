# Verify conservative line widths
def sans_width(s, size=24):
    return len(s) * 0.6 * size

def mono_width(s, size=24):
    return len(s) * 0.62 * size

# Text in card rows: width available inside card row box:
# Row box: x=52..708 (w=656). Text at x=68. Available w = 656 - 32 = 624px.
card_texts = [
    "Subject: who it is for",
    "Issuer: the CA that signed it",
    "Validity: notBefore and notAfter,",
    "checked against the client's own clock",
    "Public key",
    "Subject Alternative Names (SAN):",
    "the DNS names or IPs the certificate is",
    "valid for; browsers and modern libraries",
    "ignore the old CN field",
    "Key usage and extended key usage:",
    "serverAuth, clientAuth",
    "Basic constraints: whether this is a CA",
    "Authority and subject key identifiers",
    "CRL and OCSP URLs",
    "Issuer's signature"
]

print("--- Card Rows Text Widths (Max 624px) ---")
for t in card_texts:
    w = sans_width(t, 24)
    print(f"{w:5.1f}px | {t}")
    assert w <= 624, f"Overflow in card row: {t} ({w} > 624)"

# Check nodes: width available inside check node:
# Node box: x=820..1560 (w=740).
# Icon: x=838..890 (w=52). Text at x=908.
# Box ends at 1560. Available w for text = 1560 - 16 - 908 = 636px.
check_texts = [
    "chain built from leaf to trusted root",
    "using the intermediates the server presents",
    "validity dates",
    "name against the SAN",
    "key usage and basic constraints",
    "revocation status if enabled",
    "each signature"
]

print("\n--- Check Nodes Text Widths (Max 636px) ---")
for t in check_texts:
    w = sans_width(t, 24)
    print(f"{w:5.1f}px | {t}")
    assert w <= 636, f"Overflow in check node: {t} ({w} > 636)"

# Command strip: width available inside command box:
# Command box: x=52..1548 (w=1496). Text at x=68. Available w = 1496 - 32 = 1464px.
cmd_texts = [
    "openssl x509 -in cert.pem -noout -text",
    "openssl x509 -noout -subject -issuer -dates -ext ",
    "subjectAltName,basicConstraints,keyUsage,extendedKeyUsage",
    "openssl x509 -noout -checkend 2592000 (non-zero exit if it expires within 30 days)",
    "openssl verify -CAfile ca.pem -untrusted intermediate.pem leaf.pem"
]

print("\n--- Command Strip Text Widths (Max 1464px) ---")
for t in cmd_texts:
    w = mono_width(t, 24)
    print(f"{w:6.1f}px | {t}")
    assert w <= 1464, f"Overflow in command: {t} ({w} > 1464)"

print("\nALL TEXT LINES PASS CONSERVATIVE WIDTH CHECKS WITH > 16px PADDING!")
