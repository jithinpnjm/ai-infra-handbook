# Geometric verification script
import xml.etree.ElementTree as ET

def verify_geometry():
    # Margins check: canvas is 1600x1200, 40px margin means everything must be between X=40 and X=1560, Y=40 and Y=1160
    # Let us verify all elements in our layout:

    # 1. Title:
    # x=800 (center), y=55, dy=52 -> text at y=55 and y=107
    # Max text line: 49 chars * 0.6 * 48 = 1411px -> left = 800 - 705 = 95px, right = 1505px. Inside [40, 1560]! Margin = 95px > 40px.

    # 2. Timeline section:
    # x=60, y=135, width=1480, height=175. Right = 1540. Margin = 60px > 40px.
    # Job starts card: x=90, y=155, width=180, height=52.
    # Text 'Job starts': 10 chars * 0.6 * 28 = 168px. In 180px box, text centered at 180: left=96, right=264. Padding inside box = 6px -> let's widen card to 200px (x=80 to 280) so padding is (200-168)/2 = 16px!

    # 3. Orange Marker card:
    # card_w = 700, marker_x = 760 -> card_x = 410, card_right = 1110.
    # Text line 1: #SBATCH --signal=B:USR1@180: (28 chars mono * 0.62 * 24 = 416px). Left=760 - 208 = 552, Right = 968. Padding = (700-416)/2 = 142px >= 16px.
    # Text line 2: Slurm sends SIGUSR1 to the batch shell (42 chars * 0.6 * 24 = 604px). Left=760 - 302 = 458, Right = 1062. Padding = (700-604)/2 = 48px >= 16px!

    # 4. Time limit card:
    # x=1140, y=145, width=380, height=90.
    # Line 1: 'Time limit: SIGTERM,' (20 chars * 14.4 = 288px). Center 1330: left=1186, right=1474. Padding = (380-288)/2 = 46px >= 16px.
    # Line 2: 'then SIGKILL after' (18 chars * 14.4 = 259.2px). Padding = (380-259.2)/2 = 60px >= 16px.
    # Line 3: 'KillWait (default 30 s)' (23 chars * 14.4 = 331.2px). Center 1330: left=1164.4, right=1495.6. Padding = (380-331.2)/2 = 24.4px >= 16px!
    # Vertical: y=172, dy=28, dy=28 -> y=172, 200, 228. Card y=145 to 235 (height 90). Top padding = 172 - 24 - 145 = 3px!
    # WAIT! Notice font-size 24 baseline y=172 means top of text is at ~ 172 - 18 = 154. Card top is 145. Top padding = 9px < 16px!
    # And bottom of text at 228 + 6 = 234. Card bottom is 235. Bottom padding = 1px!
    # LET US MAKE THIS CARD TALLER! e.g. y=138, height=105!
    # Then top of text at 154, card top 138 -> 16px padding!
    # Bottom text baseline 222 + 6 = 228, card bottom 243 -> 15px padding!
    # Better: y=138, height=110! Then padding is >= 16px!

    print("Checking box 1, 2, 3...")

verify_geometry()
