import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1120" width="1600" height="1120">
  <title>Where a secret can leak in Terraform</title>
  <desc>Where a secret can leak in Terraform</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1120" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Where a secret can leak in Terraform</text>

  <!-- ================= ROW 1: THE CORE FLOW (x=50..1550, y=110..390) ================= -->

  <!-- Node 1: Secret passed to a resource (w=470, h=280) -->
  <g id="node-secret">
    <rect x="50" y="110" width="470" height="280" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Lock / Key icon (56x56, stroke 4) -->
    <g transform="translate(257, 126)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="20" width="44" height="32" rx="6" fill="#ffffff" />
      <path d="M 16 20 V 12 A 12 12 0 0 1 40 12 V 20" />
      <circle cx="28" cy="34" r="4" fill="#207448" />
      <line x1="28" y1="38" x2="28" y2="44" />
    </g>
    <!-- Text -->
    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">
      <tspan x="285" y="222">Secret passed to a resource:</tspan>
      <tspan x="285" y="254">Terraform must know the value</tspan>
      <tspan x="285" y="286">to manage the resource, and</tspan>
      <tspan x="285" y="318">whatever it knows it may</tspan>
      <tspan x="285" y="350">write down</tspan>
    </text>
  </g>

  <!-- Arrow 1: Node 1 -> Node 2 -->
  <line x1="520" y1="250" x2="600" y2="250" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Node 2: state file is plain text (w=400, h=280) - Single Orange Stroke -->
  <g id="node-state-file">
    <rect x="600" y="110" width="400" height="280" rx="16" fill="#e8f1ea" stroke="#db8129" stroke-width="3" />
    <!-- File / Unlocked Icon (56x56, stroke 4) -->
    <g transform="translate(772, 130)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 4 L 34 4 L 46 16 L 46 52 L 10 52 Z" fill="#ffffff" />
      <polyline points="34 4 34 16 46 16" />
      <line x1="18" y1="26" x2="38" y2="26" />
      <line x1="18" y1="34" x2="38" y2="34" />
      <line x1="18" y1="42" x2="30" y2="42" />
    </g>
    <!-- Text -->
    <text font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36" text-anchor="middle">
      <tspan x="800" y="240">state file is plain text</tspan>
      <tspan x="800" y="278">unless the provider</tspan>
      <tspan x="800" y="316">protects it</tspan>
    </text>
  </g>

  <!-- Arrow 2: Node 2 -> Node 3 -->
  <line x1="1000" y1="250" x2="1080" y2="250" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Node 3: state bucket (w=470, h=280) -->
  <g id="node-state-bucket">
    <rect x="1080" y="110" width="470" height="280" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Storage Cylinder / Shield Icon (56x56, stroke 4) -->
    <g transform="translate(1287, 126)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="20" ry="8" fill="#ffffff" />
      <path d="M 8 14 V 42 C 8 48 48 48 48 42 V 14" />
      <ellipse cx="28" cy="28" rx="20" ry="8" />
    </g>
    <!-- Text -->
    <text font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">
      <tspan x="1315" y="222">state bucket: private,</tspan>
      <tspan x="1315" y="254">encrypted at rest,</tspan>
      <tspan x="1315" y="286">access controlled; protect</tspan>
      <tspan x="1315" y="318">it as if it held</tspan>
      <tspan x="1315" y="350">every password</tspan>
    </text>
  </g>

  <!-- ================= ROW 2: PATTERNS AND PLAN FILE (y=430..820) ================= -->

  <!-- Left Column: Older pattern (top) + Plan file (bottom) -->
  <g id="left-column">
    <!-- Older pattern card (x=50, y=430, w=720, h=210) -->
    <rect x="50" y="430" width="720" height="210" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Target / Crosshair Icon (56x56, stroke 4) -->
    <g transform="translate(75, 507)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" fill="#ffffff" />
      <circle cx="28" cy="28" r="12" />
      <circle cx="28" cy="28" r="3" fill="#207448" />
      <line x1="28" y1="2" x2="28" y2="10" />
      <line x1="28" y1="46" x2="28" y2="54" />
      <line x1="2" y1="28" x2="10" y2="28" />
      <line x1="46" y1="28" x2="54" y2="28" />
    </g>
    <!-- Text -->
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="155" y="475">generated credentials end up in</tspan>
      <tspan x="155" y="507">state; convenient because Terraform</tspan>
      <tspan x="155" y="539">can read the credential back next</tspan>
      <tspan x="155" y="571">run, and the same convenience makes</tspan>
      <tspan x="155" y="603">the state a target</tspan>
    </text>

    <!-- Plan file card (x=50, y=660, w=720, h=160) -->
    <rect x="50" y="660" width="720" height="160" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Document Warning Icon (56x56, stroke 4) -->
    <g transform="translate(75, 712)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 6 L 32 6 L 44 18 L 44 50 L 8 50 Z" fill="#ffffff" />
      <polyline points="32 6 32 18 44 18" />
      <line x1="26" y1="26" x2="26" y2="36" />
      <circle cx="26" cy="42" r="2" fill="#207448" />
    </g>
    <!-- Text -->
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="155" y="714">a saved plan file holds the full</tspan>
      <tspan x="155" y="750">configuration and may hold sensitive</tspan>
      <tspan x="155" y="786">values: treat it as sensitive</tspan>
    </text>
  </g>

  <!-- Right Column: Newer Nebius Provider Pattern (Container x=830..1550, y=430..820, w=720, h=390) -->
  <g id="right-column-container">
    <rect x="830" y="430" width="720" height="390" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Sub-card 1: write-only arguments (x=855, y=455, w=670, h=100) -->
    <rect x="855" y="455" width="670" height="100" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <!-- Pencil / Edit Icon (56x56, stroke 4) -->
    <g transform="translate(875, 477)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 32 8 L 46 22 L 18 50 L 4 52 L 6 38 Z" fill="#e8f1ea" />
      <line x1="26" y1="14" x2="40" y2="28" />
    </g>
    <text x="955" y="515" font-family="sans-serif" font-size="25" fill="#303a36">write-only arguments in a sensitive object</text>

    <!-- Sub-card 2: ephemeral variables (x=855, y=575, w=670, h=105) -->
    <rect x="855" y="575" width="670" height="105" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <!-- Hourglass / Timer Icon (56x56, stroke 4) -->
    <g transform="translate(875, 599)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 8 L 44 8 L 30 28 L 44 48 L 10 48 L 24 28 Z" fill="#e8f1ea" />
      <line x1="8" y1="8" x2="46" y2="8" />
      <line x1="8" y1="48" x2="46" y2="48" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="955" y="618">ephemeral variables declared</tspan>
      <tspan x="955" y="652">with ephemeral = true</tspan>
    </text>

    <!-- Sub-card 3: ephemeral resources (x=855, y=700, w=670, h=95) -->
    <rect x="855" y="700" width="670" height="95" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <!-- Cloud / Resource Icon (56x56, stroke 4) -->
    <g transform="translate(875, 719)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="42" height="38" rx="6" fill="#e8f1ea" />
      <line x1="6" y1="20" x2="48" y2="20" />
      <circle cx="16" cy="14" r="2.5" fill="#207448" />
      <circle cx="26" cy="14" r="2.5" fill="#207448" />
    </g>
    <text x="955" y="756" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">ephemeral resources</text>
  </g>

  <!-- ================= ROW 3: INTERVIEW MESSAGE (x=50..1550, y=850..960) ================= -->
  <g id="interview-message-card">
    <rect x="50" y="850" width="1500" height="110" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Speech bubble / Dialogue Icon (56x56, stroke 4) -->
    <g transform="translate(80, 877)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 10 C 6 6 10 4 16 4 L 40 4 C 46 4 50 6 50 10 L 50 32 C 50 36 46 38 40 38 L 22 38 L 10 48 L 10 38 L 16 38 C 10 38 6 36 6 32 Z" fill="#ffffff" />
      <line x1="16" y1="16" x2="40" y2="16" />
      <line x1="16" y1="26" x2="32" y2="26" />
    </g>
    <!-- Text -->
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="160" y="897">say what the state holds, who can read it and what you would change;</tspan>
      <tspan x="160" y="933">do not claim the older pattern is safe</tspan>
    </text>
  </g>

  <!-- ================= ROW 4: TAKEAWAY BAR (x=50..1550, y=990..1065) ================= -->
  <g id="takeaway-bar">
    <rect x="50" y="990" width="1500" height="75" rx="14" fill="#207448" />
    <text x="800" y="1038" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">prefer write-only or ephemeral secrets</text>
  </g>

</svg>"""

with open("test_candidate_secrets.svg", "w") as f:
    f.write(svg_content)
print("Saved test_candidate_secrets.svg")
