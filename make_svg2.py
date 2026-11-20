svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>What a network namespace owns</title>
  <desc>Visual infographic explaining what a network namespace owns, comparing red and default network namespaces on a host, port space isolation, creation commands, and container namespace entry.</desc>

  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <text x="800" y="62" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">What a network namespace owns</text>

  <g id="host-container">
    <rect x="50" y="95" width="1500" height="1065" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>

    <g transform="translate(80, 114)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="44" rx="4"/>
      <line x1="4" y1="20" x2="52" y2="20" stroke-width="2.5"/>
      <line x1="4" y1="34" x2="52" y2="34" stroke-width="2.5"/>
      <circle cx="12" cy="13" r="2.5" fill="#207448"/>
      <circle cx="18" cy="13" r="2.5" fill="#207448"/>
      <line x1="26" y1="13" x2="44" y2="13" stroke-width="2.5"/>
      <circle cx="12" cy="27" r="2.5" fill="#207448"/>
      <circle cx="18" cy="27" r="2.5" fill="#207448"/>
      <line x1="26" y1="27" x2="44" y2="27" stroke-width="2.5"/>
      <circle cx="12" cy="41" r="2.5" fill="#207448"/>
      <circle cx="18" cy="41" r="2.5" fill="#207448"/>
      <line x1="26" y1="41" x2="44" y2="41" stroke-width="2.5"/>
    </g>
    <text x="155" y="153" font-family="sans-serif" font-size="34" font-weight="bold" fill="#207448">host</text>

    <g id="callout-banner">
      <rect x="250" y="112" width="1270" height="60" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
      <g transform="translate(268, 120)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="14" cy="22" r="10"/>
        <circle cx="36" cy="22" r="10"/>
        <line x1="14" y1="18" x2="14" y2="26"/>
        <line x1="36" y1="18" x2="36" y2="26"/>
        <path d="M 20 14 C 20 8 30 8 30 14"/>
      </g>
      <text x="330" y="151" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">two containers can both serve on port 8080: each has its own port space</text>
    </g>

    <g id="namespace-red">
      <rect x="80" y="215" width="690" height="505" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>

      <g transform="translate(105, 230)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 28 6 L 50 18 L 50 42 L 28 54 L 6 42 L 6 18 Z"/>
        <line x1="28" y1="6" x2="28" y2="30"/>
        <line x1="28" y1="30" x2="50" y2="18"/>
        <line x1="28" y1="30" x2="6" y2="18"/>
        <line x1="28" y1="30" x2="28" y2="54"/>
      </g>
      <text x="175" y="268" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">red</text>

      <g transform="translate(105, 290)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="4" width="28" height="20" rx="3"/>
          <path d="M 10 24 L 10 18 L 22 18 L 22 24"/>
          <line x1="13" y1="9" x2="13" y2="13"/>
          <line x1="16" y1="9" x2="16" y2="13"/>
          <line x1="19" y1="9" x2="19" y2="13"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own interfaces</text>
      </g>

      <g transform="translate(105, 348)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="16" cy="16" r="12"/>
          <line x1="4" y1="16" x2="28" y2="16"/>
          <path d="M 16 4 A 12 12 0 0 1 16 28"/>
          <path d="M 16 4 A 12 12 0 0 0 16 28"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own IP addresses</text>
      </g>

      <g transform="translate(105, 406)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" y1="16" x2="26" y2="16"/>
          <polyline points="20 10 26 16 20 22"/>
          <path d="M 12 16 C 12 24 18 26 26 26"/>
          <polyline points="21 23 26 26 21 29"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own routing tables</text>
      </g>

      <g transform="translate(105, 464)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="8" cy="16" r="4"/>
          <circle cx="24" cy="16" r="4"/>
          <line x1="12" y1="16" x2="20" y2="16"/>
          <path d="M 8 10 L 8 6 L 24 6 L 24 10"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own ARP and ND neighbour tables</text>
      </g>

      <g transform="translate(105, 522)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M 16 3 L 27 7 V 17 C 27 24 16 29 16 29 C 16 29 5 24 5 17 V 7 Z"/>
          <line x1="16" y1="9" x2="16" y2="23"/>
          <line x1="10" y1="15" x2="22" y2="15"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own netfilter rules</text>
      </g>

      <g transform="translate(105, 580)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="10" width="10" height="12" rx="3"/>
          <rect x="19" y="10" width="10" height="12" rx="3"/>
          <line x1="13" y1="16" x2="19" y2="16"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own conntrack table</text>
      </g>

      <g transform="translate(105, 638)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M 4 8 L 12 8 L 15 11 L 28 11 C 29 11 30 12 30 13 L 30 24 C 30 25 29 26 28 26 L 4 26 C 3 26 2 25 2 24 L 2 10 C 2 9 3 8 4 8 Z"/>
          <line x1="9" y1="18" x2="23" y2="18"/>
        </g>
        <text x="64" y="33" font-family="monospace, sans-serif" font-size="24" font-weight="bold" fill="#303a36">own /proc/net</text>
      </g>
    </g>

    <g id="namespace-default">
      <rect x="830" y="215" width="690" height="505" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>

      <g transform="translate(855, 230)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 28 6 L 50 18 L 50 42 L 28 54 L 6 42 L 6 18 Z"/>
        <line x1="28" y1="6" x2="28" y2="30"/>
        <line x1="28" y1="30" x2="50" y2="18"/>
        <line x1="28" y1="30" x2="6" y2="18"/>
        <line x1="28" y1="30" x2="28" y2="54"/>
      </g>
      <text x="925" y="268" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">default</text>

      <g transform="translate(855, 290)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="4" width="28" height="20" rx="3"/>
          <path d="M 10 24 L 10 18 L 22 18 L 22 24"/>
          <line x1="13" y1="9" x2="13" y2="13"/>
          <line x1="16" y1="9" x2="16" y2="13"/>
          <line x1="19" y1="9" x2="19" y2="13"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own interfaces</text>
      </g>

      <g transform="translate(855, 348)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="16" cy="16" r="12"/>
          <line x1="4" y1="16" x2="28" y2="16"/>
          <path d="M 16 4 A 12 12 0 0 1 16 28"/>
          <path d="M 16 4 A 12 12 0 0 0 16 28"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own IP addresses</text>
      </g>

      <g transform="translate(855, 406)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" y1="16" x2="26" y2="16"/>
          <polyline points="20 10 26 16 20 22"/>
          <path d="M 12 16 C 12 24 18 26 26 26"/>
          <polyline points="21 23 26 26 21 29"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own routing tables</text>
      </g>

      <g transform="translate(855, 464)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="8" cy="16" r="4"/>
          <circle cx="24" cy="16" r="4"/>
          <line x1="12" y1="16" x2="20" y2="16"/>
          <path d="M 8 10 L 8 6 L 24 6 L 24 10"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own ARP and ND neighbour tables</text>
      </g>

      <g transform="translate(855, 522)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M 16 3 L 27 7 V 17 C 27 24 16 29 16 29 C 16 29 5 24 5 17 V 7 Z"/>
          <line x1="16" y1="9" x2="16" y2="23"/>
          <line x1="10" y1="15" x2="22" y2="15"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own netfilter rules</text>
      </g>

      <g transform="translate(855, 580)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="10" width="10" height="12" rx="3"/>
          <rect x="19" y="10" width="10" height="12" rx="3"/>
          <line x1="13" y1="16" x2="19" y2="16"/>
        </g>
        <text x="64" y="33" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">own conntrack table</text>
      </g>

      <g transform="translate(855, 638)">
        <rect x="0" y="0" width="640" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <g transform="translate(16, 8)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M 4 8 L 12 8 L 15 11 L 28 11 C 29 11 30 12 30 13 L 30 24 C 30 25 29 26 28 26 L 4 26 C 3 26 2 25 2 24 L 2 10 C 2 9 3 8 4 8 Z"/>
          <line x1="9" y1="18" x2="23" y2="18"/>
        </g>
        <text x="64" y="33" font-family="monospace, sans-serif" font-size="24" font-weight="bold" fill="#303a36">own /proc/net</text>
      </g>
    </g>

    <g id="commands-under-red">
      <rect x="80" y="765" width="690" height="365" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>

      <g transform="translate(105, 785)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="48" height="42" rx="6"/>
        <line x1="4" y1="18" x2="52" y2="18" stroke-width="2.5"/>
        <polyline points="14 28 20 34 14 40" stroke-width="3"/>
        <line x1="26" y1="40" x2="38" y2="40" stroke-width="3"/>
      </g>

      <g transform="translate(105, 848)">
        <circle cx="24" cy="28" r="18" fill="#207448"/>
        <text x="24" y="36" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
        <rect x="58" y="0" width="582" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <text x="80" y="37" font-family="monospace, sans-serif" font-size="25" font-weight="bold" fill="#207448">ip netns add red</text>
      </g>

      <g transform="translate(105, 920)">
        <circle cx="24" cy="46" r="18" fill="#207448"/>
        <text x="24" y="54" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
        <rect x="58" y="0" width="582" height="92" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <text x="80" y="37" font-family="monospace, sans-serif" font-size="25" font-weight="bold" fill="#207448">ip netns exec red ip link</text>
        <text x="80" y="73" font-family="sans-serif" font-size="24" fill="#303a36">(only a down loopback at first)</text>
      </g>

      <g transform="translate(105, 1028)">
        <circle cx="24" cy="28" r="18" fill="#207448"/>
        <text x="24" y="36" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
        <rect x="58" y="0" width="582" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
        <text x="80" y="37" font-family="monospace, sans-serif" font-size="25" font-weight="bold" fill="#207448">ip -n red link set lo up</text>
      </g>
    </g>

    <g id="orange-note">
      <rect x="830" y="765" width="690" height="365" rx="14" fill="#fff8f2" stroke="#db8129" stroke-width="3"/>

      <g transform="translate(1147, 810)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="48" height="42" rx="6"/>
        <line x1="16" y1="27" x2="36" y2="27" stroke-width="4"/>
        <polyline points="28 19 36 27 28 35" stroke-width="4"/>
      </g>

      <g transform="translate(865, 890)">
        <rect x="0" y="0" width="620" height="200" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="2"/>
        <text x="310" y="80" text-anchor="middle" font-family="monospace, sans-serif" font-size="25" font-weight="bold" fill="#db8129">nsenter -t &lt;pid&gt; -n ip addr</text>
        <text x="310" y="140" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">enters a container namespace by PID</text>
      </g>
    </g>
  </g>
</svg>"""

import pathlib, subprocess
pathlib.Path("test_output2.svg").write_text(svg_content)
d = pathlib.Path('/tmp/svgcheck')
subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,1200',
    f'--screenshot={d}/n25-netns2.png',
    f'file://{pathlib.Path("test_output2.svg").resolve()}'
], capture_output=True)
print("Updated screenshot saved!")
