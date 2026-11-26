#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, os

H = 1200

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">
  <title>A warning signal, a clean stop, and a requeue</title>
  <desc>Visual explanation of Slurm warning signal USR1 triggering bash trap, clean SIGTERM stop on training process, and automatic job requeue via slurmctld.</desc>

  <defs>
    <!-- Green arrowhead for standard step arrows (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
    <!-- Orange arrowhead for the single most important arrow (18px) -->
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129"/>
    </marker>
  </defs>

  <!-- ==================== BACKGROUND ==================== -->
  <rect width="100%" height="100%" fill="#f5f8f5"/>

  <!-- Main Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">A warning signal, a clean stop, and a requeue</text>

  <!-- ==================== THREE SWIM LANE BACKGROUNDS ==================== -->
  <!-- Lane 1 Background: Batch shell -->
  <rect x="40" y="95" width="1520" height="275" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <!-- Lane 2 Background: Training -->
  <rect x="40" y="415" width="1520" height="275" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <!-- Lane 3 Background: slurmctld -->
  <rect x="40" y="735" width="1520" height="285" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

  <!-- ==================== LANE 1 HEADER ==================== -->
  <rect x="55" y="110" width="200" height="245" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(127, 130)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="42" rx="6" fill="#f5f8f5"/>
    <path d="M 14 20 L 22 27 L 14 34"/>
    <line x1="26" y1="34" x2="38" y2="34"/>
  </g>
  <text x="155" y="240" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">
    <tspan x="155" dy="0">Batch shell</tspan>
    <tspan x="155" dy="34">(the script)</tspan>
  </text>

  <!-- ==================== LANE 2 HEADER ==================== -->
  <rect x="55" y="430" width="200" height="245" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(127, 445)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="12" y="12" width="32" height="32" rx="4" fill="#f5f8f5"/>
    <path d="M 20 4 L 20 12 M 28 4 L 28 12 M 36 4 L 36 12"/>
    <path d="M 20 44 L 20 52 M 28 44 L 28 52 M 36 44 L 36 52"/>
    <path d="M 4 20 L 12 20 M 4 28 L 12 28 M 4 36 L 12 36"/>
    <path d="M 44 20 L 52 20 M 44 28 L 52 28 M 44 36 L 52 36"/>
  </g>
  <text x="155" y="545" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#207448">
    <tspan x="155" dy="0">Training</tspan>
    <tspan x="155" dy="32">(srun python</tspan>
    <tspan x="155" dy="32">train.py)</tspan>
  </text>

  <!-- ==================== LANE 3 HEADER ==================== -->
  <rect x="55" y="755" width="200" height="245" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(127, 775)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="28" cy="28" r="12" fill="#f5f8f5"/>
    <path d="M 28 4 L 28 10 M 28 46 L 28 52 M 4 28 L 10 28 M 46 28 L 52 28 M 11 11 L 15 15 M 41 41 L 45 45 M 11 45 L 15 41 M 41 15 L 45 11"/>
  </g>
  <text x="155" y="885" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">
    <tspan x="155" dy="0">slurmctld</tspan>
    <tspan x="155" dy="34">(controller)</tspan>
  </text>

  <!-- ==================== STEP 1 ==================== -->
  <!-- Number circle 1 -->
  <circle cx="290" cy="125" r="24" fill="#207448"/>
  <text x="290" y="134" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>

  <!-- Arriving Arrow 1 (at y=168) -->
  <line x1="265" y1="168" x2="575" y2="168" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>
  <!-- Arrow 1 label (above arrow, text-anchor="start") -->
  <text x="322" y="122" text-anchor="start" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="322" dy="0">#SBATCH</tspan>
    <tspan x="322" dy="26">--signal=B:USR1@600</tspan>
  </text>

  <!-- Step 1 Note Box -->
  <rect x="270" y="185" width="310" height="165" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="425" y="225" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="425" dy="0">600 seconds before</tspan>
    <tspan x="425" dy="30">the time limit,</tspan>
    <tspan x="425" dy="30">the batch shell</tspan>
    <tspan x="425" dy="30">receives USR1</tspan>
  </text>

  <!-- ==================== STEP 2 ==================== -->
  <!-- Number circle 2 -->
  <circle cx="645" cy="130" r="24" fill="#207448"/>
  <text x="645" y="139" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>

  <!-- Step 2 Box -->
  <rect x="620" y="175" width="365" height="175" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(774, 190)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 28 6 L 48 15 L 48 29 C 48 41 28 49 28 49 C 28 49 8 41 8 29 L 8 15 Z" fill="#e8f1ea"/>
    <path d="M 20 27 L 26 33 L 37 21"/>
  </g>
  <text x="802" y="285" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="802" dy="0">trap runs</tspan>
    <tspan x="802" dy="32">checkpoint_and_requeue</tspan>
  </text>

  <!-- ==================== STEP 3 ==================== -->
  <!-- Number circle 3 (in gap between lanes) -->
  <circle cx="745" cy="395" r="24" fill="#207448"/>
  <text x="745" y="404" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>

  <!-- Vertical Arrow from Step 2 to Step 3 box -->
  <line x1="802" y1="350" x2="802" y2="495" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>
  <!-- Step 3 Arrow label -->
  <text x="822" y="430" text-anchor="start" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="822" dy="0">kill -TERM on the</tspan>
    <tspan x="822" dy="28">training process</tspan>
  </text>

  <!-- Step 3 Target Box in Lane 2 -->
  <rect x="585" y="505" width="440" height="165" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(777, 516)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <ellipse cx="28" cy="14" rx="20" ry="8" fill="#e8f1ea"/>
    <path d="M 8 14 V 30 C 8 34 17 38 28 38 C 39 38 48 34 48 30 V 14"/>
    <path d="M 8 30 V 42 C 8 46 17 50 28 50 C 39 50 48 46 48 42 V 30"/>
  </g>
  <text x="805" y="612" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="805" dy="0">the training program writes</tspan>
    <tspan x="805" dy="32">a checkpoint on SIGTERM</tspan>
  </text>

  <!-- ==================== STEP 4 ==================== -->
  <!-- Number circle 4 -->
  <circle cx="1055" cy="130" r="24" fill="#207448"/>
  <text x="1055" y="139" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>

  <!-- Step 4 Box -->
  <rect x="1030" y="175" width="280" height="175" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(1142, 188)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="28" cy="28" r="22" fill="#e8f1ea"/>
    <polyline points="28,14 28,28 38,28"/>
  </g>
  <text x="1170" y="287" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="1170" dy="0">wait for training</tspan>
    <tspan x="1170" dy="32">to exit</tspan>
  </text>

  <!-- ==================== STEP 5 ==================== -->
  <!-- Number circle 5 -->
  <circle cx="1395" cy="395" r="24" fill="#207448"/>
  <text x="1395" y="404" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>

  <!-- Step 5 Orange Arrow -->
  <line x1="1355" y1="350" x2="1355" y2="785" stroke="#db8129" stroke-width="5" marker-end="url(#arrow-orange)"/>
  <text x="1335" y="555" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="24" font-weight="bold" fill="#db8129">
    <tspan x="1335" dy="0">scontrol requeue</tspan>
    <tspan x="1335" dy="30">$SLURM_JOB_ID</tspan>
  </text>

  <!-- ==================== STEP 6 ==================== -->
  <!-- Number circle 6 -->
  <circle cx="1055" cy="755" r="24" fill="#207448"/>
  <text x="1055" y="764" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">6</text>

  <!-- Step 6 Box -->
  <rect x="1030" y="795" width="500" height="100" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <!-- Queue Icon (56x56 px, stroke 4) -->
  <g transform="translate(1050, 817)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="12" rx="3" fill="#e8f1ea"/>
    <rect x="4" y="24" width="48" height="12" rx="3" fill="#e8f1ea"/>
    <path d="M 4 42 H 36 L 46 42"/>
  </g>
  <text x="1325" y="842" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="1325" dy="0">job goes back to the</tspan>
    <tspan x="1325" dy="32">queue with the same job ID</tspan>
  </text>

  <!-- Step 6 Note -->
  <rect x="1030" y="905" width="500" height="97" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="1280" y="946" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="24" fill="#303a36">
    <tspan x="1280" dy="0">the next run sees</tspan>
    <tspan x="1280" dy="30">SLURM_RESTART_COUNT increase</tspan>
  </text>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <rect x="40" y="1065" width="1520" height="80" rx="12" fill="#207448"/>
  <text x="800" y="1113" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Periodic checkpoints are the real safety net; the signal handler saves the wait for the next checkpoint.</text>

</svg>'''

open("candidate.svg", "w").write(svg)
print("Wrote candidate.svg")
