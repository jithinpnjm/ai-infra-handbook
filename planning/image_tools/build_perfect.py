#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_perfect_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>Building a private CA by hand: the seven steps and why each is there</title>')
    svg.append('  <desc>A visual walkthrough of the seven steps to build, sign, verify, trust, and serve with a private Certificate Authority, contrasted with production PKI best practices and public CA operations.</desc>')
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    
    # Title: 48px bold
    svg.append('  <text x="800" y="45" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Building a private CA by hand: </tspan>')
    svg.append('    <tspan x="800" dy="50">the seven steps and why each is there</tspan>')
    svg.append('  </text>')
    
    # ================= Step 1 =================
    # by=108, bh=153
    # Lines y: 147, 170, 193, 216, 239
    svg.append('  <g id="step-1">')
    svg.append('    <rect x="40" y="108" width="1030" height="153" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <circle cx="72" cy="184" r="22" fill="#207448" />')
    svg.append('    <text x="72" y="193" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>')
    svg.append('    <g transform="translate(104, 160)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 20 4 L 38 11 V 24 C 38 35 20 44 20 44 C 20 44 2 35 2 24 V 11 Z" />')
    svg.append('      <circle cx="20" cy="20" r="5" />')
    svg.append('      <line x1="20" y1="25" x2="20" y2="35" />')
    svg.append('      <line x1="17" y1="30" x2="23" y2="30" />')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="165" y="147" font-size="30" font-weight="bold">Make the CA key and self-signed root: </tspan>')
    svg.append('      <tspan x="165" y="170" font-family="monospace" font-size="24">openssl req -x509 ... -subj /CN=Lab Root CA </tspan>')
    svg.append('      <tspan x="165" y="193" font-family="monospace" font-size="24">-addext basicConstraints=critical,CA:TRUE </tspan>')
    svg.append('      <tspan x="165" y="216" font-family="monospace" font-size="24">-addext keyUsage=critical,keyCertSign,cRLSign </tspan>')
    svg.append('      <tspan x="165" y="239" font-family="monospace" font-size="24">-keyout ca.key -out ca.pem (10 years)</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= Step 2 =================
    # by=266, bh=153
    # Lines y: 305, 328, 351, 374, 397
    svg.append('  <g id="step-2">')
    svg.append('    <rect x="40" y="266" width="1030" height="153" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <circle cx="72" cy="342" r="22" fill="#207448" />')
    svg.append('    <text x="72" y="351" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>')
    svg.append('    <g transform="translate(104, 318)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="4" width="32" height="40" rx="4" />')
    svg.append('      <line x1="12" y1="14" x2="28" y2="14" />')
    svg.append('      <line x1="12" y1="22" x2="28" y2="22" />')
    svg.append('      <line x1="12" y1="30" x2="20" y2="30" />')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="165" y="305" font-size="30" font-weight="bold">Make the server key and CSR: </tspan>')
    svg.append('      <tspan x="165" y="328" font-family="monospace" font-size="24">openssl req -newkey ec ... -subj /CN=api.lab.internal </tspan>')
    svg.append('      <tspan x="165" y="351" font-family="monospace" font-size="24">-keyout srv.key -out srv.csr; </tspan>')
    svg.append('      <tspan x="165" y="374" font-family="sans-serif" font-size="24">a CSR carries only the public key and the requested names, </tspan>')
    svg.append('      <tspan x="165" y="397" font-family="sans-serif" font-size="24">the application form you send to the CA, never the secret</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= Step 3 =================
    # by=424, bh=130
    # Lines y: 463, 486, 509, 532
    svg.append('  <g id="step-3">')
    svg.append('    <rect x="40" y="424" width="1030" height="130" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <circle cx="72" cy="489" r="22" fill="#207448" />')
    svg.append('    <text x="72" y="498" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>')
    svg.append('    <g transform="translate(104, 465)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 6 4 H 26 L 36 14 V 42 H 6 Z" />')
    svg.append('      <polyline points="26,4 26,14 36,14" />')
    svg.append('      <line x1="12" y1="24" x2="28" y2="24" />')
    svg.append('      <line x1="12" y1="32" x2="24" y2="32" />')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="165" y="463" font-size="30" font-weight="bold">Write the extension file srv.ext: </tspan>')
    svg.append('      <tspan x="165" y="486" font-family="monospace" font-size="24">subjectAltName=DNS:api.lab.internal,</tspan><tspan x="165" y="509" font-family="monospace" font-size="24">DNS:*.lab.internal,IP:10.0.0.5; </tspan>')
    svg.append('      <tspan x="165" y="532" font-family="monospace" font-size="24">extendedKeyUsage=serverAuth; basicConstraints=CA:FALSE</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= Step 4 =================
    # by=559, bh=107
    # Lines y: 598, 621, 644
    svg.append('  <g id="step-4">')
    svg.append('    <rect x="40" y="559" width="1030" height="107" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <circle cx="72" cy="612" r="22" fill="#207448" />')
    svg.append('    <text x="72" y="621" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>')
    svg.append('    <g transform="translate(104, 588)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 6 36 L 26 12 L 34 20 L 14 44 L 6 44 Z" />')
    svg.append('      <line x1="22" y1="16" x2="30" y2="24" />')
    svg.append('      <circle cx="33" cy="9" r="3" fill="#207448" />')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="165" y="598" font-size="30" font-weight="bold">Sign: </tspan>')
    svg.append('      <tspan x="245" y="598" font-family="monospace" font-size="24">openssl x509 -req -in srv.csr -CA ca.pem </tspan>')
    svg.append('      <tspan x="165" y="621" font-family="monospace" font-size="24">-CAkey ca.key -CAcreateserial -days 90 </tspan>')
    svg.append('      <tspan x="165" y="644" font-family="monospace" font-size="24">-extfile srv.ext -out srv.pem</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= Step 5 =================
    # by=671, bh=63
    # Line y: 710
    svg.append('  <g id="step-5">')
    svg.append('    <rect x="40" y="671" width="1030" height="63" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <circle cx="72" cy="702" r="22" fill="#207448" />')
    svg.append('    <text x="72" y="711" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>')
    svg.append('    <g transform="translate(104, 680)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="20" cy="22" r="16" />')
    svg.append('      <polyline points="13,22 18,27 28,17" />')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="165" y="710" font-size="30" font-weight="bold">Verify: </tspan>')
    svg.append('      <tspan x="270" y="710" font-family="monospace" font-size="24">openssl verify -CAfile ca.pem srv.pem</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= Step 6 =================
    # by=739, bh=84
    # Lines y: 778, 801
    svg.append('  <g id="step-6">')
    svg.append('    <rect x="40" y="739" width="1030" height="84" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <circle cx="72" cy="781" r="22" fill="#207448" />')
    svg.append('    <text x="72" y="790" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">6</text>')
    svg.append('    <g transform="translate(104, 757)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="18" width="24" height="22" rx="4" />')
    svg.append('      <path d="M 13 18 V 11 C 13 7 27 7 27 11 V 18" />')
    svg.append('      <circle cx="20" cy="29" r="2" fill="#207448" />')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="165" y="778" font-size="30" font-weight="bold">Trust the CA on the client </tspan>')
    svg.append('      <tspan x="165" y="801" font-family="monospace" font-size="24">(update-ca-certificates)</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= Step 7 =================
    # by=828, bh=107
    # Lines y: 867, 890, 913
    svg.append('  <g id="step-7">')
    svg.append('    <rect x="40" y="828" width="1030" height="107" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <circle cx="72" cy="881" r="22" fill="#207448" />')
    svg.append('    <text x="72" y="890" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">7</text>')
    svg.append('    <g transform="translate(104, 857)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="28" height="14" rx="3" />')
    svg.append('      <rect x="6" y="26" width="28" height="14" rx="3" />')
    svg.append('      <circle cx="12" cy="15" r="2" fill="#207448" />')
    svg.append('      <circle cx="12" cy="33" r="2" fill="#207448" />')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="165" y="867" font-size="30" font-weight="bold">Serve it with nginx: </tspan>')
    svg.append('      <tspan x="165" y="890" font-family="monospace" font-size="24">ssl_certificate, ssl_certificate_key, </tspan>')
    svg.append('      <tspan x="165" y="913" font-family="monospace" font-size="24">ssl_protocols TLSv1.2 TLSv1.3, http2 on</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= Right Panel: Real use (orange) =================
    # y=108, h=827 (ends at 935)
    svg.append('  <g id="real-use">')
    svg.append('    <rect x="1090" y="108" width="470" height="827" rx="14" fill="#e8f1ea" stroke="#db8129" stroke-width="3.5" />')
    svg.append('    <g transform="translate(1120, 130)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="6" width="36" height="36" rx="6" />')
    svg.append('      <circle cx="24" cy="24" r="8" />')
    svg.append('      <line x1="24" y1="10" x2="24" y2="16" />')
    svg.append('      <line x1="24" y1="32" x2="24" y2="38" />')
    svg.append('      <line x1="10" y1="24" x2="16" y2="24" />')
    svg.append('      <line x1="32" y1="24" x2="38" y2="24" />')
    svg.append('    </g>')
    svg.append('    <text x="1175" y="160" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Real use</text>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    r_lines = [
        "prefer step-ca or Vault PKI; ",
        "keep the root offline and ",
        "issue from intermediates; ",
        "name constraints, short ",
        "lifetimes, automated ",
        "rotation; distribute the ",
        "root to all trust stores ",
        "through configuration ",
        "management; keys generated ",
        "on the server or in an HSM, ",
        "TPM or KMS, never emailed, ",
        "mode 0600, one machine per ",
        "key; a client certificate is ",
        "built the same way with ",
        "extendedKeyUsage=clientAuth"
    ]
    y_r = 205
    for i, rl in enumerate(r_lines):
        svg.append(f'      <tspan x="1120" y="{y_r + i * 36}">{rl}</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= Public CA strip =================
    # y=945, h=122 (ends at 1067)
    svg.append('  <g id="public-ca">')
    svg.append('    <rect x="40" y="945" width="1520" height="122" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <g transform="translate(68, 980)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="24" cy="24" r="18" />')
    svg.append('      <ellipse cx="24" cy="24" rx="18" ry="8" />')
    svg.append('      <line x1="24" y1="6" x2="24" y2="42" />')
    svg.append('    </g>')
    svg.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    p_lines = [
        "Let's Encrypt, DigiCert, Google Trust Services check control of the domain (DV) with a DNS or ",
        "HTTP challenge; OV and EV add organisation checks; ACME (RFC 8555) automates renewal through ",
        "certbot, acme.sh, Caddy, cert-manager; Let's Encrypt lasts 90 days; CT logs every public ",
        "certificate; CAA records restrict which CAs may issue"
    ]
    y_p = 979
    for i, pl in enumerate(p_lines):
        svg.append(f'      <tspan x="135" y="{y_p + i * 22}">{pl}</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ================= Bottom bar =================
    # y=1075, h=52 (ends at 1127)
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1075" width="1520" height="52" rx="10" fill="#207448" />')
    svg.append('    <g transform="translate(68, 1081)" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="15" cy="20" r="9" />')
    svg.append('      <line x1="24" y1="20" x2="42" y2="20" />')
    svg.append('      <line x1="34" y1="20" x2="34" y2="28" />')
    svg.append('      <line x1="40" y1="20" x2="40" y2="26" />')
    svg.append('    </g>')
    svg.append('    <text x="800" y="1110" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">')
    svg.append('      Building one by hand once is the best way to understand what the tools do for you')
    svg.append('    </text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    return "\n".join(svg)

if __name__ == "__main__":
    content = build_perfect_svg()
    with open("candidate_perfect.svg", "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote candidate_perfect.svg")
