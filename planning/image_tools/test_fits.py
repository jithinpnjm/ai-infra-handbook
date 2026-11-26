import sys

def check_line(text, font_size, font_type, box_width, padding=16):
    rate = 0.62 if font_type == 'mono' else 0.6
    est_width = len(text) * font_size * rate
    avail_width = box_width - 2 * padding
    fits = est_width <= avail_width
    return fits, est_width, avail_width

# Let's test lines for each step
box_w_step = 1010
box_w_right = 470
box_w_full = 1520

# Step 1:
# In Step 1, we have an icon + circle on the left:
# Box is x=40 to 1050 (w=1010).
# Circle is cx=85, cy=185 (r=24). Icon is at x=125, y=160 (w=48, h=48).
# Text starts at x=190.
# Available text width inside box = 1050 - 190 - 20 (right padding) = 840 px.

print("--- Step 1 ---")
s1_lines = [
    ("Make the CA key and self-signed root:", 30, 'sans'),
    ("openssl req -x509 ... -subj /CN=Lab Root CA", 24, 'mono'),
    ("-addext basicConstraints=critical,CA:TRUE", 24, 'mono'),
    ("-addext keyUsage=critical,keyCertSign,cRLSign", 24, 'mono'),
    ("-keyout ca.key -out ca.pem (10 years)", 24, 'mono')
]
for t, fs, ft in s1_lines:
    fits, est, av = check_line(t, fs, ft, 840 + 32, padding=16)
    print(f"[{'PASS' if fits else 'FAIL'}] est={est:.1f} av={av:.1f} len={len(t)} : '{t}'")

print("--- Step 2 ---")
s2_lines = [
    ("Make the server key and CSR:", 30, 'sans'),
    ("openssl req -newkey ec ... -subj /CN=api.lab.internal -keyout srv.key -out srv.csr;", 24, 'mono'),
    ("a CSR carries only the public key and the requested names, the application form you", 24, 'sans'),
    ("send to the CA, never the secret", 24, 'sans')
]
for t, fs, ft in s2_lines:
    fits, est, av = check_line(t, fs, ft, 840 + 32, padding=16)
    print(f"[{'PASS' if fits else 'FAIL'}] est={est:.1f} av={av:.1f} len={len(t)} : '{t}'")

print("--- Step 3 ---")
s3_lines = [
    ("Write the extension file srv.ext:", 30, 'sans'),
    ("subjectAltName=DNS:api.lab.internal,DNS:*.lab.internal,IP:10.0.0.5;", 24, 'mono'),
    ("extendedKeyUsage=serverAuth; basicConstraints=CA:FALSE", 24, 'mono')
]
for t, fs, ft in s3_lines:
    fits, est, av = check_line(t, fs, ft, 840 + 32, padding=16)
    print(f"[{'PASS' if fits else 'FAIL'}] est={est:.1f} av={av:.1f} len={len(t)} : '{t}'")

print("--- Step 4 ---")
s4_lines = [
    ("Sign: openssl x509 -req -in srv.csr -CA ca.pem -CAkey ca.key", 24, 'mono'),
    ("-CAcreateserial -days 90 -extfile srv.ext -out srv.pem", 24, 'mono')
]
# Wait, for step 4 title: "Sign:" can be 30px bold!
# Let's test "Sign: openssl x509 -req -in srv.csr -CA ca.pem -CAkey ca.key"
# Wait, "Sign:" (30px) + " openssl x509 -req -in srv.csr -CA ca.pem -CAkey ca.key" (24px mono):
est = 5 * 30 * 0.6 + 55 * 24 * 0.62
print(f"Step 4 line 1 combined est={est:.1f} av=840: {est <= 840}")

print("--- Step 5 ---")
# "Verify: " (30px) + "openssl verify -CAfile ca.pem srv.pem" (24px mono):
est5 = 8 * 30 * 0.6 + 37 * 24 * 0.62
print(f"Step 5 combined est={est5:.1f} av=840: {est5 <= 840}")

print("--- Step 6 ---")
# "Trust the CA on the client " (30px) + "(update-ca-certificates)" (24px mono):
est6 = 27 * 30 * 0.6 + 24 * 24 * 0.62
print(f"Step 6 combined est={est6:.1f} av=840: {est6 <= 840}")

print("--- Step 7 ---")
s7_lines = [
    ("Serve it with nginx: ssl_certificate, ssl_certificate_key,", 24, 'mono'),
    ("ssl_protocols TLSv1.2 TLSv1.3, http2 on", 24, 'mono')
]
for t, fs, ft in s7_lines:
    fits, est, av = check_line(t, fs, ft, 840 + 32, padding=16)
    print(f"[{'PASS' if fits else 'FAIL'}] est={est:.1f} av={av:.1f} len={len(t)} : '{t}'")
