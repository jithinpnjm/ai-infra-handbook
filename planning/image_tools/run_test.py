#!/usr/bin/env python3
from test_host_key_audit import test_svg

svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1040" width="1600" height="1040">
  <title>Host key change and automation key hardening</title>
  <desc>Infographic illustrating the process of handling host key changes on re-imaged nodes and hardening automation SSH access via sshd_config and Ansible authorized_key.</desc>

  <!-- Background -->
  <rect width="1600" height="1040" fill="#f5f8f5"/>

  <!-- Diagram Title -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#207448">Host key change and automation key hardening</text>

  <!-- ==================== LEFT PANEL ==================== -->
  <g id="left-panel">
    <rect x="40" y="90" width="740" height="910" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Left Card 1: Re-imaged node changes host key -->
    <rect x="60" y="110" width="700" height="180" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <g transform="translate(680, 130)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="44" rx="6"/>
      <line x1="4" y1="20" x2="52" y2="20"/>
      <line x1="4" y1="34" x2="52" y2="34"/>
      <circle cx="12" cy="13" r="2.5" fill="#207448"/>
      <circle cx="12" cy="27" r="2.5" fill="#207448"/>
      <circle cx="12" cy="41" r="2.5" fill="#207448"/>
      <line x1="36" y1="13" x2="44" y2="13"/>
      <line x1="36" y1="27" x2="44" y2="27"/>
      <line x1="36" y1="41" x2="44" y2="41"/>
    </g>
    <text x="85" y="190" font-family="sans-serif" font-size="26" fill="#303a36">
      <tspan x="85" dy="0">a re-imaged node changes its </tspan>
      <tspan x="85" dy="38" font-family="monospace">Ed25519 host key</tspan>
    </text>

    <!-- Left Card 2: OpenSSH aborts with verification failed -->
    <rect x="60" y="315" width="700" height="235" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <g transform="translate(680, 335)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 4 L 8 13 L 8 28 C 8 42 28 52 28 52 C 28 52 48 42 48 28 L 48 13 Z"/>
      <line x1="28" y1="18" x2="28" y2="32"/>
      <circle cx="28" cy="40" r="2.5" fill="#207448"/>
    </g>
    <text x="85" y="375" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="85" dy="0">OpenSSH aborts with </tspan>
      <tspan x="85" dy="38" font-family="monospace">Host key verification failed and </tspan>
      <tspan x="85" dy="38" font-family="monospace">WARNING REMOTE HOST </tspan>
      <tspan x="85" dy="38" font-family="monospace">IDENTIFICATION HAS CHANGED</tspan>
    </text>

    <!-- Left Card 3: Confirm rebuild expected -->
    <rect x="60" y="575" width="700" height="155" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <g transform="translate(680, 595)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <polyline points="16,28 24,36 40,20"/>
    </g>
    <text x="85" y="665" font-family="sans-serif" font-size="26" fill="#303a36">confirm the rebuild was expected</text>

    <!-- Left Card 4: ssh-keygen and ssh-keyscan -->
    <rect x="60" y="755" width="700" height="225" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <g transform="translate(680, 775)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="40" rx="6"/>
      <polyline points="14,20 22,28 14,36"/>
      <line x1="26" y1="36" x2="38" y2="36"/>
    </g>
    <text x="85" y="820" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="85" dy="0">then ssh-keygen -R 192.168.33.10 and </tspan>
      <tspan x="85" dy="38">ssh-keyscan -H 192.168.33.10 </tspan>
      <tspan x="85" dy="38" font-family="sans-serif">appended to known_hosts</tspan>
    </text>
  </g>

  <!-- ==================== RIGHT PANEL ==================== -->
  <g id="right-panel">
    <rect x="820" y="90" width="740" height="910" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Right Card 1: sshd_config hardening -->
    <rect x="840" y="110" width="700" height="240" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <g transform="translate(1460, 130)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="18" width="40" height="32" rx="6"/>
      <path d="M 16 18 L 16 12 A 12 12 0 0 1 40 12 L 40 18"/>
      <circle cx="28" cy="32" r="3.5" fill="#207448"/>
      <line x1="28" y1="35.5" x2="28" y2="42"/>
    </g>
    <text x="865" y="190" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">
      <tspan x="865" dy="0">sshd_config </tspan>
      <tspan x="865" dy="42" font-size="24" font-weight="normal">PasswordAuthentication no and </tspan>
      <tspan x="865" dy="38" font-size="24" font-weight="normal">PermitRootLogin no</tspan>
    </text>

    <!-- Right Card 2: ansible.posix.authorized_key options -->
    <rect x="840" y="375" width="700" height="245" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <g transform="translate(1460, 395)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="20" cy="22" r="10"/>
      <line x1="27" y1="29" x2="48" y2="50"/>
      <line x1="39" y1="41" x2="45" y2="35"/>
      <line x1="43" y1="45" x2="49" y2="39"/>
    </g>
    <text x="865" y="450" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="865" dy="0">ansible.posix.authorized_key with </tspan>
      <tspan x="865" dy="40">key_options no-port-forwarding and </tspan>
      <tspan x="865" dy="40" font-family="sans-serif">from the control node IP</tspan>
    </text>

    <!-- Right Card 3: exclusive true (Orange highlight) -->
    <rect x="840" y="645" width="700" height="335" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <g transform="translate(1460, 665)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="18" width="40" height="32" rx="6"/>
      <path d="M 16 18 L 16 12 A 12 12 0 0 1 40 12 L 40 18"/>
      <line x1="18" y1="34" x2="38" y2="34"/>
    </g>
    <text x="865" y="740" font-family="monospace" font-size="26" fill="#303a36">
      <tspan x="865" dy="0" fill="#db8129" font-weight="bold">exclusive true </tspan>
      <tspan x="865" dy="46" font-family="sans-serif" font-size="24">removes unauthorized keys so a </tspan>
      <tspan x="865" dy="40" font-family="sans-serif" font-size="24">departed admin's key stops working</tspan>
    </text>
  </g>
</svg>'''

test_svg(svg)
