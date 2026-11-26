from sim_layout import check_wrap

# Let's test this layout:
# Container: netfilter chains
# Suppose netfilter chains container is width 940 (x=40..980)
# Inside netfilter chains:
# Let's say:
# Left side (or middle):
# Docker rules box: width 480
# Firewall rules box: width 480
# If stacked vertically:
# Header: netfilter chains (height 40)
# Docker rules box: height 110
# Gap: 20
# Firewall rules box: height 80 (shown skipped)
# Total height = 40 + 110 + 20 + 80 = 250px!
# And to the right of Docker rules box:
# At x=580..960 (width 380):
# Container port 80 box!
# Orange arrow goes from Docker rules box (right edge) to Container port 80 (left edge)!
# Distance between them: 580 - (60 + 480) = 40px, or if Docker rules is width 440:
# x=60..500 (width 440).
# Container port 80: x=680..960 (width 280).
# Horizontal gap = 680 - 500 = 180px!
# On this 180px horizontal gap (or curved arrow):
# Orange arrow from Docker rules to Container port 80!
# And label 'published port 8080 answers from anywhere' placed above or beside the arrow!
# Meanwhile, below Docker rules:
# ufw or firewalld rule box at x=60..500 (beside / below)!

print("Testing text wrapping in Docker rules (w=440 - 40 = 400):")
d_text = "Docker's own NAT and FORWARD rules (DOCKER chain) are inserted ahead of the rules managed by ufw or firewalld"
for l in check_wrap(d_text, 400, size=24):
    print(" ", len(l), l)

print("\nTesting text wrapping in FW rules (w=440 - 40 = 400):")
f_text = "ufw or firewalld rule that should block the port"
for l in check_wrap(f_text, 400, size=24):
    print(" ", len(l), l)

print("\nTesting container port 80 in w=280:")
cp_text = "container port 80"
for l in check_wrap(cp_text, 240, size=28):
    print(" ", len(l), l)
