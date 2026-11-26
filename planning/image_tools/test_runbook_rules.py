import re
import xml.etree.ElementTree as ET

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Seven rules for a runbook written for a half-asleep reader</title>
  <desc>Infographic explaining seven rules and examples for writing effective runbooks for on-call engineers.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Diagram Title -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#207448">Seven rules for a runbook written for a half-asleep reader</text>

  <!-- Setting Panel -->
  <g id="setting">
    <rect x="40" y="75" width="1520" height="95" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <!-- Alarm Clock Icon at 03:10 -->
    <g transform="translate(60, 95)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="30" r="22"/>
      <path d="M 14 12 C 12 5 20 2 24 7"/>
      <path d="M 42 12 C 44 5 36 2 32 7"/>
      <line x1="14" y1="48" x2="8" y2="55"/>
      <line x1="42" y1="48" x2="48" y2="55"/>
      <line x1="28" y1="30" x2="41" y2="30"/>
      <line x1="28" y1="30" x2="38" y2="13"/>
    </g>
    <text font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36"><tspan x="135" y="115">the page arrives at 03:10; the engineer is tired, </tspan><tspan x="135" y="150">does not know the service well and has the runbook in one tab</tspan></text>
  </g>

  <!-- Table of Rule and Example -->
  <g id="rules-table">
    <!-- Row 1: Date and owner -->
    <g id="rule-1">
      <rect x="40" y="185" width="1520" height="95" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
      <line x1="710" y1="185" x2="710" y2="280" stroke="#c4d9cb" stroke-width="2" stroke-dasharray="6 4"/>
      <!-- Calendar Icon -->
      <g transform="translate(60, 205)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="5" y="8" width="46" height="42" rx="6"/>
        <line x1="5" y1="20" x2="51" y2="20"/>
        <line x1="16" y1="2" x2="16" y2="10"/>
        <line x1="40" y1="2" x2="40" y2="10"/>
        <circle cx="18" cy="31" r="2.5" fill="#207448"/>
        <circle cx="28" cy="31" r="2.5" fill="#207448"/>
        <circle cx="38" cy="31" r="2.5" fill="#207448"/>
      </g>
      <text font-family="sans-serif" font-size="30" fill="#303a36"><tspan x="135" y="224" font-weight="bold" fill="#207448">Date and owner </tspan><tspan x="135" y="260" font-weight="bold" fill="#207448">on the first line: </tspan><tspan x="740" y="242" font-size="24" font-family="monospace">Reviewed 2026-03-28 by Mei Tanaka</tspan></text>
    </g>

    <!-- Row 2: User impact and first safe action (Primary Highlight - Orange) -->
    <g id="rule-2">
      <rect x="40" y="290" width="1520" height="105" rx="10" fill="#fff9f2" stroke="#db8129" stroke-width="3"/>
      <line x1="710" y1="290" x2="710" y2="395" stroke="#db8129" stroke-width="2" stroke-dasharray="6 4"/>
      <!-- Alert / Shield Triangle Icon in Orange -->
      <g transform="translate(60, 314)" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 28 4 L 52 48 L 4 48 Z"/>
        <line x1="28" y1="18" x2="28" y2="32"/>
        <circle cx="28" cy="40" r="2" fill="#db8129"/>
      </g>
      <text font-family="sans-serif" font-size="30" fill="#303a36"><tspan x="135" y="332" font-weight="bold" fill="#db8129">Open with the user impact, </tspan><tspan x="135" y="368" font-weight="bold" fill="#db8129">then the first safe action: </tspan><tspan x="740" y="332" font-size="24" font-family="monospace">Users see slow replies. </tspan><tspan x="740" y="368" font-size="24" font-family="monospace">First step: set the group weight to 0</tspan></text>
    </g>

    <!-- Row 3: One action per numbered step -->
    <g id="rule-3">
      <rect x="40" y="405" width="1520" height="95" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
      <line x1="710" y1="405" x2="710" y2="500" stroke="#c4d9cb" stroke-width="2" stroke-dasharray="6 4"/>
      <!-- Numbered Step / Command Prompt Icon -->
      <g transform="translate(60, 425)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="5" y="8" width="46" height="42" rx="6"/>
        <polyline points="14,24 22,29 14,34"/>
        <line x1="26" y1="34" x2="38" y2="34"/>
      </g>
      <text font-family="sans-serif" font-size="30" fill="#303a36"><tspan x="135" y="444" font-weight="bold" fill="#207448">One action per </tspan><tspan x="135" y="480" font-weight="bold" fill="#207448">numbered step: </tspan><tspan x="740" y="462" font-size="24" font-family="monospace">Run this command. You should see this</tspan></text>
    </g>

    <!-- Row 4: Result look like -->
    <g id="rule-4">
      <rect x="40" y="510" width="1520" height="95" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
      <line x1="710" y1="510" x2="710" y2="605" stroke="#c4d9cb" stroke-width="2" stroke-dasharray="6 4"/>
      <!-- Eye / Inspection Icon -->
      <g transform="translate(60, 530)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 4 28 Q 28 10 52 28 Q 28 46 4 28 Z"/>
        <circle cx="28" cy="28" r="7"/>
      </g>
      <text font-family="sans-serif" font-size="30" fill="#303a36"><tspan x="135" y="549" font-weight="bold" fill="#207448">Say what the result </tspan><tspan x="135" y="585" font-weight="bold" fill="#207448">should look like: </tspan><tspan x="740" y="567" font-size="24" font-family="monospace">Expected: weight 0 in the output</tspan></text>
    </g>

    <!-- Row 5: Undo before risky step -->
    <g id="rule-5">
      <rect x="40" y="615" width="1520" height="95" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
      <line x1="710" y1="615" x2="710" y2="710" stroke="#c4d9cb" stroke-width="2" stroke-dasharray="6 4"/>
      <!-- Undo / Return Arrow Icon -->
      <g transform="translate(60, 635)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 46 36 C 46 22 36 14 24 14 C 12 14 4 24 4 36"/>
        <polyline points="14,8 24,14 18,24"/>
      </g>
      <text font-family="sans-serif" font-size="30" fill="#303a36"><tspan x="135" y="654" font-weight="bold" fill="#207448">State the undo before </tspan><tspan x="135" y="690" font-weight="bold" fill="#207448">the risky step: </tspan><tspan x="740" y="672" font-size="24" font-family="monospace">To undo, set the weight back to 25</tspan></text>
    </g>

    <!-- Row 6: Stop point and name to call -->
    <g id="rule-6">
      <rect x="40" y="720" width="1520" height="100" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
      <line x1="710" y1="720" x2="710" y2="820" stroke="#c4d9cb" stroke-width="2" stroke-dasharray="6 4"/>
      <!-- Pager / Phone Icon -->
      <g transform="translate(60, 742)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="4" width="40" height="48" rx="6"/>
        <rect x="15" y="10" width="26" height="20" rx="3"/>
        <circle cx="19" cy="40" r="2" fill="#207448"/>
        <circle cx="28" cy="40" r="2" fill="#207448"/>
        <circle cx="37" cy="40" r="2" fill="#207448"/>
      </g>
      <text font-family="sans-serif" font-size="30" fill="#303a36"><tspan x="135" y="759" font-weight="bold" fill="#207448">Give a stop point </tspan><tspan x="135" y="795" font-weight="bold" fill="#207448">and a name to call: </tspan><tspan x="740" y="759" font-size="24" font-family="monospace">If errors continue after step 4, </tspan><tspan x="740" y="795" font-size="24" font-family="monospace">page the platform on-call</tspan></text>
    </g>

    <!-- Row 7: No background theory in the steps -->
    <g id="rule-7">
      <rect x="40" y="830" width="1520" height="95" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
      <line x1="710" y1="830" x2="710" y2="925" stroke="#c4d9cb" stroke-width="2" stroke-dasharray="6 4"/>
      <!-- Book / Link Icon -->
      <g transform="translate(60, 850)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 6 10 C 14 8 22 12 28 16 C 34 12 42 8 50 10 L 50 44 C 42 42 34 46 28 50 C 22 46 14 42 6 44 Z"/>
        <line x1="28" y1="16" x2="28" y2="50"/>
      </g>
      <text font-family="sans-serif" font-size="30" fill="#303a36"><tspan x="135" y="869" font-weight="bold" fill="#207448">No background theory </tspan><tspan x="135" y="905" font-weight="bold" fill="#207448">in the steps: </tspan><tspan x="740" y="887" font-size="24" font-family="monospace">put theory under a link at the bottom</tspan></text>
    </g>
  </g>

  <!-- Footer Panel -->
  <g id="footer">
    <rect x="40" y="940" width="1520" height="230" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <!-- Checklist / Drill Icon -->
    <g transform="translate(60, 1025)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="50" rx="6"/>
      <rect x="18" y="3" width="20" height="9" rx="3" fill="#e8f1ea"/>
      <line x1="16" y1="24" x2="38" y2="24"/>
      <line x1="16" y1="36" x2="38" y2="36"/>
      <line x1="16" y1="48" x2="30" y2="48"/>
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="135" y="980">test it by giving it to an engineer who has not used it and watch where they pause; </tspan><tspan x="135" y="1020">Wheel of Misfortune: new engineers act out a past incident from its post-mortem </tspan><tspan x="135" y="1060">(example target: runbook drill in under 10 minutes); </tspan><tspan x="135" y="1100">every step is a claim that it works today, so review after every service change; </tspan><tspan x="135" y="1140">automate deterministic steps</tspan></text>
  </g>
</svg>"""

root = ET.fromstring(svg_content)
texts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    t = "".join(elem.itertext()).strip()
    fs = float(elem.attrib.get("font-size", 0))
    print(f"Font-size {fs}: '{t}'")
    assert fs >= 24, f"Font size {fs} < 24 for '{t}'"
    texts.append(t)

expected_labels = [
    "Seven rules for a runbook written for a half-asleep reader",
    "the page arrives at 03:10; the engineer is tired, does not know the service well and has the runbook in one tab",
    "Date and owner on the first line: Reviewed 2026-03-28 by Mei Tanaka",
    "Open with the user impact, then the first safe action: Users see slow replies. First step: set the group weight to 0",
    "One action per numbered step: Run this command. You should see this",
    "Say what the result should look like: Expected: weight 0 in the output",
    "State the undo before the risky step: To undo, set the weight back to 25",
    "Give a stop point and a name to call: If errors continue after step 4, page the platform on-call",
    "No background theory in the steps: put theory under a link at the bottom",
    "test it by giving it to an engineer who has not used it and watch where they pause; Wheel of Misfortune: new engineers act out a past incident from its post-mortem (example target: runbook drill in under 10 minutes); every step is a claim that it works today, so review after every service change; automate deterministic steps"
]

for label in expected_labels:
    assert label in texts, f"Missing label: {label}"

print("\nALL 10 EXPECTED LABELS EXACTLY MATCHED!")
