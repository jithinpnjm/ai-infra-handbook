import re

# Canvas: width=1600, height=1200
# Row 1 (y = 110 to 370): Metrics Scraping & Adapter
# Box 1: vLLM pod (x = 50, y = 110, w = 420, h = 180)
# Arrow 1: (x=470, y=200) -> (x=520, y=200) [h-arrow, len 50]
# Box 2: Prometheus (x = 520, y = 110, w = 340, h = 180)
# Arrow 2: (x=860, y=200) -> (x=910, y=200) [h-arrow, len 50]
# Box 3: prometheus-adapter rule (x = 910, y = 110, w = 640, h = 330)

# Row 2 (y = 480 to 760): K8s Custom Metrics API & HPA Decision
# Box 4: custom.metrics.k8s.io API (x = 50, y = 480, w = 680, h = 80)
# Cmd custom: (x = 50, y = 570, w = 680, h = 150)
# Box 5: HPA reads it and decides (x = 810, y = 480, w = 740, h = 80)
# Cmd HPA: (x = 810, y = 570, w = 740, h = 65)
# Conditions box: (x = 810, y = 645, w = 740, h = 175)

# Wait! Where does Arrow 3 go?
# Arrow 3 goes from Box 3 (prometheus-adapter rule) to Box 4 (custom.metrics.k8s.io API).
# If Box 3 is at x = 910 to 1550, y = 110 to 440,
# and Box 4 is at x = 50 to 730, y = 480 to 560:
# How does Arrow 3 route?
# From bottom of Box 3 (x = 1230, y = 440) -> down to y = 460 -> left to x = 390 -> down to top of Box 4 (x = 390, y = 480)!
# Wait! Does a backwards (right-to-left) arrow look good, or does it violate left-to-right flow?
