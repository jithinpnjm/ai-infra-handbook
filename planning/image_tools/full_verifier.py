import xml.etree.ElementTree as ET
import re

tree = ET.parse("output.svg")
root = tree.getroot()

# 1. Check title and desc are first children
first_two = [child.tag.split('}')[-1] for child in list(root)[:2]]
print("First two elements:", first_two)
assert first_two == ['title', 'desc'], f"Expected ['title', 'desc'], got {first_two}"

# 2. Extract all text content
expected_labels = [
    # Title
    "Inside an X.509 certificate: the fields that matter and what each is checked for",
    # Analogy
    "a passport: a trusted office vouches that this photograph belongs to this name",
    # Card rows
    "Subject: who it is for",
    "Issuer: the CA that signed it",
    "Validity: notBefore and notAfter, checked against the client's own clock",
    "Public key",
    "Subject Alternative Names (SAN): the DNS names or IPs the certificate is valid for; browsers and modern libraries ignore the old CN field",
    "Key usage and extended key usage: serverAuth, clientAuth",
    "Basic constraints: whether this is a CA",
    "Authority and subject key identifiers",
    "CRL and OCSP URLs",
    "Issuer's signature",
    # Checks
    "chain built from leaf to trusted root using the intermediates the server presents",
    "each signature",
    "validity dates",
    "key usage and basic constraints",
    "name against the SAN",
    "revocation status if enabled",
    # Commands
    "openssl x509 -in cert.pem -noout -text",
    "openssl x509 -noout -subject -issuer -dates -ext subjectAltName,basicConstraints,keyUsage,extendedKeyUsage",
    "openssl x509 -noout -checkend 2592000 (non-zero exit if it expires within 30 days)",
    "openssl verify -CAfile ca.pem -untrusted intermediate.pem leaf.pem",
    # Bottom bar
    "Each validation step can fail for a different reason"
]

# Get all text elements
text_elements = root.findall('.//{http://www.w3.org/2000/svg}text')
print(f"Total <text> elements: {len(text_elements)}")

extracted_texts = []
for t in text_elements:
    full_t = "".join(t.itertext())
    # normalize whitespace
    full_t = re.sub(r'\s+', ' ', full_t).strip()
    extracted_texts.append(full_t)
    print(f"Found text: {full_t}")

print("\n--- Verifying each expected label ---")
for exp in expected_labels:
    # normalize expected
    exp_norm = re.sub(r'\s+', ' ', exp).strip()
    found = False
    for ext in extracted_texts:
        if exp_norm == ext or exp_norm in ext:
            found = True
            break
    if not found:
        print(f"MISSING LABEL: {exp}")
    else:
        print(f"MATCH: {exp[:40]}...")

# 3. Check for style words in text: orange, green, grey, bold, monospace, arrow
style_words = ["orange", "green", "grey", "bold", "monospace", "arrow"]
for ext in extracted_texts:
    for sw in style_words:
        if sw in ext.lower():
            print(f"WARNING: Style word '{sw}' found in text: {ext}")

# 4. Check font sizes >= 24
for elem in root.iter():
    fs = elem.get('font-size')
    if fs:
        size = float(re.sub(r'[^\d.]', '', fs))
        if size < 24:
            print(f"WARNING: font-size < 24 found: {size} in {elem.tag}")

print("Font-size verification complete!")
