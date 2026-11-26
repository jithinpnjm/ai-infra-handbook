from sim_layout import check_wrap

# netfilter container: x=40, width=900
# Inside padding: 20px
# We have 3 items:
# 1. Docker's rules
# 2. ufw or firewalld rule that should block the port (beside it, shown skipped)
# 3. container port 80

# What if inside netfilter chains (width 900):
# Order:
# Rule 1 (active): Docker rules
# Rule 2 (skipped): ufw/firewalld rule
# And destination: container port 80

# Can Rule 1 and Rule 2 be side-by-side or stacked?
# Prompt says: "Show the order 'Docker's own NAT and FORWARD rules (DOCKER chain) are inserted ahead of the rules managed by ufw or firewalld' leading to 'container port 80' (orange arrow: 'published port 8080 answers from anywhere'). Beside it the firewall rule box 'ufw or firewalld rule that should block the port' shown skipped."

# "Show the order 'Docker's own NAT and FORWARD rules... inserted ahead of the rules managed by ufw or firewalld'"
# "Beside it the firewall rule box 'ufw or firewalld rule that should block the port' shown skipped."

# If Docker rules is on the left / top, and firewall rule is beside it (or right/below), and then orange arrow leads to container port 80!
