import xml.etree.ElementTree as ET
import re

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180" width="1600" height="1180">
  <title>No space left on device: seven checks, one command each</title>
  <desc>Seven causes of ENOSPC disk space errors, their diagnostic commands, and their remediation steps.</desc>

  <!-- Background -->
  <rect width="1600" height="1180" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">No space left on device: seven checks, one command each</text>

  <!-- Top Symptom Box -->
  <g id="top-symptom-box">
    <rect x="40" y="90" width="1520" height="76" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(62, 103)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="25,5 45,45 5,45" />
      <line x1="25" y1="18" x2="25" y2="31" />
      <circle cx="25" cy="38" r="2" fill="#207448" />
    </g>
    <text x="130" y="137" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">No space left on device (ENOSPC)</text>
    <text x="1530" y="137" text-anchor="end" font-family="sans-serif" font-size="24" fill="#303a36">one failed write proves only that one write failed</text>
  </g>

  <!-- ==================== ROW 1 ==================== -->
  <g id="row-1">
    <rect x="40" y="188" width="1520" height="106" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Col 1: Cause background -->
    <path d="M 52 188 L 480 188 L 480 294 L 52 294 A 12 12 0 0 1 40 282 L 40 200 A 12 12 0 0 1 52 188 Z" fill="#e8f1ea" />
    <circle cx="74" cy="241" r="24" fill="#207448" />
    <text x="74" y="241" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
    <!-- Icon 1: Disk cylinder -->
    <g transform="translate(106, 217)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="24" cy="10" rx="20" ry="7" />
      <path d="M 4 10 V 38 C 4 45 44 45 44 38 V 10" />
      <path d="M 4 24 C 4 31 44 31 44 24" />
    </g>
    <text x="172" y="231" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="172" dy="0">Data blocks </tspan>
      <tspan x="172" dy="32">exhausted</tspan>
    </text>
    <!-- Col 2: Check box -->
    <rect x="492" y="200" width="426" height="82" rx="8" fill="#f0f6f2" stroke="#207448" stroke-width="1.5" />
    <text x="705" y="249" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">df -h</text>
    <!-- Col 3: Fix -->
    <text x="1245" y="231" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1245" dy="0">Delete or move data; </tspan>
      <tspan x="1245" dy="30">grow the filesystem</tspan>
    </text>
  </g>

  <!-- ==================== ROW 2 (Orange Outline) ==================== -->
  <g id="row-2">
    <rect x="40" y="308" width="1520" height="106" rx="12" fill="#fffdfa" stroke="#db8129" stroke-width="3.5" />
    <!-- Col 1: Cause background -->
    <path d="M 52 308 L 480 308 L 480 414 L 52 414 A 12 12 0 0 1 40 402 L 40 320 A 12 12 0 0 1 52 308 Z" fill="#fef4eb" />
    <circle cx="74" cy="361" r="24" fill="#207448" />
    <text x="74" y="361" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
    <!-- Icon 2: Inode index table -->
    <g transform="translate(106, 337)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="36" height="36" rx="4" />
      <line x1="6" y1="18" x2="42" y2="18" />
      <line x1="18" y1="6" x2="18" y2="42" />
      <circle cx="12" cy="12" r="2.5" fill="#db8129" />
      <circle cx="30" cy="12" r="2.5" fill="#db8129" />
      <circle cx="12" cy="30" r="2.5" fill="#db8129" />
      <circle cx="30" cy="30" r="2.5" fill="#db8129" />
    </g>
    <text x="172" y="371" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Inodes exhausted</text>
    <!-- Col 2: Check box -->
    <rect x="492" y="320" width="426" height="82" rx="8" fill="#fff9f2" stroke="#db8129" stroke-width="1.5" />
    <text x="705" y="369" text-anchor="middle" font-family="monospace" font-size="24" fill="#db8129">df -i</text>
    <!-- Col 3: Fix -->
    <text x="1245" y="351" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1245" dy="0">Delete files; recreate with more inodes; </tspan>
      <tspan x="1245" dy="30">prefer XFS or bundled shards</tspan>
    </text>
  </g>

  <!-- ==================== ROW 3 ==================== -->
  <g id="row-3">
    <rect x="40" y="428" width="1520" height="106" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Col 1: Cause background -->
    <path d="M 52 428 L 480 428 L 480 534 L 52 534 A 12 12 0 0 1 40 522 L 40 440 A 12 12 0 0 1 52 428 Z" fill="#e8f1ea" />
    <circle cx="74" cy="481" r="24" fill="#207448" />
    <text x="74" y="481" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
    <!-- Icon 3: Lock -->
    <g transform="translate(106, 457)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="20" width="32" height="24" rx="4" />
      <path d="M 14 20 V 13 C 14 7.5 34 7.5 34 13 V 20" />
      <circle cx="24" cy="31" r="3" fill="#207448" />
      <line x1="24" y1="34" x2="24" y2="38" />
    </g>
    <text x="172" y="471" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="172" dy="0">Mounted </tspan>
      <tspan x="172" dy="32">read-only</tspan>
    </text>
    <!-- Col 2: Check box -->
    <rect x="492" y="440" width="426" height="82" rx="8" fill="#f0f6f2" stroke="#207448" stroke-width="1.5" />
    <text x="705" y="469" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">mount | grep &quot; ro,&quot;</text>
    <text x="705" y="501" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">dmesg</text>
    <!-- Col 3: Fix -->
    <text x="1245" y="471" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1245" dy="0">Find the I/O error cause; </tspan>
      <tspan x="1245" dy="30">repair; remount</tspan>
    </text>
  </g>

  <!-- ==================== ROW 4 ==================== -->
  <g id="row-4">
    <rect x="40" y="548" width="1520" height="106" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Col 1: Cause background -->
    <path d="M 52 548 L 480 548 L 480 654 L 52 654 A 12 12 0 0 1 40 642 L 40 560 A 12 12 0 0 1 52 548 Z" fill="#e8f1ea" />
    <circle cx="74" cy="601" r="24" fill="#207448" />
    <text x="74" y="601" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
    <!-- Icon 4: Gauge / limit meter -->
    <g transform="translate(106, 577)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 36 A 20 20 0 1 1 42 36" />
      <line x1="24" y1="36" x2="38" y2="20" stroke-width="4" />
      <circle cx="24" cy="36" r="4" fill="#207448" />
    </g>
    <text x="172" y="611" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Quota reached</text>
    <!-- Col 2: Check box -->
    <rect x="492" y="560" width="426" height="82" rx="8" fill="#f0f6f2" stroke="#207448" stroke-width="1.5" />
    <text x="590" y="589" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">quota -u</text>
    <text x="815" y="589" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">xfs_quota</text>
    <text x="705" y="621" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">repquota</text>
    <!-- Col 3: Fix -->
    <text x="1245" y="610" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">Raise the quota or clean up</text>
  </g>

  <!-- ==================== ROW 5 ==================== -->
  <g id="row-5">
    <rect x="40" y="668" width="1520" height="106" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Col 1: Cause background -->
    <path d="M 52 668 L 480 668 L 480 774 L 52 774 A 12 12 0 0 1 40 762 L 40 680 A 12 12 0 0 1 52 668 Z" fill="#e8f1ea" />
    <circle cx="74" cy="721" r="24" fill="#207448" />
    <text x="74" y="721" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
    <!-- Icon 5: Folder / mount location -->
    <g transform="translate(106, 697)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 12 L 18 12 L 22 18 L 42 18 A 3 3 0 0 1 45 21 L 45 39 A 3 3 0 0 1 42 42 L 6 42 A 3 3 0 0 1 3 39 L 3 15 A 3 3 0 0 1 6 12 Z" />
      <line x1="24" y1="26" x2="24" y2="34" />
      <circle cx="24" cy="38" r="1.5" fill="#207448" />
    </g>
    <text x="172" y="711" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="172" dy="0">Wrong place, </tspan>
      <tspan x="172" dy="32">not mounted</tspan>
    </text>
    <!-- Col 2: Check box -->
    <rect x="492" y="680" width="426" height="82" rx="8" fill="#f0f6f2" stroke="#207448" stroke-width="1.5" />
    <text x="705" y="709" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">findmnt -T /path</text>
    <text x="705" y="741" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">df /path</text>
    <!-- Col 3: Fix -->
    <text x="1245" y="711" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1245" dy="0">Mount it properly; </tspan>
      <tspan x="1245" dy="30">move the stray data</tspan>
    </text>
  </g>

  <!-- ==================== ROW 6 ==================== -->
  <g id="row-6">
    <rect x="40" y="788" width="1520" height="106" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Col 1: Cause background -->
    <path d="M 52 788 L 480 788 L 480 894 L 52 894 A 12 12 0 0 1 40 882 L 40 800 A 12 12 0 0 1 52 788 Z" fill="#e8f1ea" />
    <circle cx="74" cy="841" r="24" fill="#207448" />
    <text x="74" y="841" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">6</text>
    <!-- Icon 6: Trash / open fd -->
    <g transform="translate(106, 817)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="6" y1="14" x2="42" y2="14" />
      <path d="M 18 14 V 9 A 2 2 0 0 1 20 7 L 28 7 A 2 2 0 0 1 30 9 V 14" />
      <path d="M 10 14 L 13 41 A 3 3 0 0 0 16 44 L 32 44 A 3 3 0 0 0 35 41 L 38 14" />
      <line x1="20" y1="21" x2="20" y2="37" />
      <line x1="28" y1="21" x2="28" y2="37" />
    </g>
    <text x="172" y="831" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="172" dy="0">Deleted files </tspan>
      <tspan x="172" dy="32">still open</tspan>
    </text>
    <!-- Col 2: Check box -->
    <rect x="492" y="800" width="426" height="82" rx="8" fill="#f0f6f2" stroke="#207448" stroke-width="1.5" />
    <text x="705" y="849" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">lsof +L1</text>
    <!-- Col 3: Fix -->
    <text x="1245" y="831" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1245" dy="0">Restart the holder, or truncate </tspan>
      <tspan x="1245" dy="30">through /proc/PID/fd/N</tspan>
    </text>
  </g>

  <!-- ==================== ROW 7 ==================== -->
  <g id="row-7">
    <rect x="40" y="908" width="1520" height="106" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Col 1: Cause background -->
    <path d="M 52 908 L 480 908 L 480 1014 L 52 1014 A 12 12 0 0 1 40 1002 L 40 920 A 12 12 0 0 1 52 908 Z" fill="#e8f1ea" />
    <circle cx="74" cy="961" r="24" fill="#207448" />
    <text x="74" y="961" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">7</text>
    <!-- Icon 7: Root reservation shield -->
    <g transform="translate(106, 937)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 24 6 L 42 12 V 24 C 42 35 24 43 24 43 C 24 43 6 35 6 24 V 12 Z" />
      <circle cx="24" cy="22" r="3.5" fill="#207448" />
      <line x1="24" y1="25.5" x2="24" y2="32" />
    </g>
    <text x="172" y="951" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="172" dy="0">Reserved blocks </tspan>
      <tspan x="172" dy="32">for root</tspan>
    </text>
    <!-- Col 2: Check box -->
    <rect x="492" y="920" width="426" height="82" rx="8" fill="#f0f6f2" stroke="#207448" stroke-width="1.5" />
    <text x="705" y="969" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">tune2fs -l | grep Reserved</text>
    <!-- Col 3: Fix -->
    <text x="1245" y="951" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1245" dy="0">Lower the reservation </tspan>
      <tspan x="1245" dy="30">on data disks</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1036" width="1520" height="80" rx="14" fill="#207448" />
    <text x="800" y="1070" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">
      <tspan x="800" dy="0">Check bytes, inodes, read-only, quota, mount point, </tspan>
      <tspan x="800" dy="32">open files and reserved blocks before you delete anything</tspan>
    </text>
  </g>
</svg>'''

open("candidate_test.svg", "w").write(svg_code)
print("Saved candidate_test.svg")
