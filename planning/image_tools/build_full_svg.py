#!/usr/bin/env python3
import re
import xml.etree.ElementTree as ET

def generate_svg():
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    lines.append('  <title>Building a private CA by hand: the seven steps and why each is there</title>')
    lines.append('  <desc>A visual walkthrough of the seven steps to build, sign, verify, trust, and serve with a private Certificate Authority, contrasted with production PKI best practices and public CA operations.</desc>')
    lines.append('')
    # Background
    lines.append('  <!-- Canvas Background -->')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    lines.append('')
    # Title
    lines.append('  <!-- Title: max 2 lines, 48px bold -->')
    lines.append('  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    lines.append('    <tspan x="800" dy="0">Building a private CA by hand: </tspan>')
    lines.append('    <tspan x="800" dy="54">the seven steps and why each is there</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Step cards geometry
    # Left column: x=40, width=1030
    # Text inside card starts at x=165 (leaving room for circle cx=72 and icon at x=106..154)
    # Card right edge = 1070. Usable text width from 165 to 1050 = 885 px.
    
    # Let's define the steps layout
    # Step 1: y=134, h=124
    # Step 2: y=268, h=128
    # Step 3: y=406, h=106
    # Step 4: y=522, h=84
    # Step 5: y=616, h=72
    # Step 6: y=698, h=72
    # Step 7: y=780, h=92
    # Bottom of step 7 = 872.
    # Right panel: x=1090, y=134, w=470, h=738. Bottom = 872.
    # Public CA strip: x=40, y=890, w=1520, h=188. Bottom = 1078.
    # Bottom bar: x=40, y=1096, w=1520, h=66. Bottom = 1162.

    # Step 1
    lines.append('  <!-- ==================== STEP 1 ==================== -->')
    lines.append('  <g id="step-1">')
    lines.append('    <rect x="40" y="134" width="1030" height="122" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <circle cx="72" cy="195" r="22" fill="#207448" />')
    lines.append('    <text x="72" y="204" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>')
    # Outline Icon: Root CA Key & Shield (center ~124, 195)
    lines.append('    <g transform="translate(104, 171)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <path d="M 20 4 L 38 11 V 24 C 38 35 20 44 20 44 C 20 44 2 35 2 24 V 11 Z" />')
    lines.append('      <circle cx="20" cy="20" r="5" />')
    lines.append('      <line x1="20" y1="25" x2="20" y2="35" />')
    lines.append('      <line x1="17" y1="30" x2="23" y2="30" />')
    lines.append('    </g>')
    lines.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="165" y="162" font-size="30" font-weight="bold">Make the CA key and self-signed root: </tspan>')
    lines.append('      <tspan x="165" y="189" font-family="monospace" font-size="24">openssl req -x509 ... -subj /CN=Lab Root CA </tspan>')
    lines.append('      <tspan x="165" y="215" font-family="monospace" font-size="24">-addext basicConstraints=critical,CA:TRUE </tspan>')
    lines.append('      <tspan x="165" y="241" font-family="monospace" font-size="24">-addext keyUsage=critical,keyCertSign,cRLSign -keyout ca.key -out ca.pem (10 years)</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')

    # Step 2
    lines.append('  <!-- ==================== STEP 2 ==================== -->')
    lines.append('  <g id="step-2">')
    lines.append('    <rect x="40" y="266" width="1030" height="128" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <circle cx="72" cy="330" r="22" fill="#207448" />')
    lines.append('    <text x="72" y="339" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>')
    # Outline Icon: Server CSR Document & Key
    lines.append('    <g transform="translate(104, 306)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <rect x="4" y="4" width="32" height="40" rx="4" />')
    lines.append('      <line x1="12" y1="14" x2="28" y2="14" />')
    lines.append('      <line x1="12" y1="22" x2="28" y2="22" />')
    lines.append('      <line x1="12" y1="30" x2="20" y2="30" />')
    lines.append('    </g>')
    lines.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="165" y="293" font-size="30" font-weight="bold">Make the server key and CSR: </tspan>')
    lines.append('      <tspan x="165" y="320" font-family="monospace" font-size="24">openssl req -newkey ec ... -subj /CN=api.lab.internal -keyout srv.key -out srv.csr; </tspan>')
    lines.append('      <tspan x="165" y="347" font-family="sans-serif" font-size="24">a CSR carries only the public key and the requested names, the application form you </tspan>')
    lines.append('      <tspan x="165" y="373" font-family="sans-serif" font-size="24">send to the CA, never the secret</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')

    # Step 3
    lines.append('  <!-- ==================== STEP 3 ==================== -->')
    lines.append('  <g id="step-3">')
    lines.append('    <rect x="40" y="404" width="1030" height="106" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <circle cx="72" cy="457" r="22" fill="#207448" />')
    lines.append('    <text x="72" y="466" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>')
    # Outline Icon: Config / Extension file
    lines.append('    <g transform="translate(104, 433)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <path d="M 6 4 H 26 L 36 14 V 42 H 6 Z" />')
    lines.append('      <polyline points="26,4 26,14 36,14" />')
    lines.append('      <line x1="12" y1="24" x2="28" y2="24" />')
    lines.append('      <line x1="12" y1="32" x2="24" y2="32" />')
    lines.append('    </g>')
    lines.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="165" y="432" font-size="30" font-weight="bold">Write the extension file srv.ext: </tspan>')
    lines.append('      <tspan x="165" y="461" font-family="monospace" font-size="24">subjectAltName=DNS:api.lab.internal,</tspan><tspan x="165" y="486" font-family="monospace" font-size="24">DNS:*.lab.internal,IP:10.0.0.5; </tspan>')
    lines.append('      <tspan x="590" y="486" font-family="monospace" font-size="24">extendedKeyUsage=serverAuth; basicConstraints=CA:FALSE</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')

    # Step 4
    lines.append('  <!-- ==================== STEP 4 ==================== -->')
    lines.append('  <g id="step-4">')
    lines.append('    <rect x="40" y="520" width="1030" height="84" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <circle cx="72" cy="562" r="22" fill="#207448" />')
    lines.append('    <text x="72" y="571" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>')
    # Outline Icon: Signing / Quill / Stamp
    lines.append('    <g transform="translate(104, 538)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <path d="M 6 36 L 26 12 L 34 20 L 14 44 L 6 44 Z" />')
    lines.append('      <line x1="22" y1="16" x2="30" y2="24" />')
    lines.append('      <circle cx="33" cy="9" r="3" fill="#207448" />')
    lines.append('    </g>')
    lines.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="165" y="552" font-size="30" font-weight="bold">Sign: </tspan>')
    lines.append('      <tspan x="250" y="552" font-family="monospace" font-size="24">openssl x509 -req -in srv.csr -CA ca.pem -CAkey ca.key </tspan>')
    lines.append('      <tspan x="165" y="583" font-family="monospace" font-size="24">-CAcreateserial -days 90 -extfile srv.ext -out srv.pem</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')

    # Step 5
    lines.append('  <!-- ==================== STEP 5 ==================== -->')
    lines.append('  <g id="step-5">')
    lines.append('    <rect x="40" y="614" width="1030" height="72" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <circle cx="72" cy="650" r="22" fill="#207448" />')
    lines.append('    <text x="72" y="659" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>')
    # Outline Icon: Verification Checkmark in Badge
    lines.append('    <g transform="translate(104, 626)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <circle cx="20" cy="24" r="16" />')
    lines.append('      <polyline points="13,24 18,29 28,19" />')
    lines.append('    </g>')
    lines.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="165" y="658" font-size="30" font-weight="bold">Verify: </tspan>')
    lines.append('      <tspan x="270" y="658" font-family="monospace" font-size="24">openssl verify -CAfile ca.pem srv.pem</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')

    # Step 6
    lines.append('  <!-- ==================== STEP 6 ==================== -->')
    lines.append('  <g id="step-6">')
    lines.append('    <rect x="40" y="696" width="1030" height="72" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <circle cx="72" cy="732" r="22" fill="#207448" />')
    lines.append('    <text x="72" y="741" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">6</text>')
    # Outline Icon: Client Trust Lock
    lines.append('    <g transform="translate(104, 708)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <rect x="8" y="18" width="24" height="22" rx="4" />')
    lines.append('      <path d="M 13 18 V 11 C 13 7 27 7 27 11 V 18" />')
    lines.append('      <circle cx="20" cy="29" r="2" fill="#207448" />')
    lines.append('    </g>')
    lines.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="165" y="740" font-size="30" font-weight="bold">Trust the CA on the client </tspan>')
    lines.append('      <tspan x="545" y="740" font-family="monospace" font-size="24">(update-ca-certificates)</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')

    # Step 7
    lines.append('  <!-- ==================== STEP 7 ==================== -->')
    lines.append('  <g id="step-7">')
    lines.append('    <rect x="40" y="778" width="1030" height="94" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <circle cx="72" cy="825" r="22" fill="#207448" />')
    lines.append('    <text x="72" y="834" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">7</text>')
    # Outline Icon: Server / Network globe / service
    lines.append('    <g transform="translate(104, 801)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <rect x="6" y="8" width="28" height="14" rx="3" />')
    lines.append('      <rect x="6" y="26" width="28" height="14" rx="3" />')
    lines.append('      <circle cx="12" cy="15" r="2" fill="#207448" />')
    lines.append('      <circle cx="12" cy="33" r="2" fill="#207448" />')
    lines.append('    </g>')
    lines.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="165" y="813" font-size="30" font-weight="bold">Serve it with nginx: </tspan>')
    lines.append('      <tspan x="450" y="813" font-family="monospace" font-size="24">ssl_certificate, ssl_certificate_key, </tspan>')
    lines.append('      <tspan x="165" y="848" font-family="monospace" font-size="24">ssl_protocols TLSv1.2 TLSv1.3, http2 on</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')

    # ==================== RIGHT PANEL: Real use (orange) ====================
    lines.append('  <!-- ==================== RIGHT PANEL: Real use (orange) ==================== -->')
    lines.append('  <g id="panel-real-use">')
    # EXACTLY 1 occurrence of #db8129 on the card border
    lines.append('    <rect x="1090" y="134" width="470" height="738" rx="14" fill="#e8f1ea" stroke="#db8129" stroke-width="3.5" />')
    # Icon: Hardware Security Module / Vault in green
    lines.append('    <g transform="translate(1120, 155)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <rect x="6" y="6" width="36" height="36" rx="6" />')
    lines.append('      <circle cx="24" cy="24" r="8" />')
    lines.append('      <line x1="24" y1="10" x2="24" y2="16" />')
    lines.append('      <line x1="24" y1="32" x2="24" y2="38" />')
    lines.append('      <line x1="10" y1="24" x2="16" y2="24" />')
    lines.append('      <line x1="32" y1="24" x2="38" y2="24" />')
    lines.append('    </g>')
    lines.append('    <text x="1175" y="186" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Real use</text>')
    lines.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    # Right panel lines (wrapped to ~26-28 chars each)
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
    y_r = 230
    for i, rl in enumerate(r_lines):
        lines.append(f'      <tspan x="1120" y="{y_r + i * 35}">{rl}</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')

    # ==================== PUBLIC CA STRIP ====================
    lines.append('  <!-- ==================== PUBLIC CA STRIP ==================== -->')
    lines.append('  <g id="public-ca-strip">')
    lines.append('    <rect x="40" y="890" width="1520" height="186" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon: Web PKI Globe & Certificate
    lines.append('    <g transform="translate(68, 915)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <circle cx="24" cy="24" r="18" />')
    lines.append('      <ellipse cx="24" cy="24" rx="18" ry="8" />')
    lines.append('      <line x1="24" y1="6" x2="24" y2="42" />')
    lines.append('    </g>')
    lines.append('    <text font-family="sans-serif" font-size="24" fill="#303a36">')
    p_lines = [
        "Let's Encrypt, DigiCert, Google Trust Services check control of the domain (DV) with a DNS or ",
        "HTTP challenge; OV and EV add organisation checks; ACME (RFC 8555) automates renewal through ",
        "certbot, acme.sh, Caddy, cert-manager; Let's Encrypt lasts 90 days; CT logs every public ",
        "certificate; CAA records restrict which CAs may issue"
    ]
    y_p = 938
    for i, pl in enumerate(p_lines):
        lines.append(f'      <tspan x="135" y="{y_p + i * 35}">{pl}</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')

    # ==================== BOTTOM TAKEAWAY BAR ====================
    lines.append('  <!-- ==================== BOTTOM BAR ==================== -->')
    lines.append('  <g id="bottom-bar">')
    lines.append('    <rect x="40" y="1096" width="1520" height="64" rx="10" fill="#207448" />')
    # Key Icon in white
    lines.append('    <g transform="translate(68, 1106)" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <circle cx="15" cy="22" r="9" />')
    lines.append('      <line x1="24" y1="22" x2="42" y2="22" />')
    lines.append('      <line x1="34" y1="22" x2="34" y2="30" />')
    lines.append('      <line x1="40" y1="22" x2="40" y2="28" />')
    lines.append('    </g>')
    lines.append('    <text x="800" y="1138" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">')
    lines.append('      Building one by hand once is the best way to understand what the tools do for you')
    lines.append('    </text>')
    lines.append('  </g>')
    lines.append('')
    lines.append('</svg>')

    return "\n".join(lines)

if __name__ == "__main__":
    svg = generate_svg()
    with open("candidate_private_ca.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("Generated candidate_private_ca.svg successfully!")
