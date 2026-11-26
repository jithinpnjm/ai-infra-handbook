import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">
  <title>Inside an X.509 certificate: the fields that matter and what each is checked for</title>
  <desc>Visual explanation of X.509 certificate fields, verification checks, and diagnostic OpenSSL commands.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#207448" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Canvas Background -->
  <rect x="0" y="0" width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold, at most two lines, conservative width within 1520px) -->
  <text x="40" y="74" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="40" dy="0">Inside an X.509 certificate: the fields that matter</tspan>
    <tspan x="40" dy="54">and what each is checked for</tspan>
  </text>

  <!-- Analogy Callout Box -->
  <rect x="40" y="165" width="1520" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Passport Outline Icon -->
  <g stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="56" y="172" width="22" height="30" rx="3" />
    <circle cx="67" cy="182" r="4" />
    <line x1="61" y1="192" x2="73" y2="192" />
  </g>
  <text x="96" y="196" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">a passport: a trusted office vouches that this photograph belongs to this name</text>

  <!-- Main Section: Left Card Container (x: 40..720, y: 249..829) -->
  <rect x="40" y="249" width="680" height="580" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <!-- Card Row 1: Subject -->
  <rect x="52" y="258" width="656" height="36" rx="5" fill="#f5f8f5" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="284" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">Subject: who it is for</text>

  <!-- Card Row 2: Issuer -->
  <rect x="52" y="300" width="656" height="36" rx="5" fill="#f5f8f5" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="326" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">Issuer: the CA that signed it</text>

  <!-- Card Row 3: Validity -->
  <rect x="52" y="342" width="656" height="58" rx="5" fill="#f5f8f5" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="367" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="68" dy="0">Validity: notBefore and notAfter,</tspan>
    <tspan x="68" dy="26">checked against the client&apos;s own clock</tspan>
  </text>

  <!-- Card Row 4: Public key -->
  <rect x="52" y="406" width="656" height="36" rx="5" fill="#f5f8f5" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="432" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">Public key</text>

  <!-- Card Row 5: SAN (Single Most Important Item: Orange Highlight) -->
  <rect x="52" y="448" width="656" height="106" rx="5" fill="#fff7ed" stroke="#db8129" stroke-width="2.5" />
  <text x="68" y="473" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="68" dy="0">Subject Alternative Names (SAN):</tspan>
    <tspan x="68" dy="25">the DNS names or IPs the certificate is</tspan>
    <tspan x="68" dy="25">valid for; browsers and modern libraries</tspan>
    <tspan x="68" dy="25">ignore the old CN field</tspan>
  </text>

  <!-- Card Row 6: Key usage and extended key usage -->
  <rect x="52" y="560" width="656" height="56" rx="5" fill="#f5f8f5" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="585" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="68" dy="0">Key usage and extended key usage:</tspan>
    <tspan x="68" dy="26">serverAuth, clientAuth</tspan>
  </text>

  <!-- Card Row 7: Basic constraints -->
  <rect x="52" y="622" width="656" height="36" rx="5" fill="#f5f8f5" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="648" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">Basic constraints: whether this is a CA</text>

  <!-- Card Row 8: Authority and subject key identifiers -->
  <rect x="52" y="664" width="656" height="36" rx="5" fill="#f5f8f5" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="690" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">Authority and subject key identifiers</text>

  <!-- Card Row 9: CRL and OCSP URLs -->
  <rect x="52" y="706" width="656" height="36" rx="5" fill="#f5f8f5" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="732" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">CRL and OCSP URLs</text>

  <!-- Card Row 10: Issuer's signature -->
  <rect x="52" y="748" width="656" height="36" rx="5" fill="#f5f8f5" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="774" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">Issuer&apos;s signature</text>

  <!-- Connecting Arrows from Card to Checks (Horizontal / Orthogonal, No Crossings) -->
  <!-- Arrow 1: Issuer -> chain built... -->
  <line x1="720" y1="318" x2="812" y2="318" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Arrow 2: Validity -> validity dates -->
  <line x1="720" y1="385" x2="812" y2="385" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Arrow 3: SAN -> name against the SAN (Orange) -->
  <line x1="720" y1="499" x2="812" y2="499" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />

  <!-- Arrow 4: Key usage & Basic constraints -> key usage and basic constraints -->
  <line x1="720" y1="608" x2="812" y2="608" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Arrow 5: CRL and OCSP URLs -> revocation status if enabled -->
  <line x1="720" y1="718" x2="812" y2="718" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Arrow 6: Issuer's signature -> each signature -->
  <path d="M 720 766 L 766 766 L 766 799 L 812 799" fill="none" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Right Column: 6 Validation Check Nodes (x: 820..1560, width 740, all gaps exactly 40px) -->

  <!-- Check 1: Chain built from leaf... (y: 249..329, h=80) -->
  <rect x="820" y="249" width="740" height="80" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Outline Chain Icon (52px, green stroke 4) -->
  <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="838" y="278" width="22" height="14" rx="7" transform="rotate(-45 849 285)" />
    <rect x="854" y="294" width="22" height="14" rx="7" transform="rotate(-45 865 301)" />
    <line x1="850" y1="291" x2="860" y2="301" />
  </g>
  <text x="908" y="281" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="908" dy="0">chain built from leaf to trusted root</tspan>
    <tspan x="908" dy="28">using the intermediates the server presents</tspan>
  </text>

  <!-- Gap 40px (329..369) -->

  <!-- Check 2: Validity dates (y: 369..429, h=60) -->
  <rect x="820" y="369" width="740" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Outline Clock Icon (52px, green stroke 4) -->
  <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="862" cy="399" r="18" />
    <polyline points="862,388 862,399 872,399" />
  </g>
  <text x="908" y="407" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">validity dates</text>

  <!-- Gap 40px (429..469) -->

  <!-- Check 3: Name against the SAN (y: 469..529, h=60, Orange Emphasis) -->
  <rect x="820" y="469" width="740" height="60" rx="8" fill="#fff7ed" stroke="#db8129" stroke-width="2.5" />
  <!-- Outline Globe Icon (52px, orange stroke 4) -->
  <g stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="862" cy="499" r="18" />
    <ellipse cx="862" cy="499" rx="8" ry="18" stroke-width="3" />
    <line x1="844" y1="499" x2="880" y2="499" stroke-width="3" />
  </g>
  <text x="908" y="507" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">name against the SAN</text>

  <!-- Gap 40px (529..569) -->

  <!-- Check 4: Key usage and basic constraints (y: 569..629, h=60) -->
  <rect x="820" y="569" width="740" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Outline Key Icon (52px, green stroke 4) -->
  <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="852" cy="599" r="10" />
    <line x1="862" y1="599" x2="880" y2="599" />
    <line x1="872" y1="599" x2="872" y2="607" />
    <line x1="878" y1="599" x2="878" y2="607" />
  </g>
  <text x="908" y="607" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">key usage and basic constraints</text>

  <!-- Gap 40px (629..669) -->

  <!-- Check 5: Revocation status if enabled (y: 669..729, h=60) -->
  <rect x="820" y="669" width="740" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Outline Shield Icon (52px, green stroke 4) -->
  <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 846 686 L 862 680 L 878 686 C 878 702 862 714 862 714 C 862 714 846 702 846 686 Z" />
    <polyline points="854,697 860,703 870,693" stroke-width="3" />
  </g>
  <text x="908" y="707" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">revocation status if enabled</text>

  <!-- Gap 40px (729..769) -->

  <!-- Check 6: Each signature (y: 769..829, h=60) -->
  <rect x="820" y="769" width="740" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Outline Seal Icon (52px, green stroke 4) -->
  <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="862" cy="795" r="12" />
    <polyline points="856,805 852,815 862,810 872,815 868,805" stroke-width="3" />
  </g>
  <text x="908" y="807" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">each signature</text>

  <!-- Gap 40px (829..869) -->

  <!-- Command Strip Container (y: 869..1069, h=200) -->
  <rect x="40" y="869" width="1520" height="200" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

  <!-- Command 1 (y: 879..917, h=38) -->
  <rect x="52" y="879" width="1496" height="38" rx="5" fill="#ffffff" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="906" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="24" fill="#303a36">openssl x509 -in cert.pem -noout -text</text>

  <!-- Command 2 (y: 923..985, h=62, wrapped onto 2 lines to strictly fit width) -->
  <rect x="52" y="923" width="1496" height="62" rx="5" fill="#ffffff" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="948" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="24" fill="#303a36">
    <tspan x="68" dy="0">openssl x509 -noout -subject -issuer -dates -ext </tspan>
    <tspan x="68" dy="26">subjectAltName,basicConstraints,keyUsage,extendedKeyUsage</tspan>
  </text>

  <!-- Command 3 (y: 991..1029, h=38) -->
  <rect x="52" y="991" width="1496" height="38" rx="5" fill="#ffffff" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="1018" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="24" fill="#303a36">openssl x509 -noout -checkend 2592000 (non-zero exit if it expires within 30 days)</text>

  <!-- Command 4 (y: 1035..1061, wait: h=30 or command strip h=208?) -->
  <rect x="52" y="1035" width="1496" height="38" rx="5" fill="#ffffff" stroke="#b2cfb9" stroke-width="1.5" />
  <text x="68" y="1062" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="24" fill="#303a36">openssl verify -CAfile ca.pem -untrusted intermediate.pem leaf.pem</text>

  <!-- Gap 40px (1080..1120) -> let command strip end at 1080! -->

  <!-- Bottom Takeaway Bar (y: 1120..1160, h=40) -->
  <rect x="40" y="1120" width="1520" height="40" rx="8" fill="#207448" />
  <text x="800" y="1148" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Each validation step can fail for a different reason</text>
</svg>"""

with open("output.svg", "w") as f:
    f.write(svg_content)

print("Saved output.svg successfully!")
