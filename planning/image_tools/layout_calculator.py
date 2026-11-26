# Let's test the main layout area

# Main area: y=130 to y=765 (height 635)
# Right panel: Docker network modes
# Title: Docker network modes (30px)
# 6 items:
# bridge (4-5 lines)
# host (3-4 lines)
# none (1 line)
# container:NAME (2-3 lines)
# overlay (2 lines)
# macvlan or ipvlan (2 lines)

# Total lines: ~15 lines at 24px, line-height 28px = 420px + title 40px + padding 40px = 500px!
# 500px < 635px! It fits easily!

# Now left area: width 900 (x=40 to x=940)
# Height = 635 px (y=130 to y=765)

# Left area contains:
# 1. Packet path:
#    Client -> Host NIC -> netfilter chains
#    Order: Docker's own NAT and FORWARD rules (DOCKER chain) are inserted ahead of the rules managed by ufw or firewalld
#    leading to container port 80 (orange arrow: published port 8080 answers from anywhere)
#    Beside it: ufw or firewalld rule that should block the port (shown skipped)
# 2. Fixes box:
#    restrict a port with the DOCKER-USER chain
#    bind the port to a specific address (for example 127.0.0.1:8080:80)
#    if a published port must stay private on a shared host, restrict it in DOCKER-USER before you publish it

print("Left area height budget: 635px")
