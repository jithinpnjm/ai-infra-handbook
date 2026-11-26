def test_wrap(label, max_chars_mono=58, max_chars_sans=60):
    words = label.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars_mono:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

# Let's test Step 2:
s2 = "Make the server key and CSR: openssl req -newkey ec ... -subj /CN=api.lab.internal -keyout srv.key -out srv.csr; a CSR carries only the public key and the requested names, the application form you send to the CA, never the secret"
# Step 3:
s3 = "Write the extension file srv.ext: subjectAltName=DNS:api.lab.internal,DNS:*.lab.internal,IP:10.0.0.5; extendedKeyUsage=serverAuth; basicConstraints=CA:FALSE"
# Step 4:
s4 = "Sign: openssl x509 -req -in srv.csr -CA ca.pem -CAkey ca.key -CAcreateserial -days 90 -extfile srv.ext -out srv.pem"
# Step 7:
s7 = "Serve it with nginx: ssl_certificate, ssl_certificate_key, ssl_protocols TLSv1.2 TLSv1.3, http2 on"

print("Step 2:")
s2_manual = [
    ("Make the server key and CSR:", 30, 'sans'),
    ("openssl req -newkey ec ... -subj /CN=api.lab.internal", 24, 'mono'),
    ("-keyout srv.key -out srv.csr;", 24, 'mono'),
    ("a CSR carries only the public key and the requested names,", 24, 'sans'),
    ("the application form you send to the CA, never the secret", 24, 'sans')
]
for t, fs, ft in s2_manual:
    rate = 0.62 if ft == 'mono' else 0.6
    w = len(t) * fs * rate
    print(f"  [{len(t):2d} ch, {w:5.1f} px] {t}")

print("\nStep 3:")
s3_manual = [
    ("Write the extension file srv.ext:", 30, 'sans'),
    ("subjectAltName=DNS:api.lab.internal,DNS:*.lab.internal,IP:10.0.0.5;", 24, 'mono'),
    ("extendedKeyUsage=serverAuth; basicConstraints=CA:FALSE", 24, 'mono')
]
for t, fs, ft in s3_manual:
    rate = 0.62 if ft == 'mono' else 0.6
    w = len(t) * fs * rate
    print(f"  [{len(t):2d} ch, {w:5.1f} px] {t}")
# Wait, s3 line 2 has 67 chars * 24 * 0.62 = 996.9 px!
# If available width is 915 px, 996.9 px exceeds 915 px!
# Can s3 line 2 be split?
# Where can subjectAltName be split?
# "subjectAltName=DNS:api.lab.internal," (36 chars * 14.88 = 535 px)
# "DNS:*.lab.internal,IP:10.0.0.5;" (31 chars * 14.88 = 461 px)
print("  Split subjectAltName:")
for part in ["subjectAltName=DNS:api.lab.internal,", "DNS:*.lab.internal,IP:10.0.0.5;"]:
    print(f"    [{len(part):2d} ch, {len(part)*24*0.62:5.1f} px] {part}")

print("\nStep 4:")
s4_manual = [
    ("Sign: openssl x509 -req -in srv.csr -CA ca.pem", 24, 'mono'),
    ("-CAkey ca.key -CAcreateserial -days 90 -extfile srv.ext -out srv.pem", 24, 'mono')
]
for t, fs, ft in s4_manual:
    rate = 0.62 if ft == 'mono' else 0.6
    w = len(t) * fs * rate
    print(f"  [{len(t):2d} ch, {w:5.1f} px] {t}")

print("\nStep 6:")
s6_manual = [
    ("Trust the CA on the client", 30, 'sans'),
    ("(update-ca-certificates)", 24, 'mono')
]
for t, fs, ft in s6_manual:
    rate = 0.62 if ft == 'mono' else 0.6
    w = len(t) * fs * rate
    print(f"  [{len(t):2d} ch, {w:5.1f} px] {t}")

print("\nStep 7:")
s7_manual = [
    ("Serve it with nginx: ssl_certificate, ssl_certificate_key,", 24, 'mono'),
    ("ssl_protocols TLSv1.2 TLSv1.3, http2 on", 24, 'mono')
]
for t, fs, ft in s7_manual:
    rate = 0.62 if ft == 'mono' else 0.6
    w = len(t) * fs * rate
    print(f"  [{len(t):2d} ch, {w:5.1f} px] {t}")
