import re
import xml.etree.ElementTree as ET

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>A guard stops the apply, a comment only asks</title>
  <desc>Infographic explaining Terraform two-layer defense against accidental resource destruction, including module-level lifecycle prevent_destroy, plan-level policy checks, caveats, and companion rules.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Main Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">A guard stops the apply, a comment only asks</text>

  <!-- ==================== LAYER 1 CONTAINER: MODULE GUARD ==================== -->
  <g id="layer-1">
    <rect x="40" y="95" width="1520" height="405" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Layer 1 Header Icon: Shield with Lock Outline (56x56) -->
    <g stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <path d="M 93 112 L 115 122 V 144 C 115 158 93 168 93 168 C 93 168 71 158 71 144 V 122 Z"/>
      <rect x="86" y="138" width="14" height="12" rx="2"/>
      <path d="M 89 138 V 132 A 4 4 0 0 1 97 132 V 138"/>
    </g>

    <!-- Layer 1 Header Text -->
    <text x="140" y="136" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="140" dy="0">lifecycle prevent_destroy in the module:</tspan>
      <tspan x="140" dy="32">Terraform rejects any plan that would destroy the object</tspan>
    </text>

    <!-- Left Subpanel: Example Plan Output (Terminal Window) -->
    <g id="plan-output-subpanel">
      <rect x="65" y="188" width="915" height="292" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Terminal Window Bar -->
      <path d="M 65 200 A 12 12 0 0 1 77 188 H 968 A 12 12 0 0 1 980 200 V 226 H 65 Z" fill="#207448"/>
      <circle cx="87" cy="207" r="5" fill="#ffffff" opacity="0.8"/>
      <circle cx="104" cy="207" r="5" fill="#ffffff" opacity="0.8"/>
      <circle cx="121" cy="207" r="5" fill="#ffffff" opacity="0.8"/>
      <path d="M 148 201 L 155 207 L 148 213 M 159 213 H 168" stroke="#ffffff" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>

      <!-- Plan Line 1: Resource Destroy Notice -->
      <text x="85" y="260" font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="85" dy="0">nebius_mk8s_v1_node_group.pool[gpu] will be destroyed</tspan>
        <tspan x="85" dy="30">(because key gpu is not in for_each map)</tspan>
      </text>

      <!-- Plan Line 2: Plan Summary -->
      <text x="85" y="336" font-family="monospace" font-size="24" fill="#303a36">Plan: 0 to add, 0 to change, 1 to destroy.</text>

      <!-- Plan Line 3: Instance Cannot Be Destroyed (Single Orange Highlight) -->
      <text x="85" y="380" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129">Error: Instance cannot be destroyed</text>

      <!-- Plan Line 4: Failure Explanation -->
      <text x="85" y="426" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="85" dy="0">the plan still prints but ends with an error</tspan>
        <tspan x="85" dy="30">so an automated apply fails</tspan>
      </text>
    </g>

    <!-- Right Subpanel: Three Caveats -->
    <g id="three-caveats-subpanel">
      <rect x="1005" y="188" width="535" height="292" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>

      <!-- Caution Icon (56x56) -->
      <g stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 1053 202 L 1079 246 L 1027 246 Z"/>
        <line x1="1053" y1="216" x2="1053" y2="230"/>
        <circle cx="1053" cy="239" r="1.5" fill="#207448"/>
      </g>

      <!-- Caveat 1 -->
      <rect x="1020" y="256" width="505" height="66" rx="8" fill="#e8f1ea"/>
      <text x="1035" y="282" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1035" dy="0">does not help if you delete the</tspan>
        <tspan x="1035" dy="28">resource block from the code</tspan>
      </text>

      <!-- Caveat 2 -->
      <rect x="1020" y="332" width="505" height="66" rx="8" fill="#e8f1ea"/>
      <text x="1035" y="358" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1035" dy="0">can make some changes</tspan>
        <tspan x="1035" dy="28">impossible</tspan>
      </text>

      <!-- Caveat 3 -->
      <rect x="1020" y="408" width="505" height="58" rx="8" fill="#e8f1ea"/>
      <text x="1035" y="444" font-family="sans-serif" font-size="24" fill="#303a36">blocks terraform destroy</text>
    </g>
  </g>

  <!-- ==================== REASON CALLOUT BAR ==================== -->
  <g id="reason-callout">
    <rect x="40" y="520" width="1520" height="70" rx="12" fill="#207448"/>
    <text x="800" y="564" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">one layer can be removed by a careless edit and the other catches the edit</text>
  </g>

  <!-- ==================== LAYER 2 CONTAINER: PLAN POLICY CHECK ==================== -->
  <g id="layer-2">
    <rect x="40" y="610" width="1520" height="135" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Layer 2 Icon: Policy Gate & Document Check Outline (56x56) -->
    <g stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <rect x="72" y="632" width="34" height="46" rx="4"/>
      <line x1="82" y1="645" x2="96" y2="645"/>
      <line x1="82" y1="655" x2="96" y2="655"/>
      <circle cx="102" cy="662" r="11"/>
      <line x1="110" y1="670" x2="119" y2="679"/>
    </g>

    <!-- Layer 2 Text -->
    <text x="140" y="658" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">
      <tspan x="140" dy="0">policy check on the plan: terraform show -json fed to a risk script</tspan>
      <tspan x="140" dy="34">or Open Policy Agent; exits 1 on CRITICAL destroy of a stateful resource</tspan>
    </text>
  </g>

  <!-- ==================== COMPANION RULES CONTAINER ==================== -->
  <g id="companion-rules">
    <rect x="40" y="765" width="1520" height="405" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Card 1: moved block -->
    <g id="rule-moved-block">
      <rect x="60" y="785" width="720" height="175" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Move / Rename Redirect Outline (56x56) -->
      <g stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
        <path d="M 88 855 C 88 830, 115 830, 125 830"/>
        <polyline points="117,822 127,830 117,838"/>
        <rect x="83" y="855" width="22" height="18" rx="3" stroke-width="3"/>
      </g>
      <text x="155" y="825" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="155" dy="0">moved block records a rename so the</tspan>
        <tspan x="155" dy="28">plan shows a move not a destroy; keep</tspan>
        <tspan x="155" dy="28">every moved block forever or old</tspan>
        <tspan x="155" dy="28">callers plan a destroy</tspan>
      </text>
    </g>

    <!-- Card 2: create_before_destroy -->
    <g id="rule-create-before-destroy">
      <rect x="820" y="785" width="720" height="175" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Staggered Creation / Precedence Outline (56x56) -->
      <g stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
        <rect x="844" y="845" width="30" height="24" rx="4"/>
        <rect x="860" y="825" width="30" height="24" rx="4"/>
        <line x1="875" y1="833" x2="875" y2="841" stroke-width="3"/>
        <line x1="871" y1="837" x2="879" y2="837" stroke-width="3"/>
      </g>
      <text x="915" y="838" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="915" dy="0">create_before_destroy creates the</tspan>
        <tspan x="915" dy="32">replacement first and spreads to</tspan>
        <tspan x="915" dy="32">dependencies</tspan>
      </text>
    </g>

    <!-- Card 3: after every import read the plan -->
    <g id="rule-after-import">
      <rect x="60" y="975" width="720" height="175" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Document Inspection / Eye Outline (56x56) -->
      <g stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none">
        <rect x="84" y="999" width="34" height="46" rx="4"/>
        <path d="M 91 1022 Q 101 1014 111 1022 Q 101 1030 91 1022 Z"/>
        <circle cx="101" cy="1022" r="2.5" fill="#207448"/>
      </g>
      <text x="155" y="1045" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="155" dy="0">after every import read the plan</tspan>
        <tspan x="155" dy="32">before anything else</tspan>
      </text>
    </g>

    <!-- Card 4: plan.bin sealed envelope -->
    <g id="rule-sealed-envelope">
      <rect x="820" y="975" width="720" height="175" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Sealed Envelope Outline (56x56) -->
      <g stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none">
        <rect x="844" y="1005" width="46" height="34" rx="4"/>
        <path d="M 844 1007 L 867 1023 L 890 1007"/>
        <circle cx="867" cy="1025" r="4.5" fill="#207448"/>
      </g>
      <text x="915" y="1032" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="915" dy="0">terraform plan -out=plan.bin then</tspan>
        <tspan x="915" dy="30">apply that exact file; treat it as</tspan>
        <tspan x="915" dy="30">sensitive; the sealed envelope</tspan>
      </text>
    </g>
  </g>
</svg>'''

with open("candidate_test.svg", "w") as f:
    f.write(svg_content)

print("candidate_test.svg written successfully!")
