const fs = require('fs');

const W = [230, 280, 200, 140, 140, 230];
const c = [155, 460, 765, 1025, 1220, 1445];

// Generate the SVG string
function generateSVG() {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>How a lookup actually works</title>
  <desc>A sequence diagram showing DNS resolution from application getaddrinfo through stub resolver, recursive resolver, root server, .com TLD server, and example.com authoritative server.</desc>
  <defs>
    <!-- Arrowhead markers -->
    <!-- Green marker right -->
    <marker id="arrow-green-right" viewBox="0 0 18 18" refX="18" refY="9" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 0 2 L 18 9 L 0 16 z" fill="#207448" />
    </marker>
    <!-- Green marker left -->
    <marker id="arrow-green-left" viewBox="0 0 18 18" refX="0" refY="9" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 18 2 L 0 9 L 18 16 z" fill="#207448" />
    </marker>
    <!-- Orange marker left (for step 8) -->
    <marker id="arrow-orange-left" viewBox="0 0 18 18" refX="0" refY="9" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 18 2 L 0 9 L 18 16 z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Diagram Title -->
  <text x="800" y="52" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">How a lookup actually works</text>

  <!-- Swimlane lifelines -->
  <!-- Lane 1: Application -->
  <line x1="${c[0]}" y1="255" x2="${c[0]}" y2="1160" stroke="#c8d6ce" stroke-width="3" stroke-dasharray="8 8" />
  <!-- Lane 2: Stub resolver -->
  <line x1="${c[1]}" y1="255" x2="${c[1]}" y2="1160" stroke="#c8d6ce" stroke-width="3" stroke-dasharray="8 8" />
  <!-- Lane 3: Recursive resolver -->
  <line x1="${c[2]}" y1="255" x2="${c[2]}" y2="1160" stroke="#c8d6ce" stroke-width="3" stroke-dasharray="8 8" />
  <!-- Lane 4: Root server -->
  <line x1="${c[3]}" y1="255" x2="${c[3]}" y2="1160" stroke="#c8d6ce" stroke-width="3" stroke-dasharray="8 8" />
  <!-- Lane 5: .com TLD server -->
  <line x1="${c[4]}" y1="255" x2="${c[4]}" y2="1160" stroke="#c8d6ce" stroke-width="3" stroke-dasharray="8 8" />
  <!-- Lane 6: example.com authoritative -->
  <line x1="${c[5]}" y1="255" x2="${c[5]}" y2="1160" stroke="#c8d6ce" stroke-width="3" stroke-dasharray="8 8" />

  <!-- PARTICIPANT HEADERS -->

  <!-- Node 1: Application -->
  <g id="node-app">
    <rect x="${c[0] - W[0]/2}" y="75" width="${W[0]}" height="175" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <!-- Window Outline Icon (56x56) at center 155, top 92 -->
    <g transform="translate(${c[0] - 28}, 92)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="52" height="52" rx="6" />
      <line x1="2" y1="16" x2="54" y2="16" />
      <circle cx="12" cy="9" r="2.5" fill="#207448" />
      <circle cx="20" cy="9" r="2.5" fill="#207448" />
      <circle cx="28" cy="9" r="2.5" fill="#207448" />
    </g>
    <text x="${c[0]}" y="200" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Application</text>
  </g>

  <!-- Node 2: Stub resolver (libc / systemd-resolved) -->
  <g id="node-stub">
    <rect x="${c[1] - W[1]/2}" y="75" width="${W[1]}" height="175" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <!-- Gear Outline Icon (56x56) at center 460, top 90 -->
    <g transform="translate(${c[1] - 26}, 88)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="26" cy="26" r="10" />
      <path d="M26 4 L26 10 M26 42 L26 48 M4 26 L10 26 M42 26 L48 26 M10.5 10.5 L14.7 14.7 M37.3 37.3 L41.5 41.5 M10.5 41.5 L14.7 37.3 M37.3 14.7 L41.5 10.5" />
    </g>
    <text x="${c[1]}" y="166" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Stub resolver</text>
    <text x="${c[1]}" y="198" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle">(libc /</text>
    <text x="${c[1]}" y="228" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle">systemd-resolved)</text>
  </g>

  <!-- Node 3: Recursive resolver (cache) -->
  <g id="node-rec">
    <rect x="${c[2] - W[2]/2}" y="75" width="${W[2]}" height="175" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <!-- Cache Server Outline Icon (56x56) at center 765, top 90 -->
    <g transform="translate(${c[2] - 26}, 88)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="26" cy="11" rx="20" ry="7" />
      <path d="M6 11 v14 c0 4 9 7 20 7 s20 -3 20 -7 v-14" />
      <path d="M6 25 v14 c0 4 9 7 20 7 s20 -3 20 -7 v-14" />
    </g>
    <text x="${c[2]}" y="166" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Recursive</text>
    <text x="${c[2]}" y="198" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">resolver</text>
    <text x="${c[2]}" y="228" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle">(cache)</text>
  </g>

  <!-- Node 4: Root server -->
  <g id="node-root">
    <rect x="${c[3] - W[3]/2}" y="75" width="${W[3]}" height="175" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <!-- Globe Outline Icon (56x56) at center 1025, top 90 -->
    <g transform="translate(${c[3] - 26}, 88)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="26" cy="26" r="22" />
      <ellipse cx="26" cy="26" rx="10" ry="22" />
      <line x1="4" y1="26" x2="48" y2="26" />
    </g>
    <text x="${c[3]}" y="184" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Root</text>
    <text x="${c[3]}" y="220" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">server</text>
  </g>

  <!-- Node 5: .com TLD server -->
  <g id="node-tld">
    <rect x="${c[4] - W[4]/2}" y="75" width="${W[4]}" height="175" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <!-- Server Rack Outline Icon (56x56) at center 1220, top 90 -->
    <g transform="translate(${c[4] - 26}, 88)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="40" height="16" rx="4" />
      <circle cx="14" cy="14" r="2" fill="#207448" />
      <rect x="6" y="30" width="40" height="16" rx="4" />
      <circle cx="14" cy="38" r="2" fill="#207448" />
    </g>
    <text x="${c[4]}" y="166" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">.com</text>
    <text x="${c[4]}" y="198" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">TLD</text>
    <text x="${c[4]}" y="228" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">server</text>
  </g>

  <!-- Node 6: example.com authoritative -->
  <g id="node-auth">
    <rect x="${c[5] - W[5]/2}" y="75" width="${W[5]}" height="175" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <!-- Shield / Authority Outline Icon (56x56) at center 1445, top 90 -->
    <g transform="translate(${c[5] - 26}, 88)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M26 6 L44 14 v14 c0 12 -9 20 -18 24 c-9 -4 -18 -12 -18 -24 V14 z" />
      <path d="M19 26 l5 5 l11 -11" />
    </g>
    <text x="${c[5]}" y="184" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">example.com</text>
    <text x="${c[5]}" y="220" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle">authoritative</text>
  </g>

  <!-- SEQUENCE MESSAGES -->

  <!-- STEP 1: App -> Stub : getaddrinfo("www.example.com") -->
  <g id="step-1">
    <!-- Number circle 1 at sender lifeline -->
    <circle cx="${c[0]}" cy="340" r="24" fill="#207448" />
    <text x="${c[0]}" y="340" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">1</text>
    <!-- Label badge above arrow -->
    <rect x="204" y="265" width="216" height="68" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="312" y="286" font-family="ui-monospace, monospace" font-size="24" fill="#303a36" text-anchor="middle">
      <tspan x="312" dy="0">getaddrinfo(</tspan>
      <tspan x="312" dy="21">"www.example</tspan>
      <tspan x="312" dy="21">.com")</tspan>
    </text>
    <!-- Arrow line -->
    <line x1="${c[0] + 24}" y1="340" x2="${c[1]}" y2="340" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green-right)" />
  </g>

  <!-- STEP 2: Stub -> Rec : query www.example.com A (recursion desired) -->
  <g id="step-2">
    <!-- Number circle 2 at sender lifeline -->
    <circle cx="${c[1]}" cy="454" r="24" fill="#207448" />
    <text x="${c[1]}" y="454" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">2</text>
    <!-- Label badge above arrow -->
    <rect x="495" y="356" width="248" height="92" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="619" y="376" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle">
      <tspan x="619" dy="0">query</tspan>
      <tspan x="619" dy="22">www.example.com</tspan>
      <tspan x="619" dy="22">A (recursion</tspan>
      <tspan x="619" dy="22">desired)</tspan>
    </text>
    <!-- Arrow line -->
    <line x1="${c[1] + 24}" y1="454" x2="${c[2]}" y2="454" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green-right)" />
  </g>

  <!-- NOTE OVER REC: cache miss -->
  <g id="note-cache-miss">
    <rect x="${c[2] - 90}" y="472" width="180" height="40" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="2" stroke-dasharray="6 4" />
    <text x="${c[2]}" y="492" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle" dominant-baseline="central">cache miss</text>
  </g>

  <!-- STEP 3: Rec -> Root : www.example.com A ? -->
  <g id="step-3">
    <!-- Number circle 3 at sender lifeline -->
    <circle cx="${c[2]}" cy="600" r="24" fill="#207448" />
    <text x="${c[2]}" y="600" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">3</text>
    <!-- Label badge above arrow -->
    <rect x="797" y="526" width="195" height="68" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="894.5" y="547" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle">
      <tspan x="894.5" dy="0">www.</tspan>
      <tspan x="894.5" dy="21">example.com</tspan>
      <tspan x="894.5" dy="21">A ?</tspan>
    </text>
    <!-- Arrow line -->
    <line x1="${c[2] + 24}" y1="600" x2="${c[3]}" y2="600" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green-right)" />
  </g>

  <!-- STEP 4: Root -> Rec : referral: NS for com (+ glue) -->
  <g id="step-4">
    <!-- Number circle 4 at sender lifeline -->
    <circle cx="${c[3]}" cy="692" r="24" fill="#207448" />
    <text x="${c[3]}" y="692" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">4</text>
    <!-- Label badge above arrow -->
    <rect x="805" y="618" width="180" height="68" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="895" y="639" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle">
      <tspan x="895" dy="0">referral:</tspan>
      <tspan x="895" dy="21">NS for com</tspan>
      <tspan x="895" dy="21">(+ glue)</tspan>
    </text>
    <!-- Arrow line dashed right to left -->
    <line x1="${c[3] - 24}" y1="692" x2="${c[2]}" y2="692" stroke="#207448" stroke-width="3" stroke-dasharray="6 4" marker-end="url(#arrow-green-left)" />
  </g>

  <!-- STEP 5: Rec -> TLD : www.example.com A ? -->
  <g id="step-5">
    <!-- Number circle 5 at sender lifeline -->
    <circle cx="${c[2]}" cy="756" r="24" fill="#207448" />
    <text x="${c[2]}" y="756" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">5</text>
    <!-- Label badge above arrow -->
    <rect x="840" y="710" width="310" height="40" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="995" y="730" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle" dominant-baseline="central">www.example.com A ?</text>
    <!-- Arrow line -->
    <line x1="${c[2] + 24}" y1="756" x2="${c[4]}" y2="756" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green-right)" />
  </g>

  <!-- STEP 6: TLD -> Rec : referral: NS for example.com (+ glue) -->
  <g id="step-6">
    <!-- Number circle 6 at sender lifeline -->
    <circle cx="${c[4]}" cy="834" r="24" fill="#207448" />
    <text x="${c[4]}" y="834" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">6</text>
    <!-- Label badge above arrow -->
    <rect x="830" y="774" width="325" height="54" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="992.5" y="798" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle">
      <tspan x="992.5" dy="0">referral: NS for</tspan>
      <tspan x="992.5" dy="24">example.com (+ glue)</tspan>
    </text>
    <!-- Arrow line dashed right to left -->
    <line x1="${c[4] - 24}" y1="834" x2="${c[2]}" y2="834" stroke="#207448" stroke-width="3" stroke-dasharray="6 4" marker-end="url(#arrow-green-left)" />
  </g>

  <!-- STEP 7: Rec -> Auth : www.example.com A ? -->
  <g id="step-7">
    <!-- Number circle 7 at sender lifeline -->
    <circle cx="${c[2]}" cy="898" r="24" fill="#207448" />
    <text x="${c[2]}" y="898" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">7</text>
    <!-- Label badge above arrow -->
    <rect x="950" y="852" width="310" height="40" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="1105" y="872" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle" dominant-baseline="central">www.example.com A ?</text>
    <!-- Arrow line -->
    <line x1="${c[2] + 24}" y1="898" x2="${c[5]}" y2="898" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green-right)" />
  </g>

  <!-- STEP 8: Auth -> Rec : A 93.184.216.34, TTL 300 (aa) [ORANGE] -->
  <g id="step-8">
    <!-- Number circle 8 at sender lifeline (Orange) -->
    <circle cx="${c[5]}" cy="976" r="24" fill="#db8129" />
    <text x="${c[5]}" y="976" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">8</text>
    <!-- Label badge above arrow (Orange border) -->
    <rect x="970" y="916" width="270" height="54" rx="8" fill="#e8f1ea" stroke="#db8129" stroke-width="3" />
    <text x="1105" y="940" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">
      <tspan x="1105" dy="0">A 93.184.216.34,</tspan>
      <tspan x="1105" dy="24">TTL 300 (aa)</tspan>
    </text>
    <!-- Arrow line dashed right to left (Orange) -->
    <line x1="${c[5] - 24}" y1="976" x2="${c[2]}" y2="976" stroke="#db8129" stroke-width="3" stroke-dasharray="6 4" marker-end="url(#arrow-orange-left)" />
  </g>

  <!-- STEP 9: Rec -> Stub : answer (cached for 300 s) -->
  <g id="step-9">
    <!-- Number circle 9 at sender lifeline -->
    <circle cx="${c[2]}" cy="1068" r="24" fill="#207448" />
    <text x="${c[2]}" y="1068" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">9</text>
    <!-- Label badge above arrow -->
    <rect x="522" y="994" width="195" height="68" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="619.5" y="1015" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle">
      <tspan x="619.5" dy="0">answer</tspan>
      <tspan x="619.5" dy="21">(cached for</tspan>
      <tspan x="619.5" dy="21">300 s)</tspan>
    </text>
    <!-- Arrow line dashed right to left -->
    <line x1="${c[2] - 24}" y1="1068" x2="${c[1]}" y2="1068" stroke="#207448" stroke-width="3" stroke-dasharray="6 4" marker-end="url(#arrow-green-left)" />
  </g>

  <!-- STEP 10: Stub -> App : address -->
  <g id="step-10">
    <!-- Number circle 10 at sender lifeline -->
    <circle cx="${c[1]}" cy="1132" r="24" fill="#207448" />
    <text x="${c[1]}" y="1132" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">10</text>
    <!-- Label badge above arrow -->
    <rect x="235" y="1086" width="150" height="40" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="310" y="1106" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36" text-anchor="middle" dominant-baseline="central">address</text>
    <!-- Arrow line dashed right to left -->
    <line x1="${c[1] - 24}" y1="1132" x2="${c[0]}" y2="1132" stroke="#207448" stroke-width="3" stroke-dasharray="6 4" marker-end="url(#arrow-green-left)" />
  </g>
</svg>`;
}

fs.writeFileSync('lookup.svg', generateSVG());
console.log('lookup.svg created successfully');
