import xml.etree.ElementTree as ET

# Exact prompt text
title_text = "How models, what models and accurate models"

col1_wrapped = [
    [
        "why and how things work:",
        "the problem each mechanism",
        "solves, the range of",
        "solutions, how this",
        "implementation applies one"
    ],
    [
        "BGP peer state: a finite",
        "state machine, timers and",
        "keepalives; a session must",
        "miss its hold timer before",
        "routes withdraw, so a",
        "failure takes that long to",
        "show up"
    ],
    [
        "built from protocol",
        "specifications, design",
        "rationales, real designs",
        "and their failures; best",
        "captured as flow charts or",
        "sequence diagrams"
    ],
    [
        "skip them and you get",
        "hunt-and-peck",
        "troubleshooting from",
        "fragments of past incidents"
    ]
]

col2_wrapped = [
    [
        "what is normal here: the",
        "signal path of each",
        "application, the baseline",
        "(traffic by time of day,",
        "SPF run times, jitter and",
        "delay per application, ECMP",
        "balance, PFC and ECN rates,",
        "temperatures, optic power),",
        "the source of truth for",
        "configuration, expected",
        "convergence time and loss",
        "on link failure, security",
        "boundaries"
    ],
    [
        "write down the normal",
        "retransmit rate, latency",
        "and load on one leaf switch"
    ],
    [
        "radar technician: a DC",
        "ohmmeter reads an inductor",
        "as a short, so it could not",
        "see the inductor failure in",
        "parallel with the shorted",
        "resistor; every tool has",
        "blind spots"
    ]
]

col3_wrapped = [
    [
        "accuracy means fit to",
        "purpose, not completeness"
    ],
    [
        "OSI is good for interfaces",
        "and building a stack, poor",
        "for what happens where and",
        "why"
    ],
    [
        "RINA treats error control,",
        "flow control and",
        "multiplexing as recurring",
        "at each scope"
    ],
    [
        "different questions need",
        "different models: path,",
        "control plane, queues,",
        "energy and thermal,",
        "application protocol"
    ]
]

orig_labels = [
    "How models, what models and accurate models",
    "How models (theory)",
    "why and how things work: the problem each mechanism solves, the range of solutions, how this implementation applies one",
    "BGP peer state: a finite state machine, timers and keepalives; a session must miss its hold timer before routes withdraw, so a failure takes that long to show up",
    "built from protocol specifications, design rationales, real designs and their failures; best captured as flow charts or sequence diagrams",
    "skip them and you get hunt-and-peck troubleshooting from fragments of past incidents",
    "What models (state of your system)",
    "what is normal here: the signal path of each application, the baseline (traffic by time of day, SPF run times, jitter and delay per application, ECMP balance, PFC and ECN rates, temperatures, optic power), the source of truth for configuration, expected convergence time and loss on link failure, security boundaries",
    "write down the normal retransmit rate, latency and load on one leaf switch",
    "radar technician: a DC ohmmeter reads an inductor as a short, so it could not see the inductor failure in parallel with the shorted resistor; every tool has blind spots",
    "Accurate models (fit to purpose)",
    "accuracy means fit to purpose, not completeness",
    "OSI is good for interfaces and building a stack, poor for what happens where and why",
    "RINA treats error control, flow control and multiplexing as recurring at each scope",
    "different questions need different models: path, control plane, queues, energy and thermal, application protocol",
    "You cannot recognise broken without knowing normal"
]

print("Checking reconstruct...")
reconstructed = [title_text, "How models (theory)"]
for c in col1_wrapped:
    reconstructed.append(" ".join(c))
reconstructed.append("What models (state of your system)")
for c in col2_wrapped:
    reconstructed.append(" ".join(c))
reconstructed.append("Accurate models (fit to purpose)")
for c in col3_wrapped:
    reconstructed.append(" ".join(c))
reconstructed.append("You cannot recognise broken without knowing normal")

assert len(reconstructed) == len(orig_labels), f"Length mismatch: {len(reconstructed)} vs {len(orig_labels)}"
for i in range(len(orig_labels)):
    assert reconstructed[i] == orig_labels[i], f"Mismatch at {i}:\n  '{reconstructed[i]}'\n  '{orig_labels[i]}'"

print("All 16 labels MATCH EXACTLY 100%!")

# Assemble SVG
svg_parts = []
svg_parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
svg_parts.append('  <title>How models, what models and accurate models</title>')
svg_parts.append('  <desc>Visual explanation comparing How models (theory), What models (state of your system), and Accurate models (fit to purpose) in technical architecture and troubleshooting.</desc>')

# Background
svg_parts.append('  <!-- Canvas Background -->')
svg_parts.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')

# Main Title
svg_parts.append('  <!-- Main Title -->')
svg_parts.append('  <text x="800" y="55" font-size="48" font-weight="bold" fill="#207448" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif">How models, what models and accurate models</text>')

cols = [
    {"x": 40, "w": 480, "title1": "How models", "title2": "(theory)"},
    {"x": 560, "w": 480, "title1": "What models", "title2": "(state of your system)"},
    {"x": 1080, "w": 480, "title1": "Accurate models", "title2": "(fit to purpose)"}
]

for col in cols:
    svg_parts.append(f'  <!-- Column Background: {col["title1"]} -->')
    svg_parts.append(f'  <rect x="{col["x"]}" y="85" width="{col["w"]}" height="994" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

# Icons
# Col 1 Gear icon
svg_parts.append('  <!-- Column 1 Icon: Mechanism / Gears -->')
svg_parts.append('  <g transform="translate(252, 102)" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">')
svg_parts.append('    <circle cx="28" cy="28" r="10" />')
svg_parts.append('    <path d="M 28 4 L 28 10 M 28 46 L 28 52 M 4 28 L 10 28 M 46 28 L 52 28 M 11 11 L 15 15 M 41 41 L 45 45 M 11 45 L 15 41 M 41 11 L 45 15" stroke-width="4.5" />')
svg_parts.append('    <circle cx="28" cy="28" r="18" stroke-width="3.5" />')
svg_parts.append('  </g>')

# Col 2 Monitor icon
svg_parts.append('  <!-- Column 2 Icon: Telemetry Monitor / Signal -->')
svg_parts.append('  <g transform="translate(772, 102)" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">')
svg_parts.append('    <rect x="4" y="6" width="48" height="34" rx="4" />')
svg_parts.append('    <path d="M 8 23 H 17 L 22 13 L 28 33 L 34 18 L 38 23 H 48" />')
svg_parts.append('    <line x1="28" y1="40" x2="28" y2="49" />')
svg_parts.append('    <line x1="18" y1="49" x2="38" y2="49" />')
svg_parts.append('  </g>')

# Col 3 Target icon
svg_parts.append('  <!-- Column 3 Icon: Fit to Purpose Target -->')
svg_parts.append('  <g transform="translate(1292, 102)" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">')
svg_parts.append('    <circle cx="28" cy="28" r="22" />')
svg_parts.append('    <circle cx="28" cy="28" r="12" />')
svg_parts.append('    <circle cx="28" cy="28" r="3" fill="#207448" />')
svg_parts.append('    <line x1="28" y1="2" x2="28" y2="10" />')
svg_parts.append('    <line x1="28" y1="46" x2="28" y2="54" />')
svg_parts.append('    <line x1="2" y1="28" x2="10" y2="28" />')
svg_parts.append('    <line x1="46" y1="28" x2="54" y2="28" />')
svg_parts.append('  </g>')

# Column Titles
for col in cols:
    cx = col["x"] + col["w"] // 2
    svg_parts.append(f'  <text x="{cx}" y="188" font-size="30" font-weight="bold" fill="#207448" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif">')
    svg_parts.append(f'    <tspan x="{cx}">{col["title1"]}</tspan>')
    svg_parts.append(f'    <tspan x="{cx}" dy="34">{col["title2"]}</tspan>')
    svg_parts.append('  </text>')

# Card definitions
c1_cards = [
    {"lines": col1_wrapped[0], "y": 245, "h": 184, "pad_top": 20},
    {"lines": col1_wrapped[1], "y": 438, "h": 244, "pad_top": 20},
    {"lines": col1_wrapped[2], "y": 690, "h": 214, "pad_top": 20},
    {"lines": col1_wrapped[3], "y": 913, "h": 154, "pad_top": 20}
]

c2_cards = [
    {"lines": col2_wrapped[0], "y": 245, "h": 424, "pad_top": 20},
    {"lines": col2_wrapped[1], "y": 684, "h": 124, "pad_top": 20},
    {"lines": col2_wrapped[2], "y": 823, "h": 244, "pad_top": 20, "orange": True}
]

c3_cards = [
    {"lines": col3_wrapped[0], "y": 245, "h": 134, "pad_top": 40},
    {"lines": col3_wrapped[1], "y": 404, "h": 194, "pad_top": 40},
    {"lines": col3_wrapped[2], "y": 624, "h": 194, "pad_top": 40},
    {"lines": col3_wrapped[3], "y": 843, "h": 224, "pad_top": 40}
]

def render_cards(col_x, cards, col_num):
    card_x = col_x + 16
    card_w = 448
    text_x = card_x + 24
    for idx, c in enumerate(cards):
        cy = c["y"]
        ch = c["h"]
        pad_t = c["pad_top"]
        is_orange = c.get("orange", False)
        
        svg_parts.append(f'  <!-- Col {col_num} Card {idx+1} -->')
        if is_orange:
            # Highlighted orange card
            svg_parts.append(f'  <rect x="{card_x}" y="{cy}" width="{card_w}" height="{ch}" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
            svg_parts.append(f'  <path d="M {card_x} {cy+10} Q {card_x} {cy} {card_x+10} {cy} L {card_x+10} {cy} L {card_x+10} {cy+ch} L {card_x+10} {cy+ch} Q {card_x} {cy+ch} {card_x} {cy+ch-10} Z" fill="#db8129" />')
        else:
            svg_parts.append(f'  <rect x="{card_x}" y="{cy}" width="{card_w}" height="{ch}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
        
        first_y = cy + pad_t + 20
        svg_parts.append(f'  <text x="{text_x}" y="{first_y}" font-size="24" fill="#303a36" font-family="system-ui, -apple-system, sans-serif">')
        for l_idx, line in enumerate(c["lines"]):
            if l_idx == 0:
                svg_parts.append(f'    <tspan x="{text_x}">{line}</tspan>')
            else:
                svg_parts.append(f'    <tspan x="{text_x}" dy="30">{line}</tspan>')
        svg_parts.append('  </text>')

render_cards(40, c1_cards, 1)
render_cards(560, c2_cards, 2)
render_cards(1080, c3_cards, 3)

# Bottom Takeaway Bar
svg_parts.append('  <!-- Bottom Takeaway Bar -->')
svg_parts.append('  <rect x="40" y="1092" width="1520" height="78" rx="12" fill="#207448" />')
svg_parts.append('  <text x="800" y="1141" font-size="30" font-weight="bold" fill="#ffffff" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif">You cannot recognise broken without knowing normal</text>')

svg_parts.append('</svg>')

full_svg = "\n".join(svg_parts)
with open("models_infographic.svg", "w") as f:
    f.write(full_svg)

tree = ET.parse("models_infographic.svg")
print("Successfully generated and validated models_infographic.svg!")
