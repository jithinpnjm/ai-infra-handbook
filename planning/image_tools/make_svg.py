import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Why a published Docker port ignores your firewall rule</title>
  <desc>Visual infographic explaining how Docker publishes ports by inserting iptables NAT and FORWARD rules ahead of host firewalls like UFW and firewalld.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#207448"/>
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#db8129"/>
    </marker>
  </defs>

  <!-- Canvas Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- ==================== TITLE (2 lines max, 48px bold) ==================== -->
  <g id="title-group">
    <text x="40" y="70" font-family="sans-serif" font-size="48px" font-weight="bold" fill="#303a36">Why a published Docker port</text>
    <text x="40" y="120" font-family="sans-serif" font-size="48px" font-weight="bold" fill="#303a36">ignores your firewall rule</text>
  </g>

  <!-- ==================== MAIN SECTION (y=160 to 800) ==================== -->

  <!-- STEP 1: Client Node -->
  <g id="client-node">
    <rect x="40" y="160" width="430" height="80" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Laptop outline (56px, stroke 4, green) -->
    <g transform="translate(55, 172)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="40" height="28" rx="3"/>
      <line x1="2" y1="46" x2="50" y2="46"/>
      <line x1="18" y1="46" x2="34" y2="46" stroke-width="6"/>
      <line x1="6" y1="34" x2="46" y2="34"/>
    </g>
    <!-- Step 1 circle (r=24, green, white number) -->
    <circle cx="132" cy="200" r="24" fill="#207448"/>
    <text x="132" y="208" font-family="sans-serif" font-size="24px" font-weight="bold" fill="#ffffff" text-anchor="middle">1</text>
    <!-- Client Label -->
    <text x="170" y="188" font-family="sans-serif" font-size="24px" fill="#303a36">
      <tspan x="170" dy="0">Client on the</tspan>
      <tspan x="170" dy="24">office network or</tspan>
      <tspan x="170" dy="24">anywhere</tspan>
    </text>
  </g>

  <!-- Arrow 1: Client -> Host NIC -->
  <line x1="470" y1="200" x2="550" y2="200" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)"/>

  <!-- STEP 2: Host NIC Node -->
  <g id="host-nic-node">
    <rect x="550" y="160" width="430" height="80" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: NIC card outline (56px, stroke 4, green) -->
    <g transform="translate(565, 172)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="34" rx="4"/>
      <line x1="6" y1="18" x2="2" y2="18"/>
      <line x1="6" y1="32" x2="2" y2="32"/>
      <rect x="16" y="16" width="14" height="18" fill="#e8f1ea"/>
      <line x1="36" y1="14" x2="44" y2="14"/>
      <line x1="36" y1="24" x2="44" y2="24"/>
      <line x1="36" y1="34" x2="44" y2="34"/>
      <line x1="12" y1="42" x2="44" y2="42" stroke-width="5"/>
    </g>
    <!-- Step 2 circle (r=24, green, white number) -->
    <circle cx="655" cy="200" r="24" fill="#207448"/>
    <text x="655" y="208" font-family="sans-serif" font-size="24px" font-weight="bold" fill="#ffffff" text-anchor="middle">2</text>
    <!-- Host NIC Label -->
    <text x="700" y="209" font-family="sans-serif" font-size="30px" font-weight="bold" fill="#303a36">Host NIC</text>
  </g>

  <!-- Arrow 2: Host NIC -> netfilter chains -->
  <line x1="765" y1="240" x2="765" y2="280" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)"/>

  <!-- STEP 3: netfilter chains (Container) -->
  <g id="netfilter-chains-container">
    <rect x="40" y="280" width="940" height="210" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <!-- Container Header Icon: Filters / mesh outline -->
    <g transform="translate(60, 290)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="4,4 32,4 20,18 20,28 16,28 16,18"/>
      <circle cx="28" cy="24" r="5"/>
      <line x1="28" y1="17" x2="28" y2="19"/>
      <line x1="28" y1="29" x2="28" y2="31"/>
      <line x1="21" y1="24" x2="23" y2="24"/>
      <line x1="33" y1="24" x2="35" y2="24"/>
    </g>
    <!-- Step 3 circle (r=24, green, white number) -->
    <circle cx="135" cy="306" r="24" fill="#207448"/>
    <text x="135" y="314" font-family="sans-serif" font-size="24px" font-weight="bold" fill="#ffffff" text-anchor="middle">3</text>
    <!-- netfilter chains Label -->
    <text x="175" y="315" font-family="sans-serif" font-size="30px" font-weight="bold" fill="#207448">netfilter chains</text>

    <!-- STEP 4: Docker rules box (Left) -->
    <g id="docker-rules-box">
      <rect x="60" y="335" width="440" height="140" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Step 4 circle (r=24, green, white number) -->
      <circle cx="92" cy="365" r="24" fill="#207448"/>
      <text x="92" y="373" font-family="sans-serif" font-size="24px" font-weight="bold" fill="#ffffff" text-anchor="middle">4</text>
      <!-- Docker rules Label -->
      <text font-family="sans-serif" font-size="24px" fill="#303a36">
        <tspan x="125" y="360">Docker's own NAT and</tspan>
        <tspan x="125" y="384">FORWARD rules (DOCKER</tspan>
        <tspan x="75" y="412">chain) are inserted ahead</tspan>
        <tspan x="75" y="438">of the rules managed by</tspan>
        <tspan x="75" y="464">ufw or firewalld</tspan>
      </text>
    </g>

    <!-- Beside it: Firewall rule box (Right, shown skipped) -->
    <g id="firewall-skipped-box">
      <rect x="530" y="335" width="430" height="140" rx="8" fill="#f0f4f1" stroke="#8a9691" stroke-width="2" stroke-dasharray="8 6"/>
      <!-- Icon: Shield with strike-through (skipped outline) -->
      <g transform="translate(550, 350)" stroke="#8a9691" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 6 6 L 24 2 L 42 6 C 42 24 24 38 24 38 C 24 38 6 24 6 6 Z"/>
        <line x1="10" y1="10" x2="38" y2="34" stroke-width="4"/>
      </g>
      <!-- Firewall rule Label -->
      <text x="610" y="385" font-family="sans-serif" font-size="24px" fill="#606d68">
        <tspan x="610" dy="0">ufw or firewalld rule that</tspan>
        <tspan x="610" dy="28">should block the port</tspan>
      </text>
    </g>
  </g>

  <!-- STEP 5: Container port 80 box -->
  <g id="container-port-box">
    <rect x="60" y="525" width="340" height="70" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Container cube outline -->
    <g transform="translate(75, 536)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="20,4 38,13 20,22 2,13"/>
      <polygon points="2,13 20,22 20,44 2,35"/>
      <polygon points="38,13 20,22 20,44 38,35"/>
    </g>
    <!-- Step 5 circle (r=24, green, white number) -->
    <circle cx="145" cy="560" r="24" fill="#207448"/>
    <text x="145" y="568" font-family="sans-serif" font-size="24px" font-weight="bold" fill="#ffffff" text-anchor="middle">5</text>
    <!-- Container port Label -->
    <text x="185" y="553" font-family="sans-serif" font-size="26px" font-weight="bold" fill="#303a36">
      <tspan x="185" dy="0">container</tspan>
      <tspan x="185" dy="26">port 80</tspan>
    </text>
  </g>

  <!-- THE SINGLE ORANGE ARROW: Docker rules -> container port 80 -->
  <line x1="230" y1="475" x2="230" y2="525" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)"/>
  <!-- Orange arrow label: in clear space beside the orange arrow -->
  <text x="430" y="552" font-family="sans-serif" font-size="24px" font-weight="bold" fill="#db8129">
    <tspan x="430" dy="0">published port 8080</tspan>
    <tspan x="430" dy="26">answers from anywhere</tspan>
  </text>

  <!-- FIXES BOX (y=635 to 800) -->
  <g id="fixes-box">
    <rect x="40" y="635" width="940" height="165" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Shield with lock outline (56px, stroke 4, green) -->
    <g transform="translate(56, 650)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 8 L 28 4 L 48 8 C 48 30 28 48 28 48 C 28 48 8 30 8 8 Z"/>
      <circle cx="28" cy="22" r="5"/>
      <line x1="28" y1="27" x2="28" y2="35"/>
    </g>
    <!-- Three fix labels -->
    <text x="125" y="665" font-family="sans-serif" font-size="24px" fill="#303a36">
      <tspan x="125" dy="0">restrict a port with the DOCKER-USER chain</tspan>
      <tspan x="125" dy="32">bind the port to a specific address (for example</tspan>
      <tspan x="125" dy="25">127.0.0.1:8080:80)</tspan>
      <tspan x="125" dy="32">if a published port must stay private on a shared host,</tspan>
      <tspan x="125" dy="25">restrict it in DOCKER-USER before you publish it</tspan>
    </text>
  </g>

  <!-- ==================== RIGHT PANEL: Docker network modes ==================== -->
  <g id="right-panel">
    <rect x="1020" y="160" width="540" height="640" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Network nodes outline (56px, stroke 4, green) -->
    <g transform="translate(1040, 175)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="14" r="8"/>
      <circle cx="44" cy="14" r="8"/>
      <circle cx="12" cy="42" r="8"/>
      <circle cx="44" cy="42" r="8"/>
      <line x1="20" y1="14" x2="36" y2="14"/>
      <line x1="12" y1="22" x2="12" y2="34"/>
      <line x1="44" y1="22" x2="44" y2="34"/>
      <line x1="20" y1="42" x2="36" y2="42"/>
      <line x1="18" y1="20" x2="38" y2="36"/>
    </g>
    <!-- Panel Title -->
    <text x="1115" y="210" font-family="sans-serif" font-size="30px" font-weight="bold" fill="#207448">Docker network modes</text>

    <!-- Network modes items -->
    <text x="1045" y="255" font-family="sans-serif" font-size="24px" fill="#303a36">
      <!-- Item 1: bridge -->
      <tspan x="1045" dy="0" font-weight="bold" fill="#207448">bridge: </tspan>
      <tspan>private subnet, veth per</tspan>
      <tspan x="1045" dy="25">container, NAT outbound, -p</tspan>
      <tspan x="1045" dy="25">publishes via DNAT; user-defined</tspan>
      <tspan x="1045" dy="25">bridges add DNS-based name</tspan>
      <tspan x="1045" dy="25">resolution and isolation</tspan>

      <!-- Item 2: host -->
      <tspan x="1045" dy="36" font-weight="bold" fill="#207448">host: </tspan>
      <tspan>shares the host namespace,</tspan>
      <tspan x="1045" dy="25">no isolation, no NAT, best</tspan>
      <tspan x="1045" dy="25">performance, ports conflict with</tspan>
      <tspan x="1045" dy="25">host: NCCL or HPC containers</tspan>

      <!-- Item 3: none -->
      <tspan x="1045" dy="36">none: only loopback</tspan>

      <!-- Item 4: container:NAME -->
      <tspan x="1045" dy="36">container:NAME: shares another</tspan>
      <tspan x="1045" dy="25">container's namespace (how a</tspan>
      <tspan x="1045" dy="25">Kubernetes pod works)</tspan>

      <!-- Item 5: overlay -->
      <tspan x="1045" dy="36">overlay: VXLAN across Docker hosts</tspan>
      <tspan x="1045" dy="25">(Swarm)</tspan>

      <!-- Item 6: macvlan or ipvlan -->
      <tspan x="1045" dy="36">macvlan or ipvlan: container on</tspan>
      <tspan x="1045" dy="25">the physical network</tspan>
    </text>
  </g>

  <!-- ==================== MODEL STRIP (CNM) ==================== -->
  <g id="model-strip">
    <rect x="40" y="840" width="1520" height="80" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Modular blocks outline (stroke 3, green) -->
    <g transform="translate(56, 852)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="16" height="16" rx="2"/>
      <rect x="28" y="6" width="16" height="16" rx="2"/>
      <rect x="16" y="32" width="16" height="16" rx="2"/>
      <line x1="12" y1="22" x2="20" y2="32"/>
      <line x1="36" y1="22" x2="28" y2="32"/>
    </g>
    <!-- CNM Label -->
    <text x="125" y="865" font-family="sans-serif" font-size="24px" fill="#303a36">
      <tspan x="125" dy="0">CNM: sandbox (the namespace config), endpoint (the attachment, typically a veth),</tspan>
      <tspan x="125" dy="25">network (a group of endpoints); local drivers bridge, host, none, macvlan, ipvlan;</tspan>
      <tspan x="125" dy="25">global driver overlay needs a key-value store</tspan>
    </text>
  </g>

  <!-- ==================== FOOTER & INSPECT COMMANDS ==================== -->
  <!-- Left Box: Footer (default subnet...) -->
  <g id="footer-subnet-box">
    <rect x="40" y="960" width="720" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Network subnet alert outline (stroke 3, green) -->
    <g transform="translate(56, 975)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="22,6 42,42 2,42"/>
      <line x1="22" y1="18" x2="22" y2="28"/>
      <circle cx="22" cy="35" r="2" fill="#207448"/>
    </g>
    <!-- Footer Subnet Label -->
    <text x="115" y="983" font-family="sans-serif" font-size="24px" fill="#303a36">
      <tspan x="115" dy="0">default subnet 172.17.0.0/16 may overlap</tspan>
      <tspan x="115" dy="24">corporate or VPN ranges: set</tspan>
      <tspan x="115" dy="24">default-address-pools in</tspan>
      <tspan x="115" dy="24">/etc/docker/daemon.json</tspan>
    </text>
  </g>

  <!-- Right Box: Inspect commands -->
  <g id="inspect-commands-box">
    <rect x="800" y="960" width="760" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Terminal prompt outline (stroke 3, green) -->
    <g transform="translate(816, 975)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="44" height="34" rx="4"/>
      <polyline points="12,18 20,23 12,28"/>
      <line x1="24" y1="28" x2="34" y2="28"/>
    </g>
    <!-- Inspect commands Label (monospace) -->
    <text x="880" y="992" font-family="monospace" font-size="24px" fill="#303a36">
      <tspan x="880" dy="0">docker network ls; docker network inspect</tspan>
      <tspan x="880" dy="27">bridge; iptables -t nat -S DOCKER; bridge</tspan>
      <tspan x="880" dy="27">fdb show br docker0</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR: Takeaway ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1100" width="1520" height="60" rx="8" fill="#207448"/>
    <!-- Bottom bar takeaway text -->
    <text x="800" y="1139" font-family="sans-serif" font-size="26px" font-weight="bold" fill="#ffffff" text-anchor="middle">Docker inserts its own rules ahead of the firewall's rules</text>
  </g>
</svg>"""

with open("output.svg", "w") as f:
    f.write(svg_content)

print("Saved clean SVG to output.svg")
