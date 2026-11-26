import re

# Canvas height = 1200
# Title at y = 55 (fs = 48 bold)

# Let's calculate the heights and y positions for all elements in Column 3:
# Available y: from 105 to 1100 (height 995 px).

# 1. custom.metrics.k8s.io API
#    h = 80 (icon + text: 2 lines)
#    y = 105 to 185
# 2. cmd_custom (kubectl get --raw ...)
#    h = 150 (4 lines mono fs=24)
#    y = 195 to 345
# Gap = 25
# 3. HPA reads it and decides
#    h = 80 (icon + text: 2 lines)
#    y = 370 to 450
# 4. cmd_hpa (kubectl describe hpa ...)
#    h = 85 (2 lines mono fs=24)
#    y = 460 to 545
# 5. Conditions box (AbleToScale, ScalingActive, ScalingLimited)
#    h = 240 (header + 3 conditions)
#    y = 555 to 795
# Gap = 25
# 6. external.metrics.k8s.io
#    h = 80 (icon + text: 2 lines)
#    y = 820 to 900
# 7. cmd_ext (kubectl get --raw ...)
#    h = 150 (4 lines mono fs=24)
#    y = 910 to 1060
# Gap = 25
# 8. Note box (across bottom)
#    h = 75
#    y = 1085 to 1160

total_end = 1160
print(f"Total end Y: {total_end} px (Canvas H = 1200)")
assert total_end <= 1180, "Overflows canvas!"
print("Fits within canvas with 40px margin at bottom!")
