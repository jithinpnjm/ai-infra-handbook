from sim_layout import check_wrap

d_text = "Docker's own NAT and FORWARD rules (DOCKER chain) are inserted ahead of the rules managed by ufw or firewalld"
for l in check_wrap(d_text, 380, size=24):
    w = len(l) * 24 * 0.6
    print(f"[{len(l):2d} ch, {w:5.1f}px / 380px] {l}")
