import xml.etree.ElementTree as ET
import re

def build_svg():
    # Colors
    bg = "#f5f8f5"
    text_color = "#303a36"
    main_green = "#207448"
    light_green = "#e8f1ea"
    orange = "#db8129"

    # SVG layout builder
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>Reading data off the wire: decode, then deserialize</title>')
    svg.append('  <desc>Reading data off the wire: decode, then deserialize</desc>')
    svg.append('')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append(f'      <path d="M 2 3 L 16 9 L 2 15 Z" fill="{main_green}" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    svg.append('')
    svg.append(f'  <!-- Canvas Background -->')
    svg.append(f'  <rect width="1600" height="1200" fill="{bg}" />')
    svg.append('')

    # Title & Source label
    svg.append('  <!-- Title (48px bold) -->')
    svg.append(f'  <text x="800" y="54" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="{text_color}">Reading data off the wire: decode, then deserialize</text>')
    svg.append('')
    svg.append('  <!-- Source label (24px) -->')
    svg.append(f'  <text x="800" y="96" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{main_green}">Network Programmability and Automation chapter 8</text>')
    svg.append('')

    # Flow Section
    # Outer panel for flow section: y=118, h=334 (x=40..1560)
    svg.append('  <!-- Flow Container -->')
    svg.append(f'  <rect x="40" y="118" width="1520" height="336" rx="14" fill="{light_green}" stroke="{main_green}" stroke-width="2" />')
    svg.append('')

    # Receive Flow: Row 1 (y=138..278, h=140)
    # Box 1: "bytes arrive" (Col 1: x=60..390, w=330, h=136)
    # Box 2: "decode into a UTF-8 string, for example {"vendors":["Cisco","Juniper","Arista"]}" (Col 2: x=460..1010, w=550, h=136)
    # Box 3: "deserialize with json.loads() into native structures: a Python dict and list" (Col 3: x=1080..1540, w=460, h=136)

    # Box 1: bytes arrive
    svg.append('  <!-- Node 1: bytes arrive -->')
    svg.append(f'  <rect x="60" y="136" width="330" height="136" rx="10" fill="#ffffff" stroke="{main_green}" stroke-width="2.5" />')
    # Icon for bytes arrive: wire / bits stream (56px)
    svg.append(f'  <g transform="translate(78, 176)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <line x1="4" y1="28" x2="52" y2="28" />')
    svg.append('    <circle cx="16" cy="14" r="5" fill="#ffffff" />')
    svg.append('    <circle cx="40" cy="42" r="5" fill="#ffffff" />')
    svg.append('    <polyline points="28,10 36,28 20,28 28,46" />')
    svg.append('  </g>')
    svg.append(f'  <text x="245" y="214" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">bytes arrive</text>')
    svg.append('')

    # Arrow 1: Box 1 to Box 2
    svg.append('  <!-- Arrow 1: bytes arrive -> decode -->')
    svg.append(f'  <line x1="390" y1="204" x2="458" y2="204" stroke="{main_green}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append('')

    # Box 2: decode
    svg.append('  <!-- Node 2: decode into a UTF-8 string -->')
    svg.append(f'  <rect x="460" y="136" width="550" height="136" rx="10" fill="#ffffff" stroke="{main_green}" stroke-width="2.5" />')
    # Icon for decode: document text / charset (56px)
    svg.append(f'  <g transform="translate(476, 176)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="8" y="6" width="40" height="44" rx="4" />')
    svg.append('    <line x1="16" y1="18" x2="40" y2="18" stroke-width="3" />')
    svg.append('    <line x1="16" y1="28" x2="36" y2="28" stroke-width="3" />')
    svg.append('    <line x1="16" y1="38" x2="30" y2="38" stroke-width="3" />')
    svg.append('  </g>')
    # Text for Box 2: decode
    svg.append(f'  <text x="765" y="174" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append('    <tspan x="765" dy="0">decode into a UTF-8 string, </tspan>')
    svg.append('    <tspan x="765" dy="32">for example </tspan>')
    svg.append('    <tspan x="765" dy="32">{"vendors":["Cisco",</tspan>')
    svg.append('    <tspan x="765" dy="32">"Juniper","Arista"]}</tspan>')
    svg.append('  </text>')
    svg.append('')

    # Arrow 2: Box 2 to Box 3
    svg.append('  <!-- Arrow 2: decode -> deserialize -->')
    svg.append(f'  <line x1="1010" y1="204" x2="1078" y2="204" stroke="{main_green}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append('')

    # Box 3: deserialize
    svg.append('  <!-- Node 3: deserialize with json.loads() -->')
    svg.append(f'  <rect x="1080" y="136" width="460" height="136" rx="10" fill="#ffffff" stroke="{main_green}" stroke-width="2.5" />')
    # Icon for deserialize: python structures / tree / gear (56px)
    svg.append(f'  <g transform="translate(1096, 176)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="6" y="8" width="20" height="18" rx="3" />')
    svg.append('    <rect x="30" y="8" width="20" height="18" rx="3" />')
    svg.append('    <rect x="18" y="30" width="20" height="18" rx="3" />')
    svg.append('    <line x1="16" y1="26" x2="28" y2="30" />')
    svg.append('    <line x1="40" y1="26" x2="28" y2="30" />')
    svg.append('  </g>')
    # Text for Box 3: deserialize
    svg.append(f'  <text x="1335" y="186" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append('    <tspan x="1335" dy="0">deserialize with json.loads() </tspan>')
    svg.append('    <tspan x="1335" dy="34">into native structures: </tspan>')
    svg.append('    <tspan x="1335" dy="34">a Python dict and list</tspan>')
    svg.append('  </text>')
    svg.append('')

    # Send Flow: Row 2 (y=296..432, h=136)
    # Box 4: serialize first (Col 3: x=1080..1540, w=460, h=136)
    # Arrow 3: Box 4 to Box 5 (pointing LEFT: x1=1080 to x2=1012, y=364)
    # Box 5: encode (Col 2: x=460..1010, w=550, h=136) - ORANGE highlight!

    # Box 4: serialize first
    svg.append('  <!-- Node 4: serialize first -->')
    svg.append(f'  <rect x="1080" y="296" width="460" height="136" rx="10" fill="#ffffff" stroke="{main_green}" stroke-width="2.5" />')
    # Icon for serialize: box / pack / arrow outward (56px)
    svg.append(f'  <g transform="translate(1120, 336)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="8" y="10" width="40" height="36" rx="4" />')
    svg.append('    <line x1="8" y1="22" x2="48" y2="22" />')
    svg.append('    <polyline points="22,32 28,38 34,32" />')
    svg.append('    <line x1="28" y1="22" x2="28" y2="38" />')
    svg.append('  </g>')
    svg.append(f'  <text x="1340" y="374" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">serialize first</text>')
    svg.append('')

    # Arrow 3: Box 4 to Box 5 (Send reverses it, pointing left!)
    svg.append('  <!-- Arrow 3: serialize first -> encode (pointing left) -->')
    svg.append(f'  <line x1="1080" y1="364" x2="1012" y2="364" stroke="{main_green}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append('')

    # Box 5: encode (ORANGE item!)
    svg.append('  <!-- Node 5: encode (orange) -->')
    svg.append(f'  <rect x="460" y="296" width="550" height="136" rx="10" fill="#ffffff" stroke="{orange}" stroke-width="3" />')
    # Icon for encode: transmission / encoding beam (56px, green stroke to keep orange count exactly 1!)
    svg.append(f'  <g transform="translate(540, 336)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="28" cy="28" r="20" />')
    svg.append('    <line x1="16" y1="28" x2="40" y2="28" />')
    svg.append('    <line x1="28" y1="16" x2="28" y2="40" />')
    svg.append('  </g>')
    svg.append(f'  <text x="765" y="374" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">encode</text>')
    svg.append('')

    # Strip Section: Screen scraping warning
    # y=474, h=96 (x=40..1560)
    svg.append('  <!-- Strip: screen scraping -->')
    svg.append(f'  <rect x="40" y="474" width="1520" height="96" rx="10" fill="#ffffff" stroke="{main_green}" stroke-width="2" />')
    # Terminal warning icon (56px)
    svg.append(f'  <g transform="translate(60, 494)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="6" y="8" width="44" height="40" rx="4" />')
    svg.append('    <polyline points="14,24 22,30 14,36" stroke-width="3" />')
    svg.append('    <line x1="26" y1="36" x2="38" y2="36" stroke-width="3" />')
    svg.append('  </g>')
    svg.append(f'  <text x="820" y="515" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append('    <tspan x="820" dy="0">screen scraping show interfaces em0 breaks when a vendor changes the spacing; </tspan>')
    svg.append('    <tspan x="820" dy="34">ask for structured output: show interfaces em0 | display xml, or JSON</tspan>')
    svg.append('  </text>')
    svg.append('')

    # Format comparison table
    # y=590..1100 (x=40..1560)
    # Intro card: y=590, h=66
    # Row 1 (XML): y=672, h=96
    # Row 2 (JSON): y=782, h=108
    # Row 3 (Protobuf): y=904, h=108
    # Row 4 (pickle): y=1026, h=74

    # Intro card
    svg.append('  <!-- Table Intro Card -->')
    svg.append(f'  <rect x="40" y="590" width="1520" height="68" rx="8" fill="{light_green}" stroke="{main_green}" stroke-width="2" />')
    svg.append(f'  <text x="800" y="632" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{text_color}">')
    svg.append('    <tspan x="800" dy="0">Markup languages like HTML annotate documents for rendering; </tspan>')
    svg.append('    <tspan x="800" dy="30">data serialization formats represent typed data structures across languages</tspan>')
    svg.append('  </text>')
    svg.append('')

    # XML Row
    svg.append('  <!-- XML Row -->')
    svg.append(f'  <rect x="40" y="674" width="1520" height="96" rx="8" fill="#ffffff" stroke="{main_green}" stroke-width="1.5" />')
    svg.append(f'  <text x="800" y="715" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append('    <tspan x="800" dy="0">XML: tags, attributes, xmlns namespaces; query with XPath such as //device/model </tspan>')
    svg.append('    <tspan x="800" dy="34">or //device[@name="leaf"]/model, or XQuery; validate with XSD (xmlschema)</tspan>')
    svg.append('  </text>')
    svg.append('')

    # JSON Row
    svg.append('  <!-- JSON Row -->')
    svg.append(f'  <rect x="40" y="784" width="1520" height="106" rx="8" fill="#ffffff" stroke="{main_green}" stroke-width="1.5" />')
    svg.append(f'  <text x="800" y="820" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append('    <tspan x="800" dy="0">JSON: lighter; validate with JSON Schema: </tspan>')
    svg.append('    <tspan x="800" dy="32">$schema https://json-schema.org/draft/2020-12/schema, minLength, maxLength, </tspan>')
    svg.append('    <tspan x="800" dy="32">minimum 1, maximum 4094, IPv4 pattern regexes through jsonschema.validate()</tspan>')
    svg.append('  </text>')
    svg.append('')

    # Protocol Buffers / FlatBuffers Row
    svg.append('  <!-- Protobuf Row -->')
    svg.append(f'  <rect x="40" y="904" width="1520" height="106" rx="8" fill="#ffffff" stroke="{main_green}" stroke-width="1.5" />')
    svg.append(f'  <text x="800" y="940" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append('    <tspan x="800" dy="0">Protocol Buffers: binary, .proto files compiled with protoc, validated with protoc-gen-validate; </tspan>')
    svg.append('    <tspan x="800" dy="32">FlatBuffers: read fields straight from the byte buffer; </tspan>')
    svg.append('    <tspan x="800" dy="32">for high-throughput RPCs such as gRPC telemetry</tspan>')
    svg.append('  </text>')
    svg.append('')

    # pickle Row
    svg.append('  <!-- pickle Row -->')
    svg.append(f'  <rect x="40" y="1024" width="1520" height="74" rx="8" fill="#ffffff" stroke="{main_green}" stroke-width="1.5" />')
    svg.append(f'  <text x="800" y="1068" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_color}">pickle: Python only, unsafe on untrusted bytes</text>')
    svg.append('')

    # Bottom takeaway bar
    # y=1120, h=62 (x=40..1560)
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append(f'  <rect x="40" y="1120" width="1520" height="62" rx="10" fill="{main_green}" />')
    svg.append(f'  <text x="800" y="1160" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Structured data beats fragile screen scraping</text>')
    svg.append('</svg>')

    return "\n".join(svg)

content = build_svg()
with open("test_candidate_build.svg", "w") as f:
    f.write(content)
print("Wrote test_candidate_build.svg successfully!")
