from sim_layout import check_wrap

# Let's test the text wrapping for the rule boxes:
docker_text = "Docker's own NAT and FORWARD rules (DOCKER chain) are inserted ahead of the rules managed by ufw or firewalld"
fw_text = "ufw or firewalld rule that should block the port"

# If docker box width = 460 (inner = 460 - 40 = 420):
d_lines = check_wrap(docker_text, 420, size=24)
print("Docker box (w=420):", len(d_lines), "lines")
for l in d_lines:
    print(" ", len(l), l)

# If fw box width = 380 (inner = 380 - 40 = 340):
f_lines = check_wrap(fw_text, 340, size=24)
print("\nFW box (w=340):", len(f_lines), "lines")
for l in f_lines:
    print(" ", len(l), l)
