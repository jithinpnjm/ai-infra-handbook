import re

# Proposed layout for H = 1050
# Column headers: y = 105 to 175
# Left Column (x: 50..770, w=720):
#   L1: Note "Works on a fresh cluster" -> y: 195..250 (h=55)
#   gap = 45
#   L2: "Service" box -> y: 295..410 (h=115)
#   gap = 45 (arrow: 410 -> 455)
#   L3: "kube-proxy programs each host" -> y: 455..570 (h=115)
#   gap = 45 (arrow: 570 -> 615)
#   L4: Pods group container -> y: 615..880 (h=265)
#       Inside: two Pod boxes:
#       Pod 1: x: 120..385 (w=265), y: 645..850 (h=205)
#       Pod 2: x: 435..700 (w=265), y: 645..850 (h=205)
#   column bottom = 915. Padding bottom = 915 - 880 = 35.
#
# Right Column (x: 830..1550, w=720):
#   R1: "Ingress object" box -> y: 195..330 (h=135)
#   gap = 45 (dashed orange arrow: 330 -> 375)
#   R2: "No controller: the Ingress does nothing" -> y: 375..470 (h=95)
#   gap = 50
#   R3: "ingress-nginx: writes NGINX config for Pods" -> y: 520..635 (h=115)
#   gap = 45
#   R4: "Contour: programs Envoy" -> y: 680..795 (h=115)
#   column bottom = 915.
#
# Gap between columns and takeaway bar:
# Takeaway bar: y: 955..1025 (h=70)
# Gap above takeaway = 955 - 915 = 40px!
# Outside margin below takeaway = 1050 - 1025 = 25px! 
# Wait! Margin below takeaway is 25px, which is < 40px!

# What if H = 1080?
# Takeaway bar: y: 965..1035 (h=70)
# Margin below takeaway: 1080 - 1035 = 45px! (>= 40px!)
# Gap above takeaway: 965 - 920 = 45px! (>= 40px!)
# Column bottom: y = 920.
# Column top: y = 95. Outside margin top: y = 95. Title at y = 55. Top margin: 95 (>= 40px!)
# Outside margin left: 50px (>= 40px!)
# Outside margin right: 1600 - 1550 = 50px (>= 40px!)
