from sim_layout import check_wrap

# Inside netfilter chains: x=40..980 (w=940), y=290..540 (h=250)
# Header: netfilter chains (y=290..330)
# Working area: y=330..530 (h=200)

# Column 1: x=60..580 (w=520)
#   Docker rules: y=340..425 (h=85)
#   FW rule (skipped): y=445..520 (h=75) (Gap = 20)
# Column 2: x=680..960 (w=280)
#   Container port 80: y=380..470 (h=90)
# Arrow: from Docker rules right edge (x=580, y=382) to Container port 80 left edge (x=680, y=425)
# Arrow length = 100px!
# Arrow color = #db8129 (orange)!
# Label beside/above arrow: 'published port 8080 answers from anywhere' (wrapped on 2 lines or above arrow)

d_text = "Docker's own NAT and FORWARD rules (DOCKER chain) are inserted ahead of the rules managed by ufw or firewalld"
f_text = "ufw or firewalld rule that should block the port"
cp_text = "container port 80"

print("Docker rules (w=520 - 32 = 488):")
for l in check_wrap(d_text, 488, size=24):
    print(" ", len(l), l)

print("\nFW rule (w=520 - 32 = 488):")
for l in check_wrap(f_text, 488, size=24):
    print(" ", len(l), l)

print("\nContainer port 80 (w=280 - 32 = 248):")
for l in check_wrap(cp_text, 248, size=28):
    print(" ", len(l), l)
