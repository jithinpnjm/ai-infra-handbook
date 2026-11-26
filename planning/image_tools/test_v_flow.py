# Let's check vertical budget of the left side:
# y = 160 to y = 800 (height 640)

# 1. Top row: Client (left) -> Host NIC (right)
# y = 160..240 (h=80)
# Gap: 40px -> y = 280
# 2. Netfilter chains container:
# y = 280..490 (h=210)
#   Inside netfilter chains:
#   Header: netfilter chains (y=280..320)
#   Docker rules (left, w=430, h=150, y=325..475)
#   Firewall rule (right, w=430, h=150, y=325..475) [BESIDE IT, SKIPPED]
# Gap: 40px -> y = 530
# 3. Container port 80 box:
# y = 530..600 (h=70)
#   Orange arrow: from Docker rules (bottom, x=275, y=475) straight down to Container port 80 (top, x=275, y=530)!
#   Arrow length = 55px!
#   And what about the label 'published port 8080 answers from anywhere'?
#   Where does it go?
#   To the right of the orange arrow: x=300..620, y=550..580!
#   Beside the arrow, in clear space!
# Gap: 40px -> y = 640
# 4. Fixes box:
# y = 640..800 (h=160)
#   Inside Fixes box:
#   All 3 fixes!

print("Total left height =", 80 + 40 + 210 + 40 + 70 + 40 + 160, "== 640")
