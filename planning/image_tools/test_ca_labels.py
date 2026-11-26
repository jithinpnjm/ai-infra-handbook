import re
import xml.etree.ElementTree as ET

# Expected labels exactly as in spec
item_title = "Building a private CA by hand: the seven steps and why each is there"
step_1 = "Make the CA key and self-signed root: openssl req -x509 ... -subj /CN=Lab Root CA -addext basicConstraints=critical,CA:TRUE -addext keyUsage=critical,keyCertSign,cRLSign -keyout ca.key -out ca.pem (10 years)"
step_2 = "Make the server key and CSR: openssl req -newkey ec ... -subj /CN=api.lab.internal -keyout srv.key -out srv.csr; a CSR carries only the public key and the requested names, the application form you send to the CA, never the secret"
step_3 = "Write the extension file srv.ext: subjectAltName=DNS:api.lab.internal,DNS:*.lab.internal,IP:10.0.0.5; extendedKeyUsage=serverAuth; basicConstraints=CA:FALSE"
step_4 = "Sign: openssl x509 -req -in srv.csr -CA ca.pem -CAkey ca.key -CAcreateserial -days 90 -extfile srv.ext -out srv.pem"
step_5 = "Verify: openssl verify -CAfile ca.pem srv.pem"
step_6 = "Trust the CA on the client (update-ca-certificates)"
step_7 = "Serve it with nginx: ssl_certificate, ssl_certificate_key, ssl_protocols TLSv1.2 TLSv1.3, http2 on"
panel_title = "Real use"
panel_body = "prefer step-ca or Vault PKI; keep the root offline and issue from intermediates; name constraints, short lifetimes, automated rotation; distribute the root to all trust stores through configuration management; keys generated on the server or in an HSM, TPM or KMS, never emailed, mode 0600, one machine per key; a client certificate is built the same way with extendedKeyUsage=clientAuth"
public_ca = "Let's Encrypt, DigiCert, Google Trust Services check control of the domain (DV) with a DNS or HTTP challenge; OV and EV add organisation checks; ACME (RFC 8555) automates renewal through certbot, acme.sh, Caddy, cert-manager; Let's Encrypt lasts 90 days; CT logs every public certificate; CAA records restrict which CAs may issue"
bottom_bar = "Building one by hand once is the best way to understand what the tools do for you"

expected_labels = [
    item_title,
    step_1,
    step_2,
    step_3,
    step_4,
    step_5,
    step_6,
    step_7,
    panel_title,
    panel_body,
    public_ca,
    bottom_bar
]

step_numbers = {"1", "2", "3", "4", "5", "6", "7"}

print("Expected labels count:", len(expected_labels))
print("Step numbers count:", len(step_numbers))
