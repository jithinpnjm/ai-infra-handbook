# Let's verify card row layout

# Card: y = 278, h = 590 (y: 278 to 868)
# Left column: x = 40 to 720 (width = 680)
# Inside rows: x = 55 to 705 (width = 650)
# Arrow gap: x = 720 to 820 (width = 100)
# Right column: x = 820 to 1560 (width = 740)

rows = [
    # (name, y, h, text)
    ("Subject", 290, 36, "Subject: who it is for"),
    ("Issuer", 332, 36, "Issuer: the CA that signed it"),
    ("Validity", 374, 58, "Validity: notBefore and notAfter,\nchecked against the client's own clock"),
    ("Public key", 438, 36, "Public key"),
    ("SAN", 480, 114, "Subject Alternative Names (SAN):\nthe DNS names or IPs the certificate\nis valid for; browsers and modern\nlibraries ignore the old CN field"),
    ("Key usage", 600, 58, "Key usage and extended key usage:\nserverAuth, clientAuth"),
    ("Basic constr", 664, 36, "Basic constraints: whether this is a CA"),
    ("Auth key id", 706, 36, "Authority and subject key identifiers"),
    ("CRL/OCSP", 748, 36, "CRL and OCSP URLs"),
    ("Issuer sig", 790, 36, "Issuer's signature")
]

for name, y, h, t in rows:
    print(f"{name:15s}: y={y}..{y+h} (center={y+h/2})")
print("Card bottom:", 278 + 590, "Last row ends at:", 790 + 36)
