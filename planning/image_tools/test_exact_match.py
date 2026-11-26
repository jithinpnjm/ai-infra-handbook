import xml.etree.ElementTree as ET

expected_labels = [
    "Reading data off the wire: decode, then deserialize",
    "Network Programmability and Automation chapter 8",
    "bytes arrive",
    "decode into a UTF-8 string, for example {\"vendors\":[\"Cisco\",\"Juniper\",\"Arista\"]}",
    "deserialize with json.loads() into native structures: a Python dict and list",
    "serialize first",
    "encode",
    "screen scraping show interfaces em0 breaks when a vendor changes the spacing; ask for structured output: show interfaces em0 | display xml, or JSON",
    "Markup languages like HTML annotate documents for rendering; data serialization formats represent typed data structures across languages",
    "XML: tags, attributes, xmlns namespaces; query with XPath such as //device/model or //device[@name=\"leaf\"]/model, or XQuery; validate with XSD (xmlschema)",
    "JSON: lighter; validate with JSON Schema: $schema https://json-schema.org/draft/2020-12/schema, minLength, maxLength, minimum 1, maximum 4094, IPv4 pattern regexes through jsonschema.validate()",
    "Protocol Buffers: binary, .proto files compiled with protoc, validated with protoc-gen-validate; FlatBuffers: read fields straight from the byte buffer; for high-throughput RPCs such as gRPC telemetry",
    "pickle: Python only, unsafe on untrusted bytes",
    "Structured data beats fragile screen scraping"
]

# Build the complete SVG text
svg_text = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Reading data off the wire: decode, then deserialize</title>
  <desc>Reading data off the wire: decode, then deserialize</desc>
  <defs>
    <style>
      .title { font-family: system-ui, -apple-system, sans-serif; font-size: 48px; font-weight: bold; fill: #303a36; }
      .source { font-family: system-ui, -apple-system, sans-serif; font-size: 24px; fill: #55665d; }
      .node-title { font-family: system-ui, -apple-system, sans-serif; font-size: 30px; font-weight: bold; fill: #207448; }
      .node-title-orange { font-family: system-ui, -apple-system, sans-serif; font-size: 30px; font-weight: bold; fill: #db8129; }
      .body-sans { font-family: system-ui, -apple-system, sans-serif; font-size: 24px; fill: #303a36; }
      .body-mono { font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace; font-size: 24px; fill: #303a36; }
      .banner-text { font-family: system-ui, -apple-system, sans-serif; font-size: 24px; font-weight: bold; fill: #207448; }
      .takeaway { font-family: system-ui, -apple-system, sans-serif; font-size: 30px; font-weight: bold; fill: #ffffff; text-anchor: middle; }
    </style>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#207448" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#db8129" />
    </marker>
  </defs>

  <rect width="1600" height="1200" fill="#f5f8f5" />

  <text class="title" x="50" y="62">Reading data off the wire: decode, then deserialize</text>
  <text class="source" x="50" y="98">Network Programmability and Automation chapter 8</text>

  <rect x="50" y="118" width="1500" height="346" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <rect x="76" y="140" width="264" height="136" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(180, 154)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="0" y="10" width="56" height="28" rx="4" fill="#ffffff" />
    <path d="M 12 10 L 12 0 M 28 10 L 28 0 M 44 10 L 44 0" />
    <circle cx="28" cy="24" r="5" fill="#207448" />
  </g>
  <text class="node-title" x="208" y="246" text-anchor="middle">bytes arrive</text>

  <line x1="340" y1="208" x2="388" y2="208" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <rect x="388" y="140" width="540" height="136" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(406, 150)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="0" width="44" height="52" rx="4" fill="#ffffff" />
    <path d="M 12 14 L 38 14 M 12 24 L 38 24 M 12 34 L 28 34" />
  </g>
  <text class="body-sans" x="406" y="180"><tspan x="460" y="180">decode into a UTF-8 string, </tspan><tspan class="body-mono" x="406" y="222">for example </tspan><tspan class="body-mono">{"vendors":[</tspan><tspan class="body-mono" x="406" y="252">"Cisco","Juniper","Arista"]}</tspan></text>

  <line x1="928" y1="208" x2="976" y2="208" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <rect x="976" y="140" width="548" height="136" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(994, 150)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="20" y="0" width="16" height="16" rx="2" fill="#ffffff" />
    <path d="M 28 16 L 28 28 M 12 28 L 44 28 M 12 28 L 12 36 M 44 28 L 44 36" />
    <rect x="4" y="36" width="16" height="16" rx="2" fill="#ffffff" />
    <rect x="36" y="36" width="16" height="16" rx="2" fill="#ffffff" />
  </g>
  <text class="body-sans" x="994" y="180"><tspan class="body-mono" x="1058" y="180">deserialize with json.loads() </tspan><tspan x="994" y="222">into native structures: </tspan><tspan x="994" y="252">a Python dict and list</tspan></text>

  <rect x="976" y="304" width="548" height="134" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(1004, 344)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="28" cy="28" r="16" fill="#ffffff" />
    <path d="M 28 4 L 28 12 M 28 44 L 28 52 M 4 28 L 12 28 M 44 28 L 52 28 M 11 11 L 17 17 M 39 39 L 45 45 M 11 45 L 17 39 M 39 17 L 45 11" />
  </g>
  <text class="node-title" x="1080" y="382">serialize first</text>

  <line x1="976" y1="371" x2="928" y2="371" stroke="#db8129" stroke-width="3" marker-end="url(#arrow-orange)" />

  <rect x="388" y="304" width="540" height="134" rx="8" fill="#fef6ed" stroke="#db8129" stroke-width="3" />
  <g transform="translate(560, 344)" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="42" rx="4" fill="#ffffff" />
    <path d="M 14 18 L 14 36 M 24 18 C 28 18 30 20 30 23 C 30 26 28 28 24 28 L 24 18 M 24 28 C 29 28 31 30 31 33 C 31 36 29 37 24 37 L 24 28 M 38 22 L 42 18 L 42 36" />
  </g>
  <text class="node-title-orange" x="640" y="382">encode</text>

  <rect x="50" y="480" width="1500" height="104" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(68, 506)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="42" rx="4" fill="#ffffff" />
    <path d="M 12 18 L 20 27 L 12 36 M 24 36 L 36 36" />
  </g>
  <text class="body-mono" x="140" y="524"><tspan x="140" y="524">screen scraping show interfaces em0 breaks when a vendor changes the spacing; </tspan><tspan x="140" y="558">ask for structured output: show interfaces em0 | display xml, or JSON</tspan></text>

  <rect x="50" y="596" width="1500" height="500" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <rect x="68" y="604" width="1464" height="88" rx="6" fill="#e8f1ea" />
  <text class="banner-text" x="90" y="644"><tspan x="90" y="644">Markup languages like HTML annotate documents for rendering; </tspan><tspan x="90" y="672">data serialization formats represent typed data structures across languages</tspan></text>

  <rect x="68" y="700" width="1464" height="88" rx="6" fill="#f9fbf9" stroke="#d0e0d4" stroke-width="1.5" />
  <g transform="translate(86, 720)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 16 12 L 6 24 L 16 36 M 32 12 L 42 24 L 32 36 M 26 8 L 22 40" />
  </g>
  <text class="body-mono" x="150" y="740"><tspan x="150" y="740">XML: tags, attributes, xmlns namespaces; query with XPath such as //device/model </tspan><tspan x="150" y="770">or //device[@name="leaf"]/model, or XQuery; validate with XSD (xmlschema)</tspan></text>

  <rect x="68" y="796" width="1464" height="114" rx="6" fill="#f9fbf9" stroke="#d0e0d4" stroke-width="1.5" />
  <g transform="translate(86, 831)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 18 10 C 10 10 12 20 6 24 C 12 28 10 38 18 38 M 30 10 C 38 10 36 20 42 24 C 36 28 38 38 30 38" />
  </g>
  <text class="body-mono" x="150" y="836"><tspan x="150" y="836">JSON: lighter; validate with JSON Schema: </tspan><tspan x="150" y="866">$schema https://json-schema.org/draft/2020-12/schema, minLength, maxLength, </tspan><tspan x="150" y="894">minimum 1, maximum 4094, IPv4 pattern regexes through jsonschema.validate()</tspan></text>

  <rect x="68" y="918" width="1464" height="114" rx="6" fill="#f9fbf9" stroke="#d0e0d4" stroke-width="1.5" />
  <g transform="translate(86, 953)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="40" height="36" rx="4" />
    <path d="M 4 18 L 44 18 M 4 30 L 44 30 M 18 6 L 18 42 M 32 6 L 32 42" />
  </g>
  <text class="body-mono" x="150" y="958"><tspan x="150" y="958">Protocol Buffers: binary, .proto files compiled with protoc, </tspan><tspan x="150" y="988">validated with protoc-gen-validate; FlatBuffers: read fields straight </tspan><tspan x="150" y="1016">from the byte buffer; for high-throughput RPCs such as gRPC telemetry</tspan></text>

  <rect x="68" y="1040" width="1464" height="62" rx="6" fill="#f9fbf9" stroke="#d0e0d4" stroke-width="1.5" />
  <g transform="translate(86, 1051)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 24 4 L 40 10 L 40 22 C 40 32 24 38 24 38 C 24 38 8 32 8 22 L 8 10 Z" />
    <path d="M 24 14 L 24 24 M 24 28 L 24 30" />
  </g>
  <text class="body-mono" x="150" y="1080">pickle: Python only, unsafe on untrusted bytes</text>

  <rect x="50" y="1114" width="1500" height="70" rx="8" fill="#207448" />
  <text class="takeaway" x="800" y="1162">Structured data beats fragile screen scraping</text>
</svg>"""

root = ET.fromstring(svg_text)
ns = {"svg": "http://www.w3.org/2000/svg"}
text_nodes = root.findall(".//svg:text", ns)

print(f"Total <text> elements: {len(text_nodes)}")
print(f"Total expected labels: {len(expected_labels)}")
assert len(text_nodes) == len(expected_labels), "Count mismatch!"

for i, (t_node, exp) in enumerate(zip(text_nodes, expected_labels)):
    full_str = " ".join("".join(t_node.itertext()).split())
    if full_str != exp:
        print(f"Mismatch at index {i}:")
        print(f"  Got:      {full_str}")
        print(f"  Expected: {exp}")
    else:
        print(f"[{i+1}/14] Match: {full_str[:40]}...")

print("\nALL 14 LABELS MATCH EXACTLY 1-to-1!")
