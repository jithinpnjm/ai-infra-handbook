import xml.etree.ElementTree as ET
import re

def build_svg():
    W = 1600
    H = 1200
    
    # Step box parameters
    step_x = 40
    step_w = 1090
    step_h = 96
    gap = 40
    step1_y = 145
    
    # Step 5 coordinates
    step5_y = step1_y + 4 * (step_h + gap)  # 145 + 4*136 = 689
    step5_mid_y = step5_y + step_h // 2      # 689 + 48 = 737
    
    # Gap between steps and budget box
    gap_x = step_x + step_w                 # 1130
    gap_w = 110
    budget_x = gap_x + gap_w                # 1240
    budget_w = 320
    budget_y = step5_mid_y - 115            # 737 - 115 = 622
    budget_h = 230
    
    # Takeaway bar
    step7_bottom = step1_y + 6 * (step_h + gap) + step_h # 145 + 6*136 + 96 = 1057
    takeaway_y = step7_bottom + 40                       # 1097
    takeaway_x = 40
    takeaway_w = 1520
    takeaway_h = 56
    
    step_pitch = step_h + gap # 136
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <title>A bad rollout, from first failed request to the rollback</title>
  <desc>Visual infographic explaining the sequence of a bad rollout, multiwindow error budget burn rate alerting, page firing, rollback, and budget spent.</desc>

  <defs>
    <!-- 18px proportional green arrowhead marker -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="#f5f8f5" />

  <!-- Title (48px bold, wrapped in tspans to guarantee >= 16px conservative padding) -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">A bad rollout, </tspan>
    <tspan x="800" dy="54">from first failed request to the rollback</tspan>
  </text>

  <!-- ==================== STEP 1 ==================== -->
  <g id="step-1">
    <rect x="{step_x}" y="{step1_y}" width="{step_w}" height="{step_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 1 -->
    <circle cx="80" cy="{step1_y + 30}" r="24" fill="#207448" />
    <text x="80" y="{step1_y + 39}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <!-- Icon 1: Deploy package / rocket (40x40) -->
    <g transform="translate(120, {step1_y + 10})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 20 2 C 20 2 31 7 33 20 L 25 28 L 12 15 L 20 2 Z" />
      <circle cx="22" cy="12" r="2.5" fill="#207448" />
      <path d="M 12 15 L 5 19 L 9 24 L 14 24" />
      <path d="M 25 28 L 21 35 L 16 31 L 16 26" />
      <path d="M 9 31 L 4 36" />
    </g>
    <!-- Step 1 Title -->
    <text x="175" y="{step1_y + 35}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Rollout starts</text>
    <!-- Step 1 Detail -->
    <text x="60" y="{step1_y + 74}" font-family="sans-serif" font-size="24" fill="#303a36">A rollout breaks the model for 12 minutes and all requests fail.</text>
  </g>

  <!-- Arrow 1 -> 2 -->
  <line x1="80" y1="{step1_y + step_h}" x2="80" y2="{step1_y + step_pitch}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />

  <!-- ==================== STEP 2 ==================== -->
  <g id="step-2">
    <rect x="{step_x}" y="{step1_y + step_pitch}" width="{step_w}" height="{step_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 2 -->
    <circle cx="80" cy="{step1_y + step_pitch + 30}" r="24" fill="#207448" />
    <text x="80" y="{step1_y + step_pitch + 39}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <!-- Icon 2: Gateway / Traffic router (40x40) -->
    <g transform="translate(120, {step1_y + step_pitch + 10})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="32" height="28" rx="5" />
      <line x1="4" y1="16" x2="36" y2="16" />
      <circle cx="11" cy="11" r="2" fill="#207448" />
      <circle cx="17" cy="11" r="2" fill="#207448" />
      <line x1="12" y1="25" x2="28" y2="25" />
      <polyline points="22,21 28,25 22,29" />
    </g>
    <!-- Step 2 Title -->
    <text x="175" y="{step1_y + step_pitch + 35}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">First failing requests reach the gateway</text>
    <!-- Step 2 Detail -->
    <text x="60" y="{step1_y + step_pitch + 74}" font-family="sans-serif" font-size="24" fill="#303a36">The error ratio is 100 percent.</text>
  </g>

  <!-- Arrow 2 -> 3 -->
  <line x1="80" y1="{step1_y + step_pitch + step_h}" x2="80" y2="{step1_y + 2 * step_pitch}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />

  <!-- ==================== STEP 3 ==================== -->
  <g id="step-3">
    <rect x="{step_x}" y="{step1_y + 2 * step_pitch}" width="{step_w}" height="{step_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 3 -->
    <circle cx="80" cy="{step1_y + 2 * step_pitch + 30}" r="24" fill="#207448" />
    <text x="80" y="{step1_y + 2 * step_pitch + 39}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <!-- Icon 3: Fast burn trend line / flame chart (40x40) -->
    <g transform="translate(120, {step1_y + 2 * step_pitch + 10})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="4,34 4,6 36,6" />
      <polyline points="6,28 14,26 24,16 34,9" />
      <line x1="10" y1="18" x2="34" y2="18" stroke-width="2" />
    </g>
    <!-- Step 3 Title -->
    <text x="175" y="{step1_y + 2 * step_pitch + 35}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Fast burn short window goes above the threshold</text>
    <!-- Step 3 Detail -->
    <text x="60" y="{step1_y + 2 * step_pitch + 74}" font-family="sans-serif" font-size="24" fill="#303a36">The 5 minute window has enough data and is above 1.44 percent.</text>
  </g>

  <!-- Arrow 3 -> 4 -->
  <line x1="80" y1="{step1_y + 2 * step_pitch + step_h}" x2="80" y2="{step1_y + 3 * step_pitch}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />

  <!-- ==================== STEP 4 ==================== -->
  <g id="step-4">
    <rect x="{step_x}" y="{step1_y + 3 * step_pitch}" width="{step_w}" height="{step_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 4 -->
    <circle cx="80" cy="{step1_y + 3 * step_pitch + 30}" r="24" fill="#207448" />
    <text x="80" y="{step1_y + 3 * step_pitch + 39}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <!-- Icon 4: Dual windows / catching up (40x40) -->
    <g transform="translate(120, {step1_y + 3 * step_pitch + 10})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="20" height="26" rx="4" />
      <rect x="16" y="4" width="20" height="26" rx="4" />
      <line x1="22" y1="13" x2="30" y2="13" />
    </g>
    <!-- Step 4 Title -->
    <text x="175" y="{step1_y + 3 * step_pitch + 35}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Long window is still catching up</text>
    <!-- Step 4 Detail -->
    <text x="60" y="{step1_y + 3 * step_pitch + 74}" font-family="sans-serif" font-size="24" fill="#303a36">The page waits until both windows agree.</text>
  </g>

  <!-- Arrow 4 -> 5 -->
  <line x1="80" y1="{step1_y + 3 * step_pitch + step_h}" x2="80" y2="{step5_y}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />

  <!-- ==================== STEP 5 (Single Orange Highlight) ==================== -->
  <g id="step-5">
    <rect x="{step_x}" y="{step5_y}" width="{step_w}" height="{step_h}" rx="14" fill="#fff9f2" stroke="#db8129" stroke-width="3" />
    <!-- Number circle 5 (Orange highlight row) -->
    <circle cx="80" cy="{step5_y + 30}" r="24" fill="#db8129" />
    <text x="80" y="{step5_y + 39}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>
    <!-- Icon 5: Alert bell / page firing (40x40) -->
    <g transform="translate(120, {step5_y + 10})" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 20 4 C 13 4 9 9 9 15 C 9 22 5 26 5 26 L 35 26 C 35 26 31 22 31 15 C 31 9 27 4 20 4 Z" />
      <path d="M 16 31 C 16 33.2 17.8 35 20 35 C 22.2 35 24 33.2 24 31" />
      <line x1="20" y1="2" x2="20" y2="4" />
    </g>
    <!-- Step 5 Title -->
    <text x="175" y="{step5_y + 35}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Page fires in about 52 seconds</text>
    <!-- Step 5 Detail -->
    <text x="60" y="{step5_y + 74}" font-family="sans-serif" font-size="24" fill="#303a36">Both windows are above the threshold, so the on-call engineer is paged.</text>
  </g>

  <!-- Arrow 5 -> 6 -->
  <line x1="80" y1="{step5_y + step_h}" x2="80" y2="{step1_y + 5 * step_pitch}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />

  <!-- ==================== STEP 6 ==================== -->
  <g id="step-6">
    <rect x="{step_x}" y="{step1_y + 5 * step_pitch}" width="{step_w}" height="{step_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 6 -->
    <circle cx="80" cy="{step1_y + 5 * step_pitch + 30}" r="24" fill="#207448" />
    <text x="80" y="{step1_y + 5 * step_pitch + 39}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">6</text>
    <!-- Icon 6: Undo / Rollback arrow (40x40) -->
    <g transform="translate(120, {step1_y + 5 * step_pitch + 10})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 13 14 L 6 21 L 13 28" />
      <path d="M 6 21 H 24 C 30 21 34 17 34 11 C 34 6 30 4 24 4" />
    </g>
    <!-- Step 6 Title -->
    <text x="175" y="{step1_y + 5 * step_pitch + 35}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">On-call engineer rolls back</text>
    <!-- Step 6 Detail -->
    <text x="60" y="{step1_y + 5 * step_pitch + 74}" font-family="sans-serif" font-size="24" fill="#303a36">The error ratio drops once the bad release is removed.</text>
  </g>

  <!-- Arrow 6 -> 7 -->
  <line x1="80" y1="{step1_y + 5 * step_pitch + step_h}" x2="80" y2="{step1_y + 6 * step_pitch}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />

  <!-- ==================== STEP 7 ==================== -->
  <g id="step-7">
    <rect x="{step_x}" y="{step1_y + 6 * step_pitch}" width="{step_w}" height="{step_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Number circle 7 -->
    <circle cx="80" cy="{step1_y + 6 * step_pitch + 30}" r="24" fill="#207448" />
    <text x="80" y="{step1_y + 6 * step_pitch + 39}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">7</text>
    <!-- Icon 7: Recovery / Checkmark (40x40) -->
    <g transform="translate(120, {step1_y + 6 * step_pitch + 10})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="20" cy="20" r="16" />
      <polyline points="11,20 16,25 29,12" />
    </g>
    <!-- Step 7 Title -->
    <text x="175" y="{step1_y + 6 * step_pitch + 35}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Short window clears first</text>
    <!-- Step 7 Detail -->
    <text x="60" y="{step1_y + 6 * step_pitch + 74}" font-family="sans-serif" font-size="24" fill="#303a36">The alert clears within minutes of the rollback, before the long window.</text>
  </g>

  <!-- ==================== CONNECTION TO BUDGET BOX ==================== -->
  <!-- Thin dashed line from step 5 to budget box -->
  <line x1="{gap_x}" y1="{step5_mid_y}" x2="{budget_x}" y2="{step5_mid_y}" stroke="#207448" stroke-width="2.5" stroke-dasharray="6,4" />

  <!-- Small timer icon labelled 'clock' near step 5 -->
  <g id="timer-clock">
    <!-- Clock outline icon (36x36) -->
    <g transform="translate(1167, {step5_mid_y - 72})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="18" cy="18" r="15" fill="#e8f1ea" />
      <polyline points="18,8 18,18 24,18" />
      <line x1="18" y1="1" x2="18" y2="3" />
    </g>
    <!-- Label 'clock' -->
    <text x="1185" y="{step5_mid_y - 12}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">clock</text>
  </g>

  <!-- ==================== BUDGET SPENT BOX ==================== -->
  <g id="budget-box">
    <rect x="{budget_x}" y="{budget_y}" width="{budget_w}" height="{budget_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Box Title -->
    <text x="{budget_x + budget_w // 2}" y="{budget_y + 44}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Budget spent</text>
    <!-- Monospace Numbers -->
    <rect x="{budget_x + 10}" y="{budget_y + 68}" width="{budget_w - 20}" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="{budget_x + budget_w // 2}" y="{budget_y + 103}" text-anchor="middle" font-family="monospace" font-size="25" font-weight="bold" fill="#207448">12 / 43.2 = 27.8%</text>
    <!-- Sans Line (wrapped with tspan) -->
    <text x="{budget_x + budget_w // 2}" y="{budget_y + 162}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="{budget_x + budget_w // 2}" dy="0">of a 30 day </tspan>
      <tspan x="{budget_x + budget_w // 2}" dy="32">99.9 percent budget</tspan>
    </text>
  </g>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="{takeaway_x}" y="{takeaway_y}" width="{takeaway_w}" height="{takeaway_h}" rx="12" fill="#207448" />
    <text x="800" y="{takeaway_y + 36}" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">Tie the freeze decision to the written error budget policy and do not improvise it.</text>
  </g>
</svg>'''
    return svg

if __name__ == '__main__':
    svg_data = build_svg()
    with open('test_rollout_candidate.svg', 'w') as f:
        f.write(svg_data)
    print("Wrote test_rollout_candidate.svg successfully.")
